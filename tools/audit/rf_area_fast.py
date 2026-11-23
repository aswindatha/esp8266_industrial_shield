import pcbnew, os
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
b=pcbnew.LoadBoard(os.path.join(ROOT,"ind_8ch_motor_ctrl.kicad_pcb"))
mm=pcbnew.ToMM
X0,X1,Y0,Y1=55.0,73.0,0.0,15.44
step=0.3
for z in b.Zones():
    layer=z.GetLayer()
    if z.GetIsRuleArea(): continue
    fp=z.GetFilledPolysList(layer)
    n=cov=0
    x=X0+step/2
    while x<X1:
        y=Y0+step/2
        while y<Y1:
            n+=1
            if fp.Contains(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))): cov+=1
            y+=step
        x+=step
    print(f"{z.GetZoneName():26} {b.GetLayerName(layer):6} covered area ~{cov*step*step:7.2f} mm^2 ({cov}/{n} samples)")
for name,layer in [("F.Cu",pcbnew.F_Cu),("B.Cu",pcbnew.B_Cu)]:
    L=0.0
    for t in b.GetTracks():
        if isinstance(t,pcbnew.PCB_VIA) or t.GetLayer()!=layer: continue
        s,e=t.GetStart(),t.GetEnd(); x0,y0,x1,y1=mm(s.x),mm(s.y),mm(e.x),mm(e.y)
        m=max(2,int(max(abs(x1-x0),abs(y1-y0))/0.05)); inside=0
        for i in range(m):
            x=x0+(x1-x0)*i/m; y=y0+(y1-y0)*i/m
            if X0<=x<=X1 and Y0<=y<=Y1: inside+=1
        if inside: L+=mm(t.GetLength())*inside/m
    print(f"{name} track length in keepout ~{L:.2f} mm")
