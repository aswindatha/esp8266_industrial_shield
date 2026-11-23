import pcbnew, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
b = pcbnew.LoadBoard(os.path.join(ROOT, "ind_8ch_motor_ctrl.kicad_pcb"))
mm=pcbnew.ToMM

X0,X1,Y0,Y1 = 55.0,73.0,0.0,15.44
step=0.1
samples=[]
x=X0+step/2
while x<X1:
    y=Y0+step/2
    while y<Y1:
        samples.append((x,y)); y+=step
    x+=step
print("grid samples:",len(samples))

for z in b.Zones():
    layer=z.GetLayer()
    fp=z.GetFilledPolysList(layer)
    cnt=0; cov=[]
    for x,y in samples:
        if fp.Contains(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))):
            cnt+=1; cov.append((x,y))
    area=cnt*step*step
    if cov:
        print(f"{z.GetZoneName():26} {b.GetLayerName(layer):6} covered area={area:7.2f} mm^2  x[{min(p[0] for p in cov):.1f},{max(p[0] for p in cov):.1f}] y[{min(p[1] for p in cov):.1f},{max(p[1] for p in cov):.1f}]")
    else:
        print(f"{z.GetZoneName():26} {b.GetLayerName(layer):6} covered area=0.00 mm^2")

# track length inside keepout
for name, layer in [("F.Cu",pcbnew.F_Cu),("B.Cu",pcbnew.B_Cu)]:
    L=0.0; nets=set()
    for t in b.GetTracks():
        if isinstance(t,pcbnew.PCB_VIA) or t.GetLayer()!=layer: continue
        s,e=t.GetStart(),t.GetEnd()
        x0,y0,x1,y1=mm(s.x),mm(s.y),mm(e.x),mm(e.y)
        # clip against rect using sampling for length estimate
        n=max(2,int(max(abs(x1-x0),abs(y1-y0))/0.02))
        inside=0
        for i in range(n):
            x=x0+(x1-x0)*i/n; y=y0+(y1-y0)*i/n
            if X0<=x<=X1 and Y0<=y<=Y1: inside+=1
        if inside:
            L+=t.GetLength()*inside/n
            nets.add(t.GetNetname())
    print(f"{name} track length in keepout ~{mm(L):.2f} mm nets={sorted(nets)}")
