import json, os, re, collections
D=os.path.dirname(os.path.abspath(__file__))
d=json.load(open(os.path.join(D,"drc_single_1.json"),encoding="utf-8"))
for i,u in enumerate(d["unconnected_items"]):
    its=u.get("items",[])
    print(f"\n[{i+1}]",u.get("description",""))
    for it in its:
        p=it.get("pos",{})
        print("   ",it.get("description","")[:75], "(%.2f,%.2f)"%(p.get("x",0),p.get("y",0)))
