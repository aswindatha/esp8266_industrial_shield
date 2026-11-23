"""Optimized global single-layer router.

Key optimizations:
 - GND handled by zone, not tracks (52 pads).
 - Multi-pin nets: greedy nearest-neighbour tree (O(n) A* calls, not O(n^2)).
 - Progress logging per net.
 - Multiple routing orders tried; best saved.
"""
import pcbnew, os, math, heapq, random, sys, time
from collections import defaultdict

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,'ind_8ch_motor_ctrl_SINGLELAYER_WIP.kicad_pcb')
OUT=os.path.join(ROOT,'ind_8ch_motor_ctrl.kicad_pcb')
MM=pcbnew.ToMM; FM=pcbnew.FromMM
STEP=0.25; CLR=0.27; TRACK_W=0.30; KEEPOUT=TRACK_W/2+CLR
GRID=int(100/STEP)+3

def kv(x,y): return (int(round(x/STEP)),int(round(y/STEP)))

b=pcbnew.LoadBoard(PCB)
for t in list(b.GetTracks()): b.RemoveNative(t)
for z in list(b.Zones()): b.RemoveNative(z)

netpads=defaultdict(list)
for f in b.GetFootprints():
    for p in f.Pads():
        nc=p.GetNetCode()
        if nc>0 and not p.GetNetname().startswith('unconnected') and p.GetNetname()!='/GND':
            netpads[nc].append(p)

padpos={}
for f in b.GetFootprints():
    for p in f.Pads():
        q=p.GetPosition(); padpos[(p.GetNetCode(),p.GetNumber(),f.GetReference())]=(MM(q.x),MM(q.y))

def pad_occ():
    d={}
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH: continue
            pos=p.GetPosition(); sz=p.GetSize(); r=max(MM(sz.x),MM(sz.y))/2+CLR
            cx,cy=MM(pos.x),MM(pos.y)
            for gx in range(int((cx-r)/STEP),int((cx+r)/STEP)+1):
                for gy in range(int((cy-r)/STEP),int((cy+r)/STEP)+1):
                    x,y=gx*STEP,gy*STEP
                    if (x-cx)**2+(y-cy)**2<=r*r: d[(gx,gy)]=p.GetNetCode()
    return d
PAD_OCC=pad_occ()

def tracks_occ(tracks):
    d={}
    for t in tracks:
        s,e=t.GetStart(),t.GetEnd(); x0,y0,x1,y1=MM(s.x),MM(s.y),MM(e.x),MM(e.y)
        n=max(1,int(math.hypot(x1-x0,y1-y0)/(STEP*0.4)))
        for i in range(n+1):
            f=i/n; cx,cy=x0+(x1-x0)*f,y0+(y1-y0)*f
            for gx in range(int((cx-KEEPOUT)/STEP),int((cx+KEEPOUT)/STEP)+1):
                for gy in range(int((cy-KEEPOUT)/STEP),int((cy+KEEPOUT)/STEP)+1):
                    x,y=gx*STEP,gy*STEP
                    if (x-cx)**2+(y-cy)**2<=KEEPOUT**2: d[(gx,gy)]=t.GetNetCode()
    return d

def astar(s,t,code,occ):
    sk,tk=kv(*s),kv(*t)
    if sk==tk: return [s,t]
    def ok(k):
        v=occ.get(k,0); return v==0 or v==code
    openh=[(0.0,sk)]; came={}; g={sk:0.0}
    while openh:
        _,cur=heapq.heappop(openh)
        if cur==tk:
            path=[cur]
            while cur in came: cur=came[cur]; path.append(cur)
            path.reverse(); return [(gx*STEP,gy*STEP) for gx,gy in path]
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            nb=(cur[0]+dx,cur[1]+dy)
            if nb[0]<1 or nb[1]<1 or nb[0]>=GRID or nb[1]>=GRID: continue
            if not ok(nb) and nb!=tk: continue
            ng=g[cur]+(1 if dx==0 or dy==0 else 1.4142)
            if ng<g.get(nb,1e9):
                g[nb]=ng; came[nb]=cur
                heapq.heappush(openh,(ng+math.hypot(tk[0]-nb[0],tk[1]-nb[1]),nb))
    return None

def simplify(pts):
    if len(pts)<3: return pts
    out=[pts[0]]
    for i in range(1,len(pts)-1):
        p0,p1,p2=pts[i-1],pts[i],pts[i+1]
        v1=(p1[0]-p0[0],p1[1]-p0[1]); v2=(p2[0]-p1[0],p2[1]-p1[1])
        if abs(v1[0]*v2[1]-v1[1]*v2[0])>1e-6: out.append(p1)
    out.append(pts[-1]); return out

def add_tracks(pts,code,store):
    s=simplify(pts)
    for a,c in zip(s,s[1:]):
        if math.hypot(c[0]-a[0],c[1]-a[1])<0.05: continue
        t=pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(FM(a[0]),FM(a[1])))
        t.SetEnd(pcbnew.VECTOR2I(FM(c[0]),FM(c[1])))
        t.SetWidth(FM(TRACK_W)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(code)
        b.Add(t); store.append(t)

def route_net(nc,pts,occ,store):
    """Greedy nearest-neighbour spanning tree."""
    remaining=list(pts[1:]); connected=[pts[0]]
    while remaining:
        # pick nearest remaining point to any connected point (Euclidean)
        best=None
        for k,cand in enumerate(remaining):
            d=min(math.hypot(cand[0]-c[0],cand[1]-c[1]) for c in connected)
            if best is None or d<best[0]: best=(d,k)
        k=best[1]; cand=remaining.pop(k)
        # A* from nearest connected point
        src=min(connected,key=lambda c:math.hypot(cand[0]-c[0],cand[1]-c[1]))
        p=astar(src,cand,nc,occ)
        if p is None: return False
        add_tracks(p,nc,store); connected.append(cand)
        to=tracks_occ(store)
        for key,val in to.items():
            if val==nc: occ[key]=val
    return True

net_items=[]
for nc,pads in netpads.items():
    if len(pads)<2: continue
    nm=pads[0].GetNetname()
    pts=[padpos[(nc,p.GetNumber(),p.GetParentFootprint().GetReference())] for p in pads]
    length=sum(math.hypot(pts[i][0]-pts[0][0],pts[i][1]-pts[0][1]) for i in range(1,len(pts)))
    net_items.append((nc,nm,pts,length))

def try_order(name,order):
    for t in list(b.GetTracks()): b.RemoveNative(t)
    occ=dict(PAD_OCC); routes={}; failed=[]
    for nc,nm,pts,_ in order:
        st=time.time()
        store=routes.setdefault(nc,[])
        if not route_net(nc,pts,occ,store): failed.append(nm)
        if time.time()-st>20: print(f"    slow: {nm} {time.time()-st:.1f}s",flush=True)
    return len(order)-len(failed),failed,routes

orders={}
orders['short_first']=sorted(net_items,key=lambda x:(len(x[2]),x[3]))
orders['long_first']=sorted(net_items,key=lambda x:(-x[3],))
def grp(x):
    n=x[1]
    if n.startswith('/MOT'): return 0
    if 'DRV' in n: return 1
    if n in ('/3V3_RAIL','/12V_PROT','/5V_RAIL','/12V_RAW'): return 2
    return 3
orders['grouped']=sorted(net_items,key=lambda x:(grp(x),-x[3]))
for i in range(3):
    o=net_items[:]; random.seed(i); random.shuffle(o); orders[f'rand{i}']=o

best=None
for name,order in orders.items():
    t0=time.time()
    ok,failed,routes=try_order(name,order)
    print(f"{name:12s}: {ok}/{len(order)} routed, {len(failed)} failed ({time.time()-t0:.1f}s)",flush=True)
    if best is None or ok>best[0]: best=(ok,name,failed,routes)
print(f"\nBEST: {best[0]}/{len(net_items)} ({best[1]})",flush=True)
if best[2]: print("failed:",best[2],flush=True)

for t in list(b.GetTracks()): b.RemoveNative(t)
for nc,trs in best[3].items():
    for t in trs: b.Add(t)

# GND zone
gn=b.FindNet('/GND')
if gn:
    z=pcbnew.ZONE(b); z.SetLayer(pcbnew.F_Cu); z.SetNet(gn); z.SetLocalClearance(FM(0.30))
    poly=z.Outline(); poly.NewOutline()
    for x,y in [(0.5,0.5),(99.5,0.5),(99.5,99.5),(0.5,99.5)]: poly.Append(FM(x),FM(y))
    b.Add(z)
try: pcbnew.FillZones(b.Zones(),b.GetConnectivity(),True)
except Exception as e: print("fillzones:",e)
pcbnew.SaveBoard(OUT,b)
print("saved",OUT,flush=True)
