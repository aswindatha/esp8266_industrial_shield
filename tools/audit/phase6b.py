import csv, os, re, collections
import pcbnew
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FAB=os.path.join(ROOT,"fab")
b=pcbnew.LoadBoard(os.path.join(ROOT,"ind_8ch_motor_ctrl.kicad_pcb"))
pcb={f.GetReference():(pcbnew.ToMM(f.GetPosition().x),pcbnew.ToMM(f.GetPosition().y),f.GetOrientationDegrees()) for f in b.GetFootprints()}

print("=== POSITION FILE CROSS-CHECK (correct columns) ===")
pos=list(csv.DictReader(open(os.path.join(FAB,"pos.csv"),encoding="utf-8")))
bad=[]
for r in pos:
    ref=r["Ref"]; px,py,rot=float(r["PosX"]),float(r["PosY"]),float(r["Rot"])
    ex,ey,erot=pcb[ref]
    if abs(px-ex)>0.01 or abs(py-(-ey))>0.01 or abs(rot-erot)>0.01:
        bad.append((ref,px,py,rot,ex,ey,erot))
print("  rows:",len(pos),"mismatches (X, mirrored Y, rot):",len(bad))
for x in bad[:10]: print("   ",x)
print("  sides:",collections.Counter(r["Side"] for r in pos))

print("\n=== DRILL DETAIL ===")
dr=open(os.path.join(FAB,"ind_8ch_motor_ctrl.drl"),encoding="utf-8").read()
# find tool definitions and plating comments
for line in dr.splitlines():
    if line.startswith("T") and "C" in line and len(line)<40: print("  tool def:",line)
    if "PLATING" in line.upper() or "NPTH" in line or "PTH" in line: print("  plating note:",line[:120])
# count coordinates per tool by scanning
cur=None; cnt=collections.Counter(); xs=[]; ys=[]
for line in dr.splitlines():
    m=re.match(r"^T(\d+)\s*$",line.strip())
    if m: cur=m.group(1); continue
    if re.match(r"^X",line) and cur: cnt[cur]+=1
print("  hit counts by tool:",dict(cnt))
print("\n=== DRILL REPORT ===")
print(open(os.path.join(FAB,"drill_report.txt"),encoding="utf-8").read()[:1400])

print("\n=== GERBER MIN FEATURE (F.Cu draw apertures) ===")
g=open(os.path.join(FAB,"ind_8ch_motor_ctrl-F_Cu.gtl"),encoding="utf-8").read()
aps=set(re.findall(r"%ADD(\d+)([A-Z]+),([\d.]+)",g))
print("  apertures:",sorted(aps,key=lambda x:float(x[2]))[:12])
print("  min aperture mm:",min((float(a[2]) for a in aps),default=None))
