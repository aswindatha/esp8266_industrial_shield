"""Place 0R jumpers in verified FREE locations (clear of all copper), one per
unrouted connection, then let the autorouter stitch each side."""
import pcbnew, os, json, math, re
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,"ind_8ch_motor_ctrl.kicad_pcb")
MM=pcbnew.ToMM; V=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
LIB=r"C:\Users\aswin\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints\Resistor_SMD.pretty"
FP="R_1206_3216Metric_Pad1.30x1.75mm_HandSolder"
b=pcbnew.LoadBoard(PCB)

# copper sample points (all tracks, vias, pad centres) with occupancy radius
occ=[]
for t in b.GetTracks():
    if isinstance(t,pcbnew.PCB_VIA):
        p=t.GetPosition(); occ.append((MM(p.x),MM(p.y),MM(t.GetWidth(pcbnew.F_Cu))/2))
    else:
        s,e=t.GetStart(),t.GetEnd(); x0,y0,x1,y1=MM(s.x),MM(s.y),MM(e.x),MM(e.y)
        n=max(2,int(math.hypot(x1-x0,y1-y0)/0.5))
        for i in range(n+1):
            occ.append((x0+(x1-x0)*i/n,y0+(y1-y0)*i/n,MM(t.GetWidth())/2))
for f in b.GetFootprints():
    if f.GetReference().startswith("JMP"): continue
    for p in f.Pads():
        q=p.GetPosition(); occ.append((MM(q.x),MM(q.y),MM(max(p.GetSize().x,p.GetSize().y))/2))

def free(x,y,r=1.6):
    for ox,oy,orad in occ:
        if math.hypot(x-ox,y-oy) < r+orad: return False
    return True

unc=json.load(open(os.path.join(ROOT,"tools","audit","unc4.json"),encoding="utf-8"))
added=0
for i,u in enumerate(unc):
    its=u.get("items",[])
    if len(its)<2: continue
    p1=its[0].get("pos",{}); p2=its[1].get("pos",{})
    x1,y1=p1.get("x",0),p1.get("y",0); x2,y2=p2.get("x",0),p2.get("y",0)
    desc=its[0].get("description","")+" "+its[1].get("description","")
    m=re.search(r"\[(/[^\]]+)\]",desc)
    if not m: continue
    net=b.FindNet(m.group(1))
    if not net: continue
    # search a grid around the bounding box of the endpoints for a free spot
    best=None
    for x in [round(3+j*1.5,2) for j in range(63)]:
        for y in [round(3+k*1.5,2) for k in range(63)]:
            if not free(x,y): continue
            d=math.hypot(x-(x1+x2)/2,y-(y1+y2)/2)
            if best is None or d<best[0]: best=(d,x,y)
    if not best: continue
    _,mx,my=best
    ang=math.degrees(math.atan2(y2-y1,x2-x1))
    fp=pcbnew.FootprintLoad(LIB,FP)
    fp.SetReference("JMP%02d"%(i+1)); fp.SetValue("0R")
    fp.SetPosition(V(mx,my)); fp.SetOrientationDegrees(ang)
    b.Add(fp)
    for p in fp.Pads(): p.SetNet(net)
    added+=1
    print("JMP%02d net=%s at (%.1f,%.1f) d=%.1f"%(i+1,m.group(1),mx,my,best[0]))
print("added",added)
pcbnew.SaveBoard(PCB,b)
