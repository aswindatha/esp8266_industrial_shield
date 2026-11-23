"""Phase 7 minimal fix: add ESP32 antenna copper keepout, reroute UART_TX below it."""
import pcbnew, os
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PCB=os.path.join(ROOT,"ind_8ch_motor_ctrl.kicad_pcb")
MM=pcbnew.FromMM
V=lambda x,y: pcbnew.VECTOR2I(MM(x),MM(y))
b=pcbnew.LoadBoard(PCB)

# ---- 1. delete the two UART_TX segments crossing the antenna region -------
targets=[((48.97,3.34),(62.16,3.34)), ((62.16,3.34),(74.23,15.40))]
def same(a,b,tol=0.05): return abs(a[0]-b[0])<tol and abs(a[1]-b[1])<tol
deleted=0
for t in list(b.GetTracks()):
    if isinstance(t,pcbnew.PCB_VIA) or t.GetNetname()!="/UART_TX": continue
    s,e=t.GetStart(),t.GetEnd()
    p=(pcbnew.ToMM(s.x),pcbnew.ToMM(s.y)); q=(pcbnew.ToMM(e.x),pcbnew.ToMM(e.y))
    for a,c in targets:
        if (same(p,a) and same(q,c)) or (same(p,c) and same(q,a)):
            b.RemoveNative(t); deleted+=1; break
print("deleted offending UART_TX segments:",deleted)

net=b.FindNet("/UART_TX")
path=[(48.97,3.34),(50.0,3.34),(50.0,16.2),(74.23,16.2),(74.23,15.40)]
for (x0,y0),(x1,y1) in zip(path,path[1:]):
    t=pcbnew.PCB_TRACK(b)
    t.SetStart(V(x0,y0)); t.SetEnd(V(x1,y1))
    t.SetWidth(MM(0.35)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net)
    b.Add(t)
print("added",len(path)-1,"reroute segments")

# ---- 2. keepout rule area over antenna (F.Cu + B.Cu) ----------------------
z=pcbnew.ZONE(b)
z.SetIsRuleArea(True)
z.SetLayerSet(pcbnew.LSET.AllCuMask())
z.SetZoneName("ESP32_ANTENNA_KEEPOUT")
z.SetDoNotAllowZoneFills(True)
z.SetDoNotAllowTracks(True)
z.SetDoNotAllowVias(True)
z.SetDoNotAllowPads(True)
poly=z.Outline(); poly.NewOutline()
for x,y in [(55.0,0.0),(73.0,0.0),(73.0,15.5),(55.0,15.5)]:
    poly.Append(MM(x),MM(y))
b.Add(z)
print("added antenna keepout rule area")

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB,b)
print("saved")
