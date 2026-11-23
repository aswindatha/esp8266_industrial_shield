"""Add production-hardening components to the 2-layer board with full routing.

Adds:
  F1       PTC fuse in series with 12V_RAW (track cut + new 12V_FUSED net)
  D_FL1..8 flyback diodes MOTx -> 12V_PROT
  C_DEC1..4 100nF decoupling caps (3V3/GND, 5V/GND)
Routes all new connections with 2-layer A* (vias allowed), then saves.
"""
import pcbnew, os, math, heapq
from collections import defaultdict

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,'ind_8ch_motor_ctrl.kicad_pcb')
MM=pcbnew.ToMM; FM=pcbnew.FromMM
STEP=0.25; GRID=int(100/STEP)+4
CLR=0.30; TW=0.30; VIA_W=0.60; VIA_D=0.30

def kv(x,y): return (int(round(x/STEP)),int(round(y/STEP)))
b=pcbnew.LoadBoard(PCB)

# ---------- occupancy (3-state: free / net / hole) ----------
# key: (gx,gy,layer) -> netcode ; layer 0=F.Cu, 1=B.Cu, -1=hole
occ={}
def mark_circle(cx,cy,r,code,layer):
    for gx in range(int((cx-r)/STEP),int((cx+r)/STEP)+1):
        for gy in range(int((cy-r)/STEP),int((cy+r)/STEP)+1):
            x,y=gx*STEP,gy*STEP
            if (x-cx)**2+(y-cy)**2<=r*r:
                k=(gx,gy,layer)
                if code==-2 or k not in occ: occ[k]=code

for f in b.GetFootprints():
    for p in f.Pads():
        q=p.GetPosition(); sz=p.GetSize()
        cx,cy=MM(q.x),MM(q.y)
        if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH:
            mark_circle(cx,cy,MM(sz.x)/2+0.3,-2,0); mark_circle(cx,cy,MM(sz.x)/2+0.3,-2,1); continue
        r=min(MM(sz.x),MM(sz.y))/2+CLR
        layers=[0,1] if p.GetAttribute()==pcbnew.PAD_ATTRIB_PTH else [0]
        for L in layers: mark_circle(cx,cy,r,p.GetNetCode(),L)

for t in b.GetTracks():
    nc=t.GetNetCode()
    if t.Type()==pcbnew.PCB_VIA_T:
        q=t.GetPosition(); mark_circle(MM(q.x),MM(q.y),VIA_W/2+CLR,nc,0); mark_circle(MM(q.x),MM(q.y),VIA_W/2+CLR,nc,1)
    else:
        L=0 if t.GetLayer()==pcbnew.F_Cu else 1
        s,e=t.GetStart(),t.GetEnd(); x0,y0,x1,y1=MM(s.x),MM(s.y),MM(e.x),MM(e.y)
        n=max(1,int(math.hypot(x1-x0,y1-y0)/(STEP*0.4)))
        for i in range(n+1):
            f2=i/n; mark_circle(x0+(x1-x0)*f2,y0+(y1-y0)*f2,MM(t.GetWidth())/2+CLR,nc,L)

def astar2(s,t,code):
    """A* on (x,y,layer); via transition cost 8. s,t=(x,y,layer)."""
    sk=(kv(s[0],s[1])[0],kv(s[0],s[1])[1],s[2])
    tk=(kv(t[0],t[1])[0],kv(t[0],t[1])[1],t[2])
    def ok(k):
        v=occ.get(k,0); return v==0 or v==code
    openh=[(0.0,sk)]; came={}; g={sk:0.0}
    while openh:
        _,cur=heapq.heappop(openh)
        if cur==tk:
            path=[cur]
            while cur in came: cur=came[cur]; path.append(cur)
            path.reverse(); return path
        x,y,L=cur
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nb=(x+dx,y+dy,L)
            if nb[0]<1 or nb[1]<1 or nb[0]>=GRID or nb[1]>=GRID: continue
            if not ok(nb) and nb!=tk: continue
            ng=g[cur]+1.0
            if ng<g.get(nb,1e9):
                g[nb]=ng; came[nb]=cur
                heapq.heappush(openh,(ng+abs(tk[0]-nb[0])+abs(tk[1]-nb[1]),nb))
        # via transition
        nb=(x,y,1-L)
        if ok(nb) and nb!=tk:
            ng=g[cur]+8.0
            if ng<g.get(nb,1e9):
                g[nb]=ng; came[nb]=cur
                heapq.heappush(openh,(ng+abs(tk[0]-nb[0])+abs(tk[1]-nb[1]),nb))
    return None

def emit(path,code):
    """Convert grid path to tracks+vias."""
    seg_start=None; cur_layer=path[0][2]
    for i in range(1,len(path)):
        p=path[i]; prev=path[i-1]
        if p[2]!=prev[2]:
            # via at prev position
            v=pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(FM(prev[0]*STEP),FM(prev[1]*STEP)))
            v.SetWidth(FM(VIA_W)); v.SetDrill(FM(VIA_D)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); v.SetNetCode(code); b.Add(v)
            cur_layer=p[2]
            seg_start=None
    # build tracks per layer run
    runs=[]; run=[]
    for k in path:
        if not run or k[2]==run[-1][2]: run.append(k)
        else: runs.append(run); run=[k]
    if run: runs.append(run)
    for run in runs:
        if len(run)<2: continue
        pts=[(k[0]*STEP,k[1]*STEP) for k in run]
        out=[pts[0]]
        for i in range(1,len(pts)-1):
            if (pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1])!=(pts[i+1][0]-pts[i][0],pts[i+1][1]-pts[i][1]): out.append(pts[i])
        out.append(pts[-1])
        for a,c in zip(out,out[1:]):
            if math.hypot(c[0]-a[0],c[1]-a[1])<0.05: continue
            t=pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(FM(a[0]),FM(a[1])))
            t.SetEnd(pcbnew.VECTOR2I(FM(c[0]),FM(c[1])))
            t.SetWidth(FM(TW)); t.SetLayer(pcbnew.F_Cu if run[0][2]==0 else pcbnew.B_Cu); t.SetNetCode(code)
            b.Add(t)

def connect(pad, target_pad, code):
    a=pad.GetPosition(); c=target_pad.GetPosition()
    s=(MM(a.x),MM(a.y),0); t=(MM(c.x),MM(c.y),0)
    p=astar2(s,t,code)
    if not p: return False
    emit(p,code)
    return True

# ---------- add components ----------
# F1: insert into 12V_RAW net between J_IN.1 and D1
jin=b.FindFootprintByReference('J_IN'); d1=b.FindFootprintByReference('D1')
p_jin=[p for p in jin.Pads() if p.GetNumber()=='1'][0]
p_d1=[p for p in d1.Pads() if p.GetNetname()=='/12V_RAW'][0]
# remove old tracks of net 12V_RAW
for t in list(b.GetTracks()):
    if t.GetNetCode()==b.FindNet('/12V_RAW').GetNetCode(): b.RemoveNative(t)

fuse=pcbnew.FootprintLoad('/usr/share/kicad/footprints/Fuse.pretty','Fuse_1206_3216Metric')
fuse.SetReference('F1'); fuse.SetValue('PTC 3A')
fuse.SetPosition(pcbnew.VECTOR2I(FM(11),FM(9))); fuse.SetOrientationDegrees(90); b.Add(fuse)
n12=b.FindNet('/12V_RAW'); n12f=pcbnew.NETINFO_ITEM(b,'/12V_FUSED'); b.Add(n12f)
fp=list(fuse.Pads()); fp.sort(key=lambda p:p.GetPosition().y)
fp[0].SetNet(n12); fp[1].SetNet(n12f)
p_d1.SetNet(n12f)
print("F1 added")
# route F1 pads
print(" route F1.1:",connect(fp[0],p_jin,n12.GetNetCode()))
print(" route F1.2:",connect(fp[1],p_d1,n12f.GetNetCode()))

# flyback diodes
nprot=b.FindNet('/12V_PROT'); prot_pad=[p for p in b.FindFootprintByReference('C_BULK1').Pads() if p.GetNetname()=='/12V_PROT'][0]
outfp=b.FindFootprintByReference('J_OUT')
for i in range(8):
    mot='MOT%d'%(i+1); net=b.FindNet('/'+mot)
    if not net: print("no net",mot); continue
    mpad=[p for p in outfp.Pads() if p.GetNetname()=='/'+mot][0]
    dio=pcbnew.FootprintLoad('/usr/share/kicad/footprints/Diode_SMD.pretty','D_SMA')
    if not dio: print("no diode fp"); break
    dio.SetReference('D_FL%d'%(i+1)); dio.SetValue('SS34')
    dio.SetPosition(pcbnew.VECTOR2I(FM(88),FM(48+i*5.5))); dio.SetOrientationDegrees(90); b.Add(dio)
    dp=list(dio.Pads())
    # cathode = pad 2 on SMA (verify); anode = pad1 -> MOT, cathode -> 12V_PROT
    dp[0].SetNet(net); dp[1].SetNet(nprot)
    ok1=connect(dp[0],mpad,net.GetNetCode())
    ok2=connect(dp[1],prot_pad,nprot.GetNetCode())
    print(" diode",i+1,ok1,ok2)

# decoupling caps
for i,(x,y,pnet) in enumerate([(33,12,'/5V_RAIL'),(33,33,'/3V3_RAIL'),(58,52,'/3V3_RAIL'),(75,80,'/3V3_RAIL')]):
    net=b.FindNet(pnet); gnd=b.FindNet('/GND')
    cp=pcbnew.FootprintLoad('/usr/share/kicad/footprints/Capacitor_SMD.pretty','C_0603_1608Metric')
    cp.SetReference('C_DEC%d'%(i+1)); cp.SetValue('100nF')
    cp.SetPosition(pcbnew.VECTOR2I(FM(x),FM(y))); b.Add(cp)
    ps=list(cp.Pads()); ps[0].SetNet(net); ps[1].SetNet(gnd)
    # target pads
    tp=None; tg=None
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname()==pnet and tp is None and f.GetReference() not in ('C_DEC%d'%(i+1),): tp=p
            if p.GetNetname()=='/GND' and tg is None: tg=p
    if tp and tg:
        print(" cap",i+1,connect(ps[0],tp,net.GetNetCode()),connect(ps[1],tg,gnd.GetNetCode()))
    else: print(" cap",i+1,"no target")

pcbnew.SaveBoard(PCB,b)
print("saved")
