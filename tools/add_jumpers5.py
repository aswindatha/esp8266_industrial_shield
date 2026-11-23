"""Insert tiny 0402 0R jumpers along unrouted paths (fits tight crossing points)."""
import pcbnew, os, json, math, re
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,"ind_8ch_motor_ctrl.kicad_pcb")
MM=pcbnew.ToMM; V=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
LIB=r"C:\Users\aswin\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints\Resistor_SMD.pretty"
FP="R_0402_1005Metric"
b=pcbnew.LoadBoard(PCB)
obst=[]
for f in b.GetFootprints():
    if f.GetReference().startswith("JMP"): continue
    c=f.GetCourtyard(pcbnew.F_CrtYd); bb=c.BBox() if c else f.GetBoundingBox(False,False)
    obst.append((MM(bb.GetLeft())-0.15,MM(bb.GetTop())-0.15,MM(bb.GetRight())+0.15,MM(bb.GetBottom())+0.15))
for t in b.GetTracks():
    if isinstance(t,pcbnew.PCB_VIA):
        p=t.GetPosition(); r=MM(t.GetWidth(pcbnew.F_Cu))/2+0.15; x,y=MM(p.x),MM(p.y)
        obst.append((x-r,y-r,x+r,y+r))
    else:
        s,e=t.GetStart(),t.GetEnd(); x0,y0,x1,y1=MM(s.x),MM(s.y),MM(e.x),MM(e.y); r=MM(t.GetWidth())/2+0.15
        obst.append((min(x0,x1)-r,min(y0,y1)-r,max(x0,x1)+r,max(y0,y1)+r))
def rect_free(x,y,hw=1.5,hh=1.5):
    box=(x-hw,y-hh,x+hw,y+hh)
    return not any(box[0]<o[2] and box[2]>o[0] and box[1]<o[3] and box[3]>o[1] for o in obst)
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
    ang=math.degrees(math.atan2(y2-y1,x2-x1))
    okp=False
    for f in [0.5,0.45,0.55,0.4,0.6,0.35,0.65,0.3,0.7]:
        cx=x1+(x2-x1)*f; cy=y1+(y2-y1)*f
        if rect_free(cx,cy):
            fp=pcbnew.FootprintLoad(LIB,FP)
            fp.SetReference("JMP%02d"%(i+1)); fp.SetValue("0R")
            fp.SetPosition(V(cx,cy)); fp.SetOrientationDegrees(ang); b.Add(fp)
            for p in fp.Pads(): p.SetNet(net)
            cb=fp.GetBoundingBox(False,False)
            obst.append((MM(cb.GetLeft())-0.15,MM(cb.GetTop())-0.15,MM(cb.GetRight())+0.15,MM(cb.GetBottom())+0.15))
            added+=1; okp=True
            print("JMP%02d %-14s (%.1f,%.1f)"%(i+1,m.group(1),cx,cy)); break
    if not okp: print("JMP%02d FAILED %s"%(i+1,m.group(1)))
print("added",added)
for t in list(b.GetTracks()): b.RemoveNative(t)
pcbnew.SaveBoard(PCB,b)
