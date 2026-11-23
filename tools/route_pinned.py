"""Single-layer router with J_IN pin reassignment to make topology planar.

J_IN pins are reassigned so their vertical order matches the vertical order of
their destination pads (power top, I2C/UART middle, sensors bottom). This removes
the connector-area crossings that blocked previous routing attempts.
Power nets use zones; signal nets use Manhattan PathFinder.
"""
import pcbnew, os, math, heapq, time
from collections import defaultdict

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,'ind_8ch_motor_ctrl_SINGLELAYER_WIP.kicad_pcb')
OUT=os.path.join(ROOT,'ind_8ch_motor_ctrl.kicad_pcb')
MM=pcbnew.ToMM; FM=pcbnew.FromMM
STEP=0.20; CLR=0.30; TRACK_W=0.30; GRID=int(100/STEP)+4
POWER_NETS={'/12V_PROT','/3V3_RAIL','/GND'}

# New J_IN pinout: pin -> net (chosen to match destination y-order)
NEW_PINNETS={1:'12V_PROT',2:'12V_RAW',3:'3V3_RAIL',4:'I2C_SCL',5:'UART_TX',
             6:'UART_RX',7:'I2C_SDA',8:'SENS_IN1',9:'SENS_IN2',10:'SENS_IN3',
             11:'SENS_IN4',12:'GND'}

def kv(x,y): return (int(round(x/STEP)),int(round(y/STEP)))
b=pcbnew.LoadBoard(PCB)
for t in list(b.GetTracks()): b.RemoveNative(t)
for z in list(b.Zones()): b.RemoveNative(z)

# reassign J_IN pad nets
jin=b.FindFootprintByReference('J_IN')
for p in jin.Pads():
    n=int(p.GetNumber())
    if n in NEW_PINNETS:
        net=b.FindNet('/'+NEW_PINNETS[n])
        if net: p.SetNet(net)
print("J_IN pinout reassigned (planar order)",flush=True)

padinfo={}
for f in b.GetFootprints():
    for p in f.Pads():
        q=p.GetPosition(); padinfo[str(p.m_Uuid.AsString())]=(p.GetNetCode(),f.GetReference(),p.GetNumber(),MM(q.x),MM(q.y))

pad_cells=defaultdict(set)
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH: continue
        nc=p.GetNetCode(); bb=p.GetBoundingBox()
        L=MM(bb.GetLeft())-CLR; R=MM(bb.GetRight())+CLR
        T=MM(bb.GetTop())-CLR; Bm=MM(bb.GetBottom())+CLR
        for gx in range(int(L/STEP),int(R/STEP)+1):
            for gy in range(int(T/STEP),int(Bm/STEP)+1):
                x,y=gx*STEP,gy*STEP
                if L<=x<=R and T<=y<=Bm: pad_cells[(gx,gy)].add(nc)

netpads=defaultdict(list)
for uid,(nc,ref,num,x,y) in padinfo.items():
    nm=b.FindNet(nc).GetNetname() if nc>0 else ''
    if nc>0 and nm not in POWER_NETS and not nm.startswith('unconnected'):
        netpads[nc].append((uid,x,y))
nets=[(nc,b.FindNet(nc).GetNetname(),p) for nc,p in netpads.items() if len(p)>=2]
print(f"routing {len(nets)} SIGNAL nets",flush=True)

present=defaultdict(set); history=defaultdict(float); routes={}; PRESENT_K=2.0
def cell_ok(code,k): return not (pad_cells.get(k,set())-{code,0})

def astar_pf(s,t,code):
    sk,tk=kv(*s),kv(*t); openh=[(0.0,sk)]; came={}; g={sk:0.0}
    while openh:
        _,cur=heapq.heappop(openh)
        if cur==tk:
            path=[cur]
            while cur in came: cur=came[cur]; path.append(cur)
            path.reverse(); return path
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nb=(cur[0]+dx,cur[1]+dy)
            if nb[0]<1 or nb[1]<1 or nb[0]>=GRID or nb[1]>=GRID: continue
            if not cell_ok(code,nb) and nb!=tk: continue
            other=present.get(nb,set())-{code}
            ng=g[cur]+1.0+PRESENT_K*len(other)+history.get(nb,0.0)
            if ng<g.get(nb,1e9):
                g[nb]=ng; came[nb]=cur
                heapq.heappush(openh,(ng+abs(tk[0]-nb[0])+abs(tk[1]-nb[1]),nb))
    return None

def route_all():
    global present; present=defaultdict(set); routes.clear()
    for nc,nm,pads in nets:
        remaining=list(pads[1:]); connected=[pads[0]]; paths=[]
        for _ in range(len(remaining)):
            best=min(range(len(remaining)),key=lambda i:min(abs(remaining[i][1]-c[1])+abs(remaining[i][2]-c[2]) for c in connected))
            cand=remaining.pop(best)
            src=min(connected,key=lambda c:abs(cand[1]-c[1])+abs(cand[2]-c[2]))
            p=astar_pf((src[1],src[2]),(cand[1],cand[2]),nc)
            if p is None: return False
            paths.append(p)
            for k in p: present[k].add(nc)
            connected.append(cand)
        routes[nc]=paths
    return True

def overuse(): return sum(len(s)-1 for s in present.values() if len(s)>1)
t0=time.time(); conv=False
for it in range(150):
    if not route_all(): print(f"iter {it}: A* fail",flush=True); break
    ov=overuse()
    if it%10==0 or ov==0: print(f"iter {it}: overuse={ov} ({time.time()-t0:.1f}s)",flush=True)
    if ov==0: conv=True; break
    for k,s in present.items():
        if len(s)>1: history[k]+=len(s)-1
    PRESENT_K=min(PRESENT_K*1.25,50)
print("CONVERGED" if conv else "NOT CONVERGED",flush=True)

if conv:
    def simplify(cells):
        pts=[(gx*STEP,gy*STEP) for gx,gy in cells]; out=[pts[0]]
        for i in range(1,len(pts)-1):
            if (pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1])!=(pts[i+1][0]-pts[i][0],pts[i+1][1]-pts[i][1]):
                out.append(pts[i])
        out.append(pts[-1]); return out
    for nc,paths in routes.items():
        for path in paths:
            s=simplify(path)
            for a,c in zip(s,s[1:]):
                if a==c: continue
                t=pcbnew.PCB_TRACK(b)
                t.SetStart(pcbnew.VECTOR2I(FM(a[0]),FM(a[1])))
                t.SetEnd(pcbnew.VECTOR2I(FM(c[0]),FM(c[1])))
                t.SetWidth(FM(TRACK_W)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(nc)
                b.Add(t)

def add_zone(netname,priority):
    n=b.FindNet(netname)
    if not n: return
    z=pcbnew.ZONE(b); z.SetLayer(pcbnew.F_Cu); z.SetNet(n); z.SetPriority(priority)
    z.SetLocalClearance(FM(0.30))
    poly=z.Outline(); poly.NewOutline()
    for x,y in [(0.5,0.5),(99.5,0.5),(99.5,99.5),(0.5,99.5)]: poly.Append(FM(x),FM(y))
    b.Add(z)
add_zone('/12V_PROT',2); add_zone('/3V3_RAIL',1); add_zone('/GND',0)
try: pcbnew.ZONE_FILLER(b).Fill(b.Zones())
except Exception as e: print("fillzones:",e)
pcbnew.SaveBoard(OUT,b); print("saved",OUT,flush=True)
