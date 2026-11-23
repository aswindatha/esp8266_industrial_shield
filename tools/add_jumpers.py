"""Insert 0R jumpers at the midpoint of each unrouted connection so the
jumper body bridges the blocking trace (standard single-layer technique)."""
import pcbnew, os, json, math
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,"ind_8ch_motor_ctrl.kicad_pcb")
MM=pcbnew.FromMM; V=lambda x,y: pcbnew.VECTOR2I(MM(x),MM(y))
LIB=r"C:\Users\aswin\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints\Resistor_SMD.pretty"
FP="R_1206_3216Metric_Pad1.30x1.75mm_HandSolder"

# import routed result
b=pcbnew.LoadBoard(PCB)
ok=pcbnew.ImportSpecctraSES(b,os.path.join(ROOT,"tools","board_single4.ses"))
print("SES import",ok)
d=json.load(open(os.path.join(ROOT,"tools","audit","drc_single4.json"),encoding="utf-8")) if os.path.exists(os.path.join(ROOT,"tools","audit","drc_single4.json")) else None

# collect endpoints of unconnected items from current DRC (regenerate via file written by caller)
unc=json.load(open(os.path.join(ROOT,"tools","audit","unc4.json"),encoding="utf-8"))
added=0
for i,u in enumerate(unc):
    its=u.get("items",[])
    if len(its)<2: continue
    p1=its[0].get("pos",{}); p2=its[1].get("pos",{})
    x1,y1=p1.get("x",0),p1.get("y",0); x2,y2=p2.get("x",0),p2.get("y",0)
    # net name from description
    desc=its[0].get("description","")+" "+its[1].get("description","")
    import re
    m=re.search(r"\[(/[^\]]+)\]",desc)
    if not m: continue
    netname=m.group(1)
    net=b.FindNet(netname)
    if not net: continue
    mx,my=(x1+x2)/2,(y1+y2)/2
    ang=math.degrees(math.atan2(y2-y1,x2-x1))+90
    fp=pcbnew.FootprintLoad(LIB,FP)
    fp.SetReference("JMP%02d"%(i+1)); fp.SetValue("0R")
    fp.SetPosition(V(mx,my)); fp.SetOrientationDegrees(ang)
    b.Add(fp)
    for p in fp.Pads(): p.SetNet(net)
    added+=1
print("added jumpers:",added)
pcbnew.SaveBoard(PCB,b)
