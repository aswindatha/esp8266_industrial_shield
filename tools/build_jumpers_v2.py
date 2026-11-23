"""Recursive 0R-jumper insertion for single-layer routing.

- Try A* between two points treating all other-net copper as HARD obstacles.
- If blocked, force a soft path, find the blocking trace, place an 0805 0R jumper
  straddling it, and recurse on each side (A->pad1, pad2->B).
- Jumper graphics hidden; DRC exclusions generated for jumper-internal nets.
"""
import pcbnew, os, json, math, heapq, re
from collections import defaultdict

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,'ind_8ch_motor_ctrl.kicad_pcb')
MM=pcbnew.ToMM; FM=pcbnew.FromMM
STEP=0.25; GRID=int(100/STEP)+3
CLR=0.32; TW=0.30
FP_LIB='/usr/share/kicad/footprints/Resistor_SMD.pretty'; FP_NAME='R_0805_2012Metric'

b=pcbnew.LoadBoard(PCB)
drc=json.load(open('/tmp/drc_single_orig.json'))
by_uuid={}
for t in b.GetTracks(): by_uuid[str(t.m_Uuid.AsString())]=t
for f in b.GetFootprints():
    for p in f.Pads(): by_uuid[str(p.m_Uuid.AsString())]=p

def kv(x,y): return (int(round(x/STEP)),int(round(y/STEP)))

pad_occ={}
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH: continue
        q=p.GetPosition(); sz=p.GetSize(); r=min(MM(sz.x),MM(sz.y))/2+CLR
        cx,cy=MM(q.x),MM(q.y)
        for gx in range(int((cx-r)/STEP),int((cx+r)/STEP)+1):
            for gy in range(int((cy-r)/STEP),int((cy+r)/STEP)+1):
                x,y=gx*STEP,gy*STEP
                if (x-cx)**2+(y-cy)**2<=r*r: pad_occ[(gx,gy)]=p.GetNetCode()

track_occ={}
for t in b.GetTracks():
    s,e=t.GetStart(),t.GetEnd(); x0,y0,x1,y1=MM(s.x),MM(s.y),MM(e.x),MM(e.y)
    n=max(1,int(math.hypot(x1-x0,y1-y0)/(STEP*0.3)))
    for i in range(n+1):
        f=i/n; cx,cy=x0+(x1-x0)*f,y0+(y1-y0)*f
        for gx in range(int((cx-0.50)/STEP),int((cx+0.50)/STEP)+1):
            for gy in range(int((cy-0.50)/STEP),int((cy+0.50)/STEP)+1):
                x,y=gx*STEP,gy*STEP
                if (x-cx)**2+(y-cy)**2<=0.50**2: track_occ.setdefault((gx,gy),[]).append((t,x0,y0,x1,y1))

def astar(s,t,code,soft):
    sk,tk=kv(*s),kv(*t); openh=[(0.0,sk)]; came={}; g={sk:0.0}
    while openh:
        _,cur=heapq.heappop(openh)
        if cur==tk:
            path=[cur]
            while cur in came: cur=came[cur]; path.append(cur)
            path.reverse(); return [(gx*STEP,gy*STEP) for gx,gy in path]
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nb=(cur[0]+dx,cur[1]+dy)
            if nb[0]<1 or nb[1]<1 or nb[0]>=GRID or nb[1]>=GRID: continue
            if pad_occ.get(nb,0) not in (0,code) and nb!=tk: continue
            others=[e for e in track_occ.get(nb,[]) if e[0].GetNetCode()!=code]
            if others and not soft and nb!=tk: continue
            cost=1.0+(6.0*len(others) if soft and others else 0)
            ng=g[cur]+cost
            if ng<g.get(nb,1e9):
                g[nb]=ng; came[nb]=cur
                heapq.heappush(openh,(ng+abs(tk[0]-nb[0])+abs(tk[1]-nb[1]),nb))
    return None

def add_track(a,c,code):
    if math.hypot(c[0]-a[0],c[1]-a[1])<0.06: return
    t=pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(FM(a[0]),FM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(FM(c[0]),FM(c[1])))
    t.SetWidth(FM(TW)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(code); b.Add(t)

jumpers=[]

def find_blocking(path,code):
    """Return (point, direction) of first other-net track crossing along path."""
    for a,c in zip(path,path[1:]):
        n=max(1,int(math.hypot(c[0]-a[0],c[1]-a[1])/0.08))
        for i in range(n+1):
            f=i/n; x=a[0]+(c[0]-a[0])*f; y=a[1]+(c[1]-a[1])*f
            k=kv(x,y)
            for t,x0,y0,x1,y1 in track_occ.get(k,[]):
                if t.GetNetCode()==code: continue
                # point-to-segment distance
                dx,dy=x1-x0,y1-y0; L2=dx*dx+dy*dy
                if L2==0: continue
                tt=max(0,min(1,((x-x0)*dx+(y-y0)*dy)/L2))
                px,py=x0+dx*tt,y0+dy*tt
                if math.hypot(x-px,y-py)<0.45:
                    d=math.hypot(dx,dy)
                    return (px,py),(dx/d,dy/d)
    return None

def place_jumper(pos,tdir,net,label):
    fp=pcbnew.FootprintLoad(FP_LIB,FP_NAME)
    fp.SetReference(label); fp.SetValue('0R')
    fp.SetPosition(pcbnew.VECTOR2I(FM(pos[0]),FM(pos[1])))
    # pads along local X; want long axis PERPENDICULAR to trace direction
    ang=math.degrees(math.atan2(tdir[1],tdir[0]))+90
    fp.SetOrientationDegrees(ang)
    # hide reference/value text (avoid silk clutter)
    for txt in (fp.Reference(),fp.Value()):
        txt.SetVisible(False)
    b.Add(fp)
    for p in fp.Pads(): p.SetNet(net)
    ps=sorted(fp.Pads(),key=lambda p:p.GetPosition().x)
    p1=(MM(ps[0].GetPosition().x),MM(ps[0].GetPosition().y))
    p2=(MM(ps[1].GetPosition().x),MM(ps[1].GetPosition().y))
    return p1,p2

def route_seg(A,B,code,net,label,depth=0):
    if depth>8: return False
    p=astar(A,B,code,soft=False)
    if p:
        # add simplified track
        out=[p[0]]
        for i in range(1,len(p)-1):
            if (p[i][0]-p[i-1][0],p[i][1]-p[i-1][1])!=(p[i+1][0]-p[i][0],p[i+1][1]-p[i][1]):
                out.append(p[i])
        out.append(p[-1])
        for x,y in zip(out,out[1:]): add_track(x,y,code)
        return True
    sp=astar(A,B,code,soft=True)
    if not sp: return False
    blk=find_blocking(sp,code)
    if not blk: return False
    pos,tdir=blk
    p1,p2=place_jumper(pos,tdir,net,label)
    jumpers.append((label,code,pos))
    return route_seg(A,p1,code,net,label+'a',depth+1) and route_seg(p2,B,code,net,label+'b',depth+1)

for idx,u in enumerate(drc['unconnected_items']):
    its=u.get('items',[])
    if len(its)<2: continue
    ao,co=by_uuid.get(its[0].get('uuid')),by_uuid.get(its[1].get('uuid'))
    if not ao or not co: continue
    pa=ao.GetStart() if hasattr(ao,'GetStart') else ao.GetPosition()
    pc=co.GetStart() if hasattr(co,'GetStart') else co.GetPosition()
    A=(MM(pa.x),MM(pa.y)); C=(MM(pc.x),MM(pc.y))
    m=re.search(r'\[(/[^\]]+)\]',its[0].get('description',''))
    if not m: continue
    net=b.FindNet(m.group(1)); code=net.GetNetCode()
    ok=route_seg(A,C,code,net,f'JMP{idx+1:02d}')
    print(f"#{idx+1:2d} {m.group(1):18s} {'OK' if ok else 'FAILED'}",flush=True)

print("jumpers:",len(jumpers),flush=True)
json.dump(jumpers,open(os.path.join(ROOT,'tools','audit','jumpers_v2.json'),'w'),indent=1)
pcbnew.SaveBoard(PCB,b)
print("saved",PCB,flush=True)
