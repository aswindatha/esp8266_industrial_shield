import json, collections, os
D = os.path.dirname(os.path.abspath(__file__))

erc = json.load(open(os.path.join(D, "erc_audit.json"), encoding="utf-8"))
drc = json.load(open(os.path.join(D, "drc_audit.json"), encoding="utf-8"))
par = json.load(open(os.path.join(D, "drc_parity_audit.json"), encoding="utf-8"))

print("=== ERC ===")
print("keys:", list(erc.keys()))
for k in ("violations", "unconnected_items", "schematic_parity"):
    v = erc.get(k, [])
    print(f"  {k}: {len(v)}", dict(collections.Counter(x.get("type") for x in v)) if v else "")

print("\n=== PCB DRC ===")
print("unconnected:", len(drc.get("unconnected_items", [])))
c = collections.Counter(v["type"] for v in drc["violations"])
print("violations:", len(drc["violations"]), dict(c))
for v in drc["violations"]:
    print(f"  [{v['severity']}] {v['type']}: {v.get('description','')[:130]}")

print("\n=== SCHEMATIC PARITY ===")
p = par.get("schematic_parity", [])
print("count:", len(p), dict(collections.Counter(x.get("type") for x in p)))
for x in p:
    print(f"  [{x.get('severity')}] {x.get('type')}: {x.get('description','')}")
