"""PathFinder-style negotiated-congestion single-layer global router.

Every net is re-routed each iteration with A* whose cell cost rises for cells
currently overused by other nets. History costs accumulate until all nets are
routed with zero shared cells. Pads of other nets are hard obstacles.
"""
import pcbnew, os, math, heapq, time
from collections import defaultdict

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,'ind_8ch_motor_ctrl_SINGLELAYER_WIP.kicad_pcb')
OUT=os.path.join(ROOT,'ind_8ch_motor_ctrl.kicad_pcb')
MM=pcbnew.ToMM; FM=pcbnew.FromMM
STEP=0.25; CLR=0.27; TRACK_W=0.30; KEEPOUT=TRACK_W/2+CLR
GRID=int(100/STEP)+3
PRESENT_K=2.0; HIST_K=1.0

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

# hard obstacles: other-net pads (netcode -> set of cells)
pad_cells=defaultdict(set)
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH: continue
        pos=p.GetPosition(); sz=p.GetSize(); r=min(MM(sz.x),MM(sz.y))/2+CLR
        cx,cy=MM(pos.x),MM(pos.y)
        for gx in range(int((cx-r)/STEP),int((cx+r)/STEP)+1):
            for gy in range(int((cy-r)/STEP),int((cy+r)/STEP)+1):
                x,y=gx*STEP,gy*STEP
                if (x-cx)**2+(y-cy)**2<=r*r: pad_cells[(gx,gy)].add(p.GetNetCode())

nets=[]
for nc,pads in netpads.items():
    if len(pads)<2: continue
    nm=pads[0].GetNetname()
    pts=[padpos[(nc,p.GetNumber(),p.GetParentFootprint().GetReference())] for p in pads]
    nets.append((nc,nm,pts))
print(f"routing {len(nets)} nets (GND via zone)",flush=True)

# PathFinder state
present=defaultdict(set)   # cell -> set of netcodes currently using
history=defaultdict(float) # cell -> history congestion cost
routes={}                  # netcode -> list of cell-paths (each a list of grid cells)

def cell_ok(code,k):
    """Hard obstacle if another *connected* net's pad occupies this cell."""
    return not ((pad_cells.get(k,set()) - {code, 0}))

def astar_pf(s,t,code):
    sk,tk=kv(*s),kv(*t)
    openh=[(0.0,sk)]; came={}; g={sk:0.0}
    while openh:
        _,cur=heapq.heappop(openh)
        if cur==tk:
            path=[cur]
            while cur in came: cur=came[cur]; path.append(cur)
            path.reverse(); return path
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            nb=(cur[0]+dx,cur[1]+dy)
            if nb[0]<1 or nb[1]<1 or nb[0]>=GRID or nb[1]>=GRID: continue
            if not cell_ok(code,nb) and nb!=tk: continue
            other=present.get(nb,set())-{code}
            cost=1.0+PRESENT_K*len(other)+HIST_K*history.get(nb,0.0)
            ng=g[cur]+cost*(1 if dx==0 or dy==0 else 1.4142)
            if ng<g.get(nb,1e9):
                g[nb]=ng; came[nb]=cur
                heapq.heappush(openh,(ng+math.hypot(tk[0]-nb[0],tk[1]-nb[1]),nb))
    return None

def mark_path(path,code):
    for k in path: present[k].add(code)

def route_all():
    global present
    present=defaultdict(set); routes.clear()
    for nc,nm,pts in nets:
        # greedy nearest-neighbour tree
        remaining=list(pts[1:]); connected=[pts[0]]; paths=[]
        for _ in range(len(remaining)):
            best=min(range(len(remaining)),key=lambda i:min(
                math.hypot(remaining[i][0]-c[0],remaining[i][1]-c[1]) for c in connected))
            cand=remaining.pop(best)
            src=min(connected,key=lambda c:math.hypot(cand[0]-c[0],cand[1]-c[1]))
            p=astar_pf(src,cand,nc)
            if p is None:
                print(f"  FAIL {nm}: {src} -> {cand}",flush=True)
                return False
            paths.append(p); mark_path(p,nc); connected.append(cand)
        routes[nc]=paths
    return True

def overuse():
    ov=0
    for k,s in present.items():
        if len(s)>1: ov+=len(s)-1
    return ov

t0=time.time(); converged=False
for it in range(80):
    ok=route_all()
    if not ok:
        print(f"iter {it}: A* FAILED to find path (hard obstacle)",flush=True)
        break
    ov=overuse()
    if it%5==0 or ov==0:
        print(f"iter {it}: overuse={ov} ({time.time()-t0:.1f}s)",flush=True)
    if ov==0:
        converged=True; break
    for k,s in present.items():
        if len(s)>1: history[k]+=len(s)-1
    PRESENT_K=min(PRESENT_K*1.3,60)

print("CONVERGED" if converged else "NOT CONVERGED",flush=True)

if converged:
    # convert cell paths to tracks
    for t in list(b.GetTracks()): b.RemoveNative(t)
    def simplify(cells):
        pts=[(gx*STEP,gy*STEP) for gx,gy in cells]
        if len(pts)<3: return pts
        out=[pts[0]]
        for i in range(1,len(pts)-1):
            p0,p1,p2=pts[i-1],pts[i],pts[i+1]
            v1=(p1[0]-p0[0],p1[1]-p0[1]); v2=(p2[0]-p1[0],p2[1]-p1[1])
            if abs(v1[0]*v2[1]-v1[1]*v2[0])>1e-6: out.append(p1)
        out.append(pts[-1]); return out
    for nc,paths in routes.items():
        for path in paths:
            s=simplify(path)
            for a,c in zip(s,s[1:]):
                if math.hypot(c[0]-a[0],c[1]-a[1])<0.05: continue
                t=pcbnew.PCB_TRACK(b)
                t.SetStart(pcbnew.VECTOR2I(FM(a[0]),FM(a[1])))
                t.SetEnd(pcbnew.VECTOR2I(FM(c[0]),FM(c[1])))
                t.SetWidth(FM(TRACK_W)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(nc)
                b.Add(t)

gn=b.FindNet('/GND')
if gn:
    z=pcbnew.ZONE(b); z.SetLayer(pcbnew.F_Cu); z.SetNet(gn); z.SetLocalClearance(FM(0.30))
    poly=z.Outline(); poly.NewOutline()
    for x,y in [(0.5,0.5),(99.5,0.5),(99.5,99.5),(0.5,99.5)]: poly.Append(FM(x),FM(y))
    b.Add(z)
try: pcbnew.ZONE_FILLER(b).Fill(b.Zones())
except Exception as e: print("fillzones:",e)
pcbnew.SaveBoard(OUT,b)
print("saved",OUT,flush=True)
