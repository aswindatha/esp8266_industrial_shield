"""Phase 5: physical geometry, copper pour, DFM/DFA audit."""
import pcbnew, os, math, collections
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
b=pcbnew.LoadBoard(os.path.join(ROOT,"ind_8ch_motor_ctrl.kicad_pcb"))
mm=pcbnew.ToMM

print("=== 1. BOARD EDGE ===")
edges=[d for d in b.GetDrawings() if d.GetLayer()==pcbnew.Edge_Cuts]
print("  Edge.Cuts items:",len(edges))
for d in edges:
    s,e=d.GetStart(),d.GetEnd()
    print(f"    ({mm(s.x):.2f},{mm(s.y):.2f}) -> ({mm(e.x):.2f},{mm(e.y):.2f})")
bb=b.GetBoardEdgesBoundingBox()
print(f"  Bounding box {mm(bb.GetWidth()):.2f} x {mm(bb.GetHeight()):.2f} mm (includes {mm(edges[0].GetWidth()):.2f} line width)")

print("\n=== 2. TERMINAL BLOCK / MOUNTING HOLE MECHANICS ===")
for ref in ["J_IN","J_OUT","MH1","MH2","MH3","MH4"]:
    f=b.FindFootprintByReference(ref)
    c=f.GetCourtyard(pcbnew.F_CrtYd).BBox() if f.GetCourtyard(pcbnew.F_CrtYd) else None
    cb=f.GetBoundingBox(False,False)
    p=f.GetPosition()
    print(f"  {ref:6} pos=({mm(p.x):6.2f},{mm(p.y):6.2f}) bbox x[{mm(cb.GetLeft()):6.2f},{mm(cb.GetRight()):6.2f}] y[{mm(cb.GetTop()):6.2f},{mm(cb.GetBottom()):6.2f}]")
    if c:
        print(f"         courtyard x[{mm(c.GetLeft()):6.2f},{mm(c.GetRight()):6.2f}] y[{mm(c.GetTop()):6.2f},{mm(c.GetBottom()):6.2f}]")

def min_dist_to_copper(x,y):
    best=(1e9,None)
    for t in b.GetTracks():
        if isinstance(t,pcbnew.PCB_VIA):
            q=t.GetPosition(); d=math.hypot(mm(q.x)-x,mm(q.y)-y)-mm(t.GetWidth(pcbnew.F_Cu))/2
            if d<best[0]: best=(d,"via "+t.GetNetname())
        else:
            s,e=t.GetStart(),t.GetEnd(); x0,y0,x1,y1=mm(s.x),mm(s.y),mm(e.x),mm(e.y)
            L=math.hypot(x1-x0,y1-y0)
            if L==0: continue
            tpar=max(0,min(1,((x-x0)*(x1-x0)+(y-y0)*(y1-y0))/(L*L)))
            d=math.hypot(x-(x0+tpar*(x1-x0)),y-(y0+tpar*(y1-y0)))-mm(t.GetWidth())/2
            if d<best[0]: best=(d,"track "+t.GetNetname())
    return best
for ref in ["MH1","MH2","MH3","MH4"]:
    f=b.FindFootprintByReference(ref); p=f.GetPosition(); x,y=mm(p.x),mm(p.y)
    d,src=min_dist_to_copper(x,y)
    print(f"  {ref} copper clearance: {d:.2f} mm to {src} (hole radius 1.6 mm)")

print("\n=== 3. ZONE FILLS ===")
for z in b.Zones():
    fp=z.GetFilledPolysList(z.GetLayer())
    n=fp.OutlineCount()
    areas=[]
    for i in range(n):
        ol=fp.COutline(i)
        pts=[(mm(ol.CPoint(j).x),mm(ol.CPoint(j).y)) for j in range(ol.PointCount())]
        if len(pts)>=3:
            A=abs(sum(pts[k][0]*pts[(k+1)%len(pts)][1]-pts[(k+1)%len(pts)][0]*pts[k][1] for k in range(len(pts))))/2
            areas.append(A)
    print(f"  {z.GetZoneName():26} {b.GetLayerName(z.GetLayer()):6} net={z.GetNetname():12} filled={z.IsFilled()} polygons={n} areas={[round(a,1) for a in areas]}")
    print(f"     clearance={mm(z.GetLocalClearance()):.2f} thermal_gap={mm(z.GetThermalReliefGap()):.2f} spoke={mm(z.GetThermalReliefSpokeWidth()):.2f} min_thick={mm(z.GetMinThickness()):.2f}")

print("\n=== 4. REFERENCE FIELD LAYERS ===")
cnt=collections.Counter()
for f in b.GetFootprints():
    cnt[(f.Reference().GetLayer()==pcbnew.F_SilkS)]+=1
print("  references on F.SilkS:",cnt[True]," on other layers:",cnt[False])
for f in b.GetFootprints():
    if f.Reference().GetLayer()!=pcbnew.F_SilkS:
        print("   ",f.GetReference(),"ref layer",b.GetLayerName(f.Reference().GetLayer()))

print("\n=== 5. 0R JUMPERS ===")
for r in ["R_J1","R_J2","R_J3","R_J4","R_J5"]:
    f=b.FindFootprintByReference(r)
    nets=[p.GetNetname() for p in f.Pads()]
    p=f.GetPosition()
    print(f"  {r} @({mm(p.x):.1f},{mm(p.y):.1f}) nets={nets} same={nets[0]==nets[1]}")
