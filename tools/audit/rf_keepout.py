"""RF keepout audit: inspect ALL copper in the ESP32-WROOM-32E antenna volume."""
import pcbnew, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
b = pcbnew.LoadBoard(os.path.join(ROOT, "ind_8ch_motor_ctrl.kicad_pcb"))
mm = pcbnew.ToMM

# ESP32-WROOM-32E at (64,21). Module body top edge y=14.44; antenna tip y~8.25.
# Conservative keepout: the full antenna footprint x 55..73, y 0..15.44
ASK, ASK_X0, ASK_X1, ASK_Y0, ASK_Y1 = "Antenna x55-73 y0-15.44", 55.0, 73.0, 0.0, 15.44

def seg_intersects_rect(x0,y0,x1,y1,rx0,ry0,rx1,ry1):
    # sample segment densely; adequate at 0.05mm resolution
    n = max(2, int(max(abs(x1-x0),abs(y1-y0))/0.05)+1)
    for i in range(n+1):
        x = x0+(x1-x0)*i/n; y = y0+(y1-y0)*i/n
        if rx0<=x<=rx1 and ry0<=y<=ry1:
            return (round(x,2),round(y,2))
    return None

print("=== TRACKS / VIAS INSIDE ANTENNA KEEPOUT ===")
hits=[]
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        x,y=mm(t.GetPosition().x),mm(t.GetPosition().y)
        if ASK_X0<=x<=ASK_X1 and ASK_Y0<=y<=ASK_Y1:
            hits.append(("VIA",t.GetNetname(),b.GetLayerName(t.GetTopLayer()),round(x,2),round(y,2)))
    else:
        s,e=t.GetStart(),t.GetEnd()
        p=seg_intersects_rect(mm(s.x),mm(s.y),mm(e.x),mm(e.y),ASK_X0,ASK_Y0,ASK_X1,ASK_Y1)
        if p:
            hits.append((b.GetLayerName(t.GetLayer()),t.GetNetname(),round(mm(t.GetWidth()),3),p))
for h in hits: print("  ",h)
print("  total:",len(hits))

print("\n=== ZONE FILL POLYGONS INSIDE ANTENNA KEEPOUT ===")
for z in b.Zones():
    layer = b.GetLayerName(z.GetLayer())
    try:
        fp = z.GetFilledPolysList(z.GetLayer())
        n = fp.OutlineCount()
    except Exception as e:
        print("  ",z.GetZoneName(),"fill query failed:",e); continue
    inside=0; samples=[]
    for i in range(n):
        ol = fp.COutline(i)
        for j in range(ol.PointCount()):
            q=ol.CPoint(j); x,y=mm(q.x),mm(q.y)
            if ASK_X0<=x<=ASK_X1 and ASK_Y0<=y<=ASK_Y1:
                inside+=1
                if len(samples)<6: samples.append((round(x,2),round(y,2)))
    print(f"  {z.GetZoneName():26} layer={layer:6} filled_outlines={n:3} vertices_in_keepout={inside:4} samples={samples}")

print("\n=== FOOTPRINTS (other than U_MCU1) INSIDE KEEPOUT ===")
for f in b.GetFootprints():
    if f.GetReference()=="U_MCU1": continue
    p=f.GetPosition(); x,y=mm(p.x),mm(p.y)
    if ASK_X0<=x<=ASK_X1 and ASK_Y0<=y<=ASK_Y1:
        print("  ",f.GetReference(),f.GetValue(),round(x,2),round(y,2))
