"""Count how many 0-ohm jumpers the single-layer board needs.

For each DRC-unconnected connection, try A* with other-net copper as HARD
obstacles. If a clean path exists -> no jumper. Otherwise -> at least one
jumper is required (one blocking crossing).
"""
import pcbnew, os, json, math, heapq, re
from collections import defaultdict
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,'1layer_prototype','ind_8ch_motor_ctrl.kicad_pcb')
MM=pcbnew.ToMM
STEP=0.25; GRID=int(100/STEP)+3; CLR=0.32
def kv(x,y): return (int(round(x/STEP)),int(round(y/STEP)))
b=pcbnew.LoadBoard(PCB)
drc=json.load(open('/tmp/1l_base.json'))
by_uuid={}
for t in b.GetTracks(): by_uuid[str(t.m_Uuid.AsString())]=t
for f in b.GetFootprints():
    for p in f.Pads(): by_uuid[str(p.m_Uuid.AsString())]=p
# occupancy
occ={}
def mark(cx,cy,r,code):
    for gx in range(int((cx-r)/STEP),int((cx+r)/STEP)+1):
        for gy in range(int((cy-r)/STEP),int((cy+r)/STEP)+1):
            x,y=gx*STEP,gy*STEP
            if (x-cx)**2+(y-cy)**2<=r*r:
                k=(gx,gy)
                if k not in occ: occ[k]=code
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH: continue
        q=p.GetPosition(); sz=p.GetSize(); r=min(MM(sz.x),MM(sz.y))/2+CLR
        mark(MM(q.x),MM(q.y),r,p.GetNetCode())
for t in b.GetTracks():
    s,e=t.GetStart(),t.GetEnd(); x0,y0,x1,y1=MM(s.x),MM(s.y),MM(e.x),MM(e.y)
    n=max(1,int(math.hypot(x1-x0,y1-y0)/(STEP*0.4)))
    for i in range(n+1):
        f2=i/n; mark(x0+(x1-x0)*f2,y0+(y1-y0)*f2,MM(t.GetWidth())/2+CLR,t.GetNetCode())
def astar(s,t,code):
    sk,tk=kv(*s),kv(*t)
    def ok(k):
        v=occ.get(k,0); return v==0 or v==code
    o=[(0.0,sk)]; came={}; g={sk:0.0}
    while o:
        _,cur=heapq.heappop(o)
        if cur==tk: return True
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nb=(cur[0]+dx,cur[1]+dy)
            if nb[0]<1 or nb[1]<1 or nb[0]>=GRID or nb[1]>=GRID: continue
            if not ok(nb) and nb!=tk: continue
            ng=g[cur]+1
            if ng<g.get(nb,1e9):
                g[nb]=ng; came[nb]=cur
                heapq.heappush(o,(ng+abs(tk[0]-nb[0])+abs(tk[1]-nb[1]),nb))
    return False
routable=0; need=0; zone=0
print("#  net                endpoints                         clean-path?  jumpers")
for i,u in enumerate(drc['unconnected_items']):
    its=u.get('items',[])
    if len(its)<2: continue
    a,c=its[0],its[1]
    if 'Zone' in a.get('description','') or 'Zone' in c.get('description',''):
        zone+=1; print(f"{i+1:2d} ZONE-ISLAND (stitch track / zone fix)"); continue
    ao=by_uuid.get(a.get('uuid')); co=by_uuid.get(c.get('uuid'))
    if not ao or not co: continue
    pa=ao.GetStart() if hasattr(ao,'GetStart') else ao.GetPosition()
    pc=co.GetStart() if hasattr(co,'GetStart') else co.GetPosition()
    A=(MM(pa.x),MM(pa.y)); C=(MM(pc.x),MM(pc.y))
    m=re.search(r'\[(/[^\]]+)\]',a.get('description',''))
    nm=m.group(1) if m else '?'
    nc=b.FindNet(nm).GetNetCode() if nm else -1
    r=astar(A,C,nc)
    if r: routable+=1; j=0
    else: need+=1; j='>=1'
    print(f"{i+1:2d} {nm:18s} ({A[0]:5.1f},{A[1]:5.1f})->({C[0]:5.1f},{C[1]:5.1f})  {'YES' if r else 'NO':3s}          {j}")
print(f"\nZone islands: {zone}; clean-routable: {routable}; need jumper(s): {need}")
print(f"MINIMUM jumpers required: {need}  (one per blocked connection)")
