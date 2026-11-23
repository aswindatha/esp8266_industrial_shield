"""Iterative single-layer router using A* with accurate obstacle geometry.

Attempts to route every DRC-unconnected connection on F.Cu. New tracks are added
to the board after each successful route. Reports remaining failures.
"""
import pcbnew, os, json, math, heapq, re, sys, copy
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, "ind_8ch_motor_ctrl.kicad_pcb")
MM = pcbnew.ToMM
FM = pcbnew.FromMM
STEP = 0.20
CLR = 0.27          # clearance between different nets (board rule 0.25 + margin)
GRID = int(100.0 / STEP) + 3

def kv(x, y):
    return (int(round(x / STEP)), int(round(y / STEP)))

def load_drc():
    return json.load(open('/tmp/drc_current.json'))

b = pcbnew.LoadBoard(PCB)
drc = load_drc()

# UUID -> item
by_uuid = {}
for t in b.GetTracks():
    by_uuid[str(t.m_Uuid.AsString())] = t
for f in b.GetFootprints():
    for p in f.Pads():
        by_uuid[str(p.m_Uuid.AsString())] = p

# --------- occupancy grid ---------
# cell value = netcode occupying it; -2 = drill/hole keepout
occ = {}

def mark_circle(cx, cy, r, code):
    for gx in range(int((cx-r)/STEP), int((cx+r)/STEP)+1):
        for gy in range(int((cy-r)/STEP), int((cy+r)/STEP)+1):
            x, y = gx*STEP, gy*STEP
            if (x-cx)**2 + (y-cy)**2 <= r*r:
                k=(gx,gy)
                if code == -2 or k not in occ:
                    occ[k]=code

def mark_seg(x0,y0,x1,y1,r,code):
    n=max(1,int(math.hypot(x1-x0,y1-y0)/(STEP*0.4)))
    for i in range(n+1):
        f=i/n
        mark_circle(x0+(x1-x0)*f, y0+(y1-y0)*f, r, code)

def rebuild_occ():
    occ.clear()
    for t in b.GetTracks():
        if t.Type()==pcbnew.PCB_VIA_T:
            p=t.GetPosition(); mark_circle(MM(p.x),MM(p.y),MM(t.GetWidth(pcbnew.F_Cu))/2+CLR,t.GetNetCode())
        else:
            s,e=t.GetStart(),t.GetEnd()
            mark_seg(MM(s.x),MM(s.y),MM(e.x),MM(e.y),MM(t.GetWidth())/2+CLR,t.GetNetCode())
    for f in b.GetFootprints():
        for p in f.Pads():
            pos=p.GetPosition(); sz=p.GetSize()
            if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH:
                mark_circle(MM(pos.x),MM(pos.y),MM(sz.x)/2+0.30,-2)
                continue
            r=max(MM(sz.x),MM(sz.y))/2+CLR
            mark_circle(MM(pos.x),MM(pos.y),r,p.GetNetCode())

rebuild_occ()

def endpoints(u):
    out=[]
    for it in u.get('items',[]):
        uid=it.get('uuid'); obj=by_uuid.get(uid)
        d=it.get('description','')
        m=re.search(r'\[(/[^\]]+)\]', d)
        nm=m.group(1) if m else ''
        nc=b.FindNet(nm).GetNetCode() if nm else -1
        if obj is not None:
            pos=obj.GetPosition()
            if hasattr(obj,'GetStart'): pos=obj.GetStart()
            out.append((MM(pos.x),MM(pos.y),nc,nm,obj))
        else:
            p=it.get('pos',{})
            out.append((p.get('x',0),p.get('y',0),nc,nm,None))
    return out

def astar(s,t,code):
    sk=kv(s[0],s[1]); tk=kv(t[0],t[1])
    def ok(k):
        v=occ.get(k,0)
        return v==0 or v==code
    openh=[(0.0,sk)]; came={}; g={sk:0.0}
    while openh:
        f,cur=heapq.heappop(openh)
        if cur==tk:
            path=[cur]
            while cur in came: cur=came[cur]; path.append(cur)
            path.reverse()
            return [(gx*STEP,gy*STEP) for gx,gy in path]
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            nb=(cur[0]+dx,cur[1]+dy)
            if nb[0]<1 or nb[1]<1 or nb[0]>=GRID or nb[1]>=GRID: continue
            if not ok(nb) and nb!=tk: continue
            ng=g[cur]+(1 if dx==0 or dy==0 else 1.4142)
            if ng<g.get(nb,1e9):
                g[nb]=ng; came[nb]=cur
                h=math.hypot(tk[0]-nb[0],tk[1]-nb[1])
                heapq.heappush(openh,(ng+h,nb))
    return None

def add_track(points,code):
    """Add connected track segments through waypoints (simplify collinear)."""
    if len(points)<2: return 0
    # simplify: keep endpoints and turn points
    pts=[points[0]]
    for i in range(1,len(points)-1):
        p0,p1,p2=points[i-1],points[i],points[i+1]
        v1=(p1[0]-p0[0],p1[1]-p0[1]); v2=(p2[0]-p1[0],p2[1]-p1[1])
        cross=abs(v1[0]*v2[1]-v1[1]*v2[0])
        if cross>1e-6: pts.append(p1)
    pts.append(points[-1])
    n=0
    for a,c in zip(pts,pts[1:]):
        if math.hypot(c[0]-a[0],c[1]-a[1])<0.05: continue
        t=pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(FM(a[0]),FM(a[1])))
        t.SetEnd(pcbnew.VECTOR2I(FM(c[0]),FM(c[1])))
        t.SetWidth(FM(0.30)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(code)
        b.Add(t); n+=1
    return n

results=[]
for i,u in enumerate(drc['unconnected_items']):
    eps=endpoints(u)
    if len(eps)<2: continue
    a,c=eps[0],eps[1]
    code=a[2] if a[2]>0 else c[2]
    if code<=0:
        results.append((i+1,a[3],'NONET',None)); continue
    # Handle zone islands: skip (handled separately)
    if 'Zone' in a[3] or 'Zone' in c[3]:
        results.append((i+1,a[3],'ZONE',None)); continue
    p=astar((a[0],a[1]),(c[0],c[1]),code)
    if p:
        n=add_track(p,code)
        rebuild_occ()
        results.append((i+1,a[3],f'ROUTED({n}seg)',len(p)))
    else:
        results.append((i+1,a[3],'BLOCKED',None))

for r in results:
    print(f"{r[0]:2d} {r[2]:12s} {r[1]}")
pcbnew.SaveBoard(os.path.join(ROOT,'ind_8ch_motor_ctrl.kicad_pcb'), b)
json.dump([{'i':r[0],'net':r[1],'status':r[2]} for r in results],
          open(os.path.join(ROOT,'tools','audit','route_solver_results.json'),'w'),indent=1)
print("saved board")
