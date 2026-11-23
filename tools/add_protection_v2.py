"""Add protection components to 2-layer board with correct incremental occupancy."""
import pcbnew, os, math, heapq
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,'ind_8ch_motor_ctrl.kicad_pcb')
MM=pcbnew.ToMM; FM=pcbnew.FromMM
STEP=0.25; GRID=int(100/STEP)+4; CLR=0.55; TW=0.30; VIA_W=0.60; VIA_D=0.30

def kv(x,y): return (int(round(x/STEP)),int(round(y/STEP)))
b=pcbnew.LoadBoard(PCB)
occ={}

def mark_circle(cx,cy,r,code,layer):
    for gx in range(int((cx-r)/STEP),int((cx+r)/STEP)+1):
        for gy in range(int((cy-r)/STEP),int((cy+r)/STEP)+1):
            x,y=gx*STEP,gy*STEP
            if (x-cx)**2+(y-cy)**2<=r*r:
                k=(gx,gy,layer)
                if code==-2 or k not in occ: occ[k]=code

def rebuild():
    occ.clear()
    for f in b.GetFootprints():
        for p in f.Pads():
            q=p.GetPosition(); sz=p.GetSize(); cx,cy=MM(q.x),MM(q.y)
            if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH:
                for L in (0,1): mark_circle(cx,cy,MM(sz.x)/2+0.3,-2,L)
                continue
            r=min(MM(sz.x),MM(sz.y))/2+CLR
            layers=[0,1] if p.GetAttribute()==pcbnew.PAD_ATTRIB_PTH else [0]
            for L in layers: mark_circle(cx,cy,r,p.GetNetCode(),L)
    for t in b.GetTracks():
        nc=t.GetNetCode()
        if t.Type()==pcbnew.PCB_VIA_T:
            q=t.GetPosition()
            for L in (0,1): mark_circle(MM(q.x),MM(q.y),VIA_W/2+CLR,nc,L)
        else:
            L=0 if t.GetLayer()==pcbnew.F_Cu else 1
            s,e=t.GetStart(),t.GetEnd(); x0,y0,x1,y1=MM(s.x),MM(s.y),MM(e.x),MM(e.y)
            n=max(1,int(math.hypot(x1-x0,y1-y0)/(STEP*0.4)))
            for i in range(n+1):
                f2=i/n; mark_circle(x0+(x1-x0)*f2,y0+(y1-y0)*f2,MM(t.GetWidth())/2+CLR,nc,L)

def astar2(s,t,code):
    sk=(kv(s[0],s[1])[0],kv(s[0],s[1])[1],s[2]); tk=(kv(t[0],t[1])[0],kv(t[0],t[1])[1],t[2])
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
        nb=(x,y,1-L)
        if ok(nb) and nb!=tk:
            ng=g[cur]+8.0
            if ng<g.get(nb,1e9):
                g[nb]=ng; came[nb]=cur
                heapq.heappush(openh,(ng+abs(tk[0]-nb[0])+abs(tk[1]-nb[1]),nb))
    return None

def emit(path,code):
    # vias at layer transitions
    for prev,k in zip(path,path[1:]):
        if k[2]!=prev[2]:
            v=pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(FM(prev[0]*STEP),FM(prev[1]*STEP)))
            v.SetWidth(FM(VIA_W)); v.SetDrill(FM(VIA_D)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu); v.SetNetCode(code); b.Add(v)
    runs=[]; run=[]
    for k in path:
        if not run or k[2]==run[-1][2]: run.append(k)
        else: runs.append(run); run=[k]
    if run: runs.append(run)
    for run in runs:
        pts=[(k[0]*STEP,k[1]*STEP) for k in run]
        if len(pts)<2: continue
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

def connect(pad,target,code):
    a=pad.GetPosition(); c=target.GetPosition()
    p=astar2((MM(a.x),MM(a.y),0),(MM(c.x),MM(c.y),0),code)
    if not p: return False
    emit(p,code); rebuild(); return True

# --- value fixes already applied; now components ---
rebuild()
jin=b.FindFootprintByReference('J_IN'); d1=b.FindFootprintByReference('D1')
pj=[p for p in jin.Pads() if p.GetNumber()=='1'][0]
pd=[p for p in d1.Pads() if p.GetNetname()=='/12V_RAW'][0]
n12=b.FindNet('/12V_RAW')
for t in list(b.GetTracks()):
    if t.GetNetCode()==n12.GetNetCode(): b.RemoveNative(t)
rebuild()
fuse=pcbnew.FootprintLoad('/usr/share/kicad/footprints/Fuse.pretty','Fuse_1206_3216Metric')
fuse.SetReference('F1'); fuse.SetValue('PTC 3A'); fuse.SetPosition(pcbnew.VECTOR2I(FM(11),FM(9))); fuse.SetOrientationDegrees(90); b.Add(fuse)
n12f=pcbnew.NETINFO_ITEM(b,'/12V_FUSED'); b.Add(n12f)
fp=list(fuse.Pads()); fp.sort(key=lambda p:p.GetPosition().y)
fp[0].SetNet(n12); fp[1].SetNet(n12f); pd.SetNet(n12f)
rebuild()
print("F1:",connect(fp[0],pj,n12.GetNetCode()),connect(fp[1],pd,n12f.GetNetCode()),flush=True)

nprot=b.FindNet('/12V_PROT')
prot=[p for p in b.FindFootprintByReference('C_BULK1').Pads() if p.GetNetname()=='/12V_PROT'][0]
out=b.FindFootprintByReference('J_OUT')
for i in range(8):
    mot='MOT%d'%(i+1); net=b.FindNet('/'+mot)
    mp=[p for p in out.Pads() if p.GetNetname()=='/'+mot][0]
    dio=pcbnew.FootprintLoad('/usr/share/kicad/footprints/Diode_SMD.pretty','D_SMA')
    dio.SetReference('D_FL%d'%(i+1)); dio.SetValue('SS34')
    dio.SetPosition(pcbnew.VECTOR2I(FM(88),FM(48+i*5.5))); dio.SetOrientationDegrees(90); b.Add(dio)
    dp=list(dio.Pads()); dp[0].SetNet(net); dp[1].SetNet(nprot); rebuild()
    print("D_FL%d"%(i+1),connect(dp[0],mp,net.GetNetCode()),connect(dp[1],prot,nprot.GetNetCode()),flush=True)

for i,(x,y,pnet) in enumerate([(33,12,'/5V_RAIL'),(33,33,'/3V3_RAIL'),(58,52,'/3V3_RAIL'),(75,80,'/3V3_RAIL')]):
    net=b.FindNet(pnet); gnd=b.FindNet('/GND')
    cp=pcbnew.FootprintLoad('/usr/share/kicad/footprints/Capacitor_SMD.pretty','C_0603_1608Metric')
    cp.SetReference('C_DEC%d'%(i+1)); cp.SetValue('100nF')
    cp.SetPosition(pcbnew.VECTOR2I(FM(x),FM(y))); b.Add(cp)
    ps=list(cp.Pads()); ps[0].SetNet(net); ps[1].SetNet(gnd); rebuild()
    tp=tg=None
    for f in b.GetFootprints():
        if f.GetReference().startswith('C_DEC'): continue
        for p in f.Pads():
            if p.GetNetname()==pnet and tp is None: tp=p
            if p.GetNetname()=='/GND' and tg is None: tg=p
    ok1=connect(ps[0],tp,net.GetNetCode()) if tp else False
    ok2=connect(ps[1],tg,gnd.GetNetCode()) if tg else False
    print("C_DEC%d"%(i+1),ok1,ok2,flush=True)

pcbnew.SaveBoard(PCB,b); print("saved",flush=True)
