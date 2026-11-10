"""Fetch the latest MP family tree from the Family Network and save a public copy.

Phone numbers are removed before saving. Writes data/family.json only when the tree changed.
"""
import json, os, re, sys, urllib.request

SOURCE = os.environ.get("FAMILY_SOURCE", "https://mpfamily.anianilak47.chatgpt.site/api/family")
OUT = "data/family.json"
STRICT = os.environ.get("STRICT", "").lower() == "true"

PHONE = re.compile(r"ph\s*no|phone|mobile|\d{6,}", re.I)

def clean(n):
    note = "\n".join(l for l in str(n.get("tooltip") or n.get("note") or "").split("\n") if not PHONE.search(l)).strip()
    out = {"id": str(n.get("id") or n.get("name")), "name": str(n.get("name", "")).strip(),
           "relation": n.get("relation", ""), "tooltip": note, "entryType": n.get("entryType", "individual"),
           "children": [clean(c) for c in n.get("children") or []]}
    if n.get("birthYear"):
        out["birthYear"] = n["birthYear"]
    return out

def main():
    req = urllib.request.Request(SOURCE, headers={"User-Agent": "Mozilla/5.0 (MP Family site sync)", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        family = data.get("family", data)
        if not family.get("name") or not isinstance(family.get("children"), list):
            raise ValueError("response does not look like a family tree")
    except Exception as e:  # noqa: BLE001
        print(f"::warning::Could not load the family tree from {SOURCE}: {e}")
        sys.exit(1 if STRICT else 0)
    new = json.dumps(clean(family), ensure_ascii=False, indent=1) + "\n"
    old = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    if new != old:
        os.makedirs("data", exist_ok=True)
        open(OUT, "w", encoding="utf-8").write(new)
        print("Family tree updated.")
    else:
        print("No changes.")

main()
