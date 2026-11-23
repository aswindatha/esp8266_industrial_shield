"""Robust 0R jumper insertion: large clearance, no reused spots, footprint-aware."""
import pcbnew, os, json, math, re
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,"ind_8ch_motor_ctrl.kicad_pcb")
MM=pcbnew.ToMM; V=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
LIB=r"C:\Users\aswin\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints\Resistor_SMD.pretty"
FP="R_1206_3216Metric_Pad1.30x1.75mm_HandSolder"
b=pcbnew.LoadBoard(PCB)

# occupancy: track sample points + pad rectangles + footprint boxes
occ=[]
for t in b.GetTracks():
    if isinstance(t,pcbnew.PCB_VIA):
        p=t.GetPosition(); occ.append((MM(p.x),MM(p.y),MM(t.GetWidth(pcbnew.F_Cu))/2))
    else:
        s,e=t.GetStart(),t.GetEnd(); x0,y0,x1,y1=MM(s.x),MM(s.y),MM(e.x),MM(e.y)
        n=max(2,int(math.hypot(x1-x0,y1-y0)/0.4))
        for i in range(n+1): occ.append((x0+(x1-x0)*i/n,y0+(y1-y0)*i/n,MM(t.GetWidth())/2))
for f in b.GetFootprints():
    if f.GetReference().startswith("JMP"): continue
    cb=f.GetBoundingBox(False,False)
    occ.append(((MM(cb.GetLeft())+MM(cb.GetRight()))/2,(MM(cb.GetTop())+MM(cb.GetBottom()))/2,
                max(MM(cb.GetWidth()),MM(cb.GetHeight()))/2))
placed=[]
def free(x,y,r=2.6):
    for ox,oy,orad in occ:
        if math.hypot(x-ox,y-oy) < r+orad: return False
    for px,py in placed:
        if math.hypot(x-px,y-py) < 4.0: return False
    return True

unc=json.load(open(os.path.join(ROOT,"tools","audit","unc4.json"),encoding="utf-8"))
added=0
for i,u in enumerate(unc):
    its=u.get("items",[])
    if len(its)<2: continue
    p1=its[0].get("pos",{}); p2=its[1].get("pos",{})
    x1,y1=p1.get("x",0),p1.get("y",0); x2,y2=p2.get("x",0),p2.get("y",0)
    m=re.search(r"\[(/[^\]]+)\]",its[0].get("description","")+" "+its[1].get("description",""))
    if not m: continue
    net=b.FindNet(m.group(1))
    if not net: continue
    cx,cy=(x1+x2)/2,(y1+y2)/2
    best=None
    for x in [round(3+j,2) for j in range(95)]:
        for y in [round(3+k,2) for k in range(95)]:
            if not free(x,y): continue
            d=math.hypot(x-cx,y-cy)
            if best is None or d<best[0]: best=(d,x,y)
    if not best: 
        print("JMP%02d NO FREE SPOT net=%s"%(i+1,m.group(1))); continue
    _,mx,my=best
    placed.append((mx,my))
    ang=math.degrees(math.atan2(y2-y1,x2-x1))
    fp=pcbnew.FootprintLoad(LIB,FP)
    fp.SetReference("JMP%02d"%(i+1)); fp.SetValue("0R")
    fp.SetPosition(V(mx,my)); fp.SetOrientationDegrees(ang)
    b.Add(fp)
    for p in fp.Pads(): p.SetNet(net)
    added+=1
    print("JMP%02d %-14s (%.1f,%.1f)"%(i+1,m.group(1),mx,my))
print("added",added)
# clear existing routing so the router treats jumpers as components
for t in list(b.GetTracks()): b.RemoveNative(t)
pcbnew.SaveBoard(PCB,b)
print("routing cleared for fresh autoroute")
