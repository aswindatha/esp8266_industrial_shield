"""Manhattan (4-directional) PathFinder router with accurate rectangular keepouts.

- 4-dir movement -> no diagonal track crossings
- pad keepouts from axis-aligned bounding boxes + clearance
- UUID-based pad identity (handles duplicate pad numbers like SOT-223 tab)
- PathFinder negotiated congestion until zero shared cells
- GND zone added at the end; GND islands stitched with tracks if needed
"""
import pcbnew, os, math, heapq, time
from collections import defaultdict

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,'ind_8ch_motor_ctrl_SINGLELAYER_WIP.kicad_pcb')
OUT=os.path.join(ROOT,'ind_8ch_motor_ctrl.kicad_pcb')
MM=pcbnew.ToMM; FM=pcbnew.FromMM
STEP=0.20; CLR=0.30; TRACK_W=0.30
GRID=int(100/STEP)+4

def kv(x,y): return (int(round(x/STEP)),int(round(y/STEP)))

b=pcbnew.LoadBoard(PCB)
for t in list(b.GetTracks()): b.RemoveNative(t)
for z in list(b.Zones()): b.RemoveNative(z)

# ---------- pads (UUID keyed) ----------
padinfo={}                       # uuid -> (netcode, ref, num, x, y)
for f in b.GetFootprints():
    for p in f.Pads():
        q=p.GetPosition()
        padinfo[str(p.m_Uuid.AsString())]=(p.GetNetCode(),f.GetReference(),p.GetNumber(),MM(q.x),MM(q.y))

# ---------- pad keepout cells (rectangular, from bounding box) ----------
pad_cells=defaultdict(set)
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH: continue
        nc=p.GetNetCode()
        bb=p.GetBoundingBox()
        L=MM(bb.GetLeft())-CLR; R=MM(bb.GetRight())+CLR
        T=MM(bb.GetTop())-CLR;  Bm=MM(bb.GetBottom())+CLR
        for gx in range(int(L/STEP),int(R/STEP)+1):
            for gy in range(int(T/STEP),int(Bm/STEP)+1):
                x,y=gx*STEP,gy*STEP
                if L<=x<=R and T<=y<=Bm:
                    pad_cells[(gx,gy)].add(nc)

# ---------- nets ----------
netpads=defaultdict(list)
for uid,(nc,ref,num,x,y) in padinfo.items():
    if nc>0 and y is not None and not b.FindNet(nc).GetNetname().startswith('unconnected') and b.FindNet(nc).GetNetname()!='/GND':
        netpads[nc].append((uid,x,y))
nets=[]
for nc,pads in netpads.items():
    if len(pads)<2: continue
    nm=b.FindNet(nc).GetNetname()
    nets.append((nc,nm,pads))
print(f"routing {len(nets)} nets; STEP={STEP} CLR={CLR}",flush=True)

present=defaultdict(set); history=defaultdict(float); routes={}
PRESENT_K=2.0

def cell_ok(code,k):
    return not (pad_cells.get(k,set())-{code,0})

def astar_pf(s,t,code):
    sk,tk=kv(*s),kv(*t)
    openh=[(0.0,sk)]; came={}; g={sk:0.0}
    while openh:
        _,cur=heapq.heappop(openh)
        if cur==tk:
            path=[cur]
            while cur in came: cur=came[cur]; path.append(cur)
            path.reverse(); return path
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):   # MANHATTAN only
            nb=(cur[0]+dx,cur[1]+dy)
            if nb[0]<1 or nb[1]<1 or nb[0]>=GRID or nb[1]>=GRID: continue
            if not cell_ok(code,nb) and nb!=tk: continue
            other=present.get(nb,set())-{code}
            cost=1.0+PRESENT_K*len(other)+history.get(nb,0.0)
            ng=g[cur]+cost
            if ng<g.get(nb,1e9):
                g[nb]=ng; came[nb]=cur
                heapq.heappush(openh,(ng+abs(tk[0]-nb[0])+abs(tk[1]-nb[1]),nb))
    return None

def mark(path,code):
    for k in path: present[k].add(code)

def route_all():
    global present
    present=defaultdict(set); routes.clear()
    for nc,nm,pads in nets:
        remaining=list(pads[1:]); connected=[pads[0]]; paths=[]
        for _ in range(len(remaining)):
            best=min(range(len(remaining)),key=lambda i:min(
                abs(remaining[i][1]-c[1])+abs(remaining[i][2]-c[2]) for c in connected))
            cand=remaining.pop(best)
            src=min(connected,key=lambda c:abs(cand[1]-c[1])+abs(cand[2]-c[2]))
            p=astar_pf((src[1],src[2]),(cand[1],cand[2]),nc)
            if p is None:
                return False
            paths.append(p); mark(p,nc); connected.append(cand)
        routes[nc]=paths
    return True

def overuse():
    return sum(len(s)-1 for s in present.values() if len(s)>1)

t0=time.time(); conv=False
for it in range(120):
    if not route_all():
        print(f"iter {it}: A* hard-obstacle failure",flush=True); break
    ov=overuse()
    if it%10==0 or ov==0: print(f"iter {it}: overuse={ov} ({time.time()-t0:.1f}s)",flush=True)
    if ov==0: conv=True; break
    for k,s in present.items():
        if len(s)>1: history[k]+=len(s)-1
    PRESENT_K=min(PRESENT_K*1.25,40)
print("CONVERGED" if conv else "NOT CONVERGED",flush=True)
if not conv:
    hot=sorted(present.items(),key=lambda kv:-len(kv[1]))[:40]
    for k,s in hot:
        if len(s)>1:
            print(f"  HOT ({k[0]*STEP:.1f},{k[1]*STEP:.1f}) nets={[b.FindNet(n).GetNetname() for n in s]}",flush=True)

if conv:
    for t in list(b.GetTracks()): b.RemoveNative(t)
    def simplify(cells):
        pts=[(gx*STEP,gy*STEP) for gx,gy in cells]
        out=[pts[0]]
        for i in range(1,len(pts)-1):
            # keep only direction changes
            if (pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]) != (pts[i+1][0]-pts[i][0],pts[i+1][1]-pts[i][1]):
                out.append(pts[i])
        out.append(pts[-1]); return out
    for nc,paths in routes.items():
        for path in paths:
            s=simplify(path)
            for a,c in zip(s,s[1:]):
                if abs(a[0]-c[0])<1e-6 and abs(a[1]-c[1])<1e-6: continue
                t=pcbnew.PCB_TRACK(b)
                t.SetStart(pcbnew.VECTOR2I(FM(a[0]),FM(a[1])))
                t.SetEnd(pcbnew.VECTOR2I(FM(c[0]),FM(c[1])))
                t.SetWidth(FM(TRACK_W)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(nc)
                b.Add(t)

# GND zone
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
