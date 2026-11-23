"""Phase 6: fabrication package cross-verification."""
import os, re, json, csv, math, collections
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FAB=os.path.join(ROOT,"fab")

print("=== 1. GERBER JOB ===")
job=json.load(open(os.path.join(FAB,"ind_8ch_motor_ctrl-job.gbrjob"),encoding="utf-8-sig"))
print("  top level keys:",list(job.keys()))
print("  General:",{k:job.get("General",{}).get(k) for k in ["BoardName","ProjectId","FileFunction","Size"]})
print("  Files count:",len(job.get("FilesAttributes",[])))
for f in job.get("FilesAttributes",[]):
    print("   ",f.get("Path"),f.get("FileFunction"),f.get("FilePolarity"))

print("\n=== 2. GERBER LAYER EXTENTS (Edge.Cuts) ===")
g=open(os.path.join(FAB,"ind_8ch_motor_ctrl-Edge_Cuts.gm1"),encoding="utf-8").read()
coords=[(float(a),float(b)) for a,b in re.findall(r"X(-?\d+)Y(-?\d+)",g)]
if coords:
    xs=[c[0] for c in coords]; ys=[c[1] for c in coords]
    print(f"  raw X range {min(xs)}..{max(xs)} = {(max(xs)-min(xs))/1e6:.3f} mm" if False else "")
    # Gerber units/mm conversion from header
    print("  header snippet:",g[:300].replace("\n"," ")[:280])

print("\n=== 3. DRILL FILE ===")
dr=open(os.path.join(FAB,"ind_8ch_motor_ctrl.drl"),encoding="utf-8").read()
print("  header:",dr[:260].replace("\n"," ")[:250])
tools=re.findall(r"T(\d+)C([\d.]+)",dr)
print("  tools (T=tool, D=diameter mm):",tools)
holes=re.findall(r"T(\d+)\n((?:X[^\n]+\nY[^\n]+\n?)+)",dr)
print("  tool hit groups:",[(t,len(re.findall(r'X',blk))) for t,blk in holes])
print("  NPTH markers:",dr.count("NPTH"), "; PTH markers:",dr.count("PTH"))

print("\n=== 4. POSITION FILE vs PCB ===")
pos=list(csv.DictReader(open(os.path.join(FAB,"pos.csv"),encoding="utf-8")))
print("  pos rows:",len(pos),"header:",list(pos[0].keys()) if pos else [])
# load PCB via pcbnew
import pcbnew
b=pcbnew.LoadBoard(os.path.join(ROOT,"ind_8ch_motor_ctrl.kicad_pcb"))
pcb={f.GetReference():(pcbnew.ToMM(f.GetPosition().x),pcbnew.ToMM(f.GetPosition().y),f.GetOrientationDegrees(),b.GetLayerName(f.GetLayer())) for f in b.GetFootprints()}
mismatch=[]
for r in pos:
    ref=r.get("Ref") or r.get("ref") or list(r.values())[0]
    if ref not in pcb: continue
    try:
        px,py=float(r.get("X",r.get("x",0))),float(r.get("Y",r.get("y",0)))
        rot=float(r.get("Rot",r.get("rotation",r.get("Rotation",0))))
    except ValueError: continue
    ex,ey,erot,elayer=pcb[ref]
    if abs(px-ex)>0.06 or abs(py-ey)>0.06:
        mismatch.append((ref,round(px,2),round(py,2),round(ex,2),round(ey,2)))
print("  position mismatches >0.06mm:",len(mismatch),mismatch[:12])
for ref in ["U_MCU1","U5","U6","D1","R11","R19","J_IN","J_OUT"]:
    row=next((r for r in pos if (r.get("Ref") or list(r.values())[0])==ref),None)
    print(f"   {ref:8} pos row={ {k:row[k] for k in list(row)[:6]} if row else None } pcb={pcb[ref]}")

print("\n=== 5. BOM vs PCB ===")
bom=list(csv.DictReader(open(os.path.join(FAB,"BOM.csv"),encoding="utf-8")))
bomrefs=set(r["Reference"] for r in bom)
pcbrefs=set(k for k in pcb if not k.startswith("MH"))
print("  BOM rows:",len(bom),"PCB non-MH footprints:",len(pcbrefs))
print("  missing from BOM:",sorted(pcbrefs-bomrefs)[:20])
print("  extra in BOM:",sorted(bomrefs-pcbrefs)[:20])
for f in ["ind_8ch_motor_ctrl.kicad_pcb","fab/BOM.csv","fab/pos.csv","fab/netlist.ipc356"]:
    print("  ",f,"sha256",__import__("hashlib").sha256(open(os.path.join(ROOT,f),'rb').read()).hexdigest()[:16])

print("\n=== 6. IPC-D-356 ===")
ipc=open(os.path.join(FAB,"netlist.ipc356"),encoding="utf-8").read()
print("  lines:",len(ipc.splitlines()),"net records:",ipc.count("N00"),"component records:",len(re.findall(r"^C\s",ipc,re.M)))
