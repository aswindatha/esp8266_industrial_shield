"""Finalize single-layer board with physical 0R wire jumpers.

For every DRC-unconnected net, find a path between endpoints (pads hard, tracks
soft), place a 0603 0R jumper at each crossing of another net's track, and connect
the endpoint/jumper-pad sequence with F.Cu tracks. Jumper pads are both on the
routed net — KiCad reports them unconnected, which is handled by project-level
DRC exclusions (standard for single-layer jumper designs).
"""
import pcbnew, os, json, math, heapq
from collections import defaultdict

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,'ind_8ch_motor_ctrl.kicad_pcb')
MM=pcbnew.ToMM; FM=pcbnew.FromMM
STEP=0.25; GRID=int(100/STEP)+3
CLR=0.30; TW=0.30

b=pcbnew.LoadBoard(PCB)
drc=json.load(open('/tmp/drc_single_orig.json'))
by_uuid={}
for t in b.GetTracks(): by_uuid[str(t.m_Uuid.AsString())]=t
for f in b.GetFootprints():
    for p in f.Pads(): by_uuid[str(p.m_Uuid.AsString())]=p

def kv(x,y): return (int(round(x/STEP)),int(round(y/STEP)))

# occupancies
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
    n=max(1,int(math.hypot(x1-x0,y1-y0)/(STEP*0.4)))
    for i in range(n+1):
        f=i/n; cx,cy=x0+(x1-x0)*f,y0+(y1-y0)*f
        for gx in range(int((cx-CLR)/STEP),int((cx+CLR)/STEP)+1):
            for gy in range(int((cy-CLR)/STEP),int((cy+CLR)/STEP)+1):
                x,y=gx*STEP,gy*STEP
                if (x-cx)**2+(y-cy)**2<=CLR**2: track_occ.setdefault((gx,gy),set()).add(t.GetNetCode())

def astar_soft(s,t,code):
    """A* where other-net tracks are soft (cost 8), other-net pads hard."""
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
            cost=1.0+8.0*len(track_occ.get(nb,set())-{code})
            ng=g[cur]+cost
            if ng<g.get(nb,1e9):
                g[nb]=ng; came[nb]=cur
                heapq.heappush(openh,(ng+abs(tk[0]-nb[0])+abs(tk[1]-nb[1]),nb))
    return None

def simplify(pts):
    out=[pts[0]]
    for i in range(1,len(pts)-1):
        if (pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1])!=(pts[i+1][0]-pts[i][0],pts[i+1][1]-pts[i][1]):
            out.append(pts[i])
    out.append(pts[-1]); return out

def add_track(a,c,code):
    if math.hypot(c[0]-a[0],c[1]-a[1])<0.05: return
    t=pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(FM(a[0]),FM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(FM(c[0]),FM(c[1])))
    t.SetWidth(FM(TW)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(code); b.Add(t)

def crossing_points(path,code):
    """Find (position, direction) where path crosses other-net tracks."""
    out=[]
    for a,c in zip(path,path[1:]):
        # sample along segment
        n=max(1,int(math.hypot(c[0]-a[0],c[1]-a[1])/0.1))
        for i in range(n+1):
            f=i/n; x=a[0]+(c[0]-a[0])*f; y=a[1]+(c[1]-a[1])*f
            k=kv(x,y)
            others=track_occ.get(k,set())-{code}
            if others and (not out or math.hypot(x-out[-1][0][0],y-out[-1][0][1])>1.5):
                out.append(((x,y),(c[0]-a[0],c[1]-a[1])))
    return out

jumpers=[]
added=0
for idx,u in enumerate(drc['unconnected_items']):
    its=u.get('items',[])
    if len(its)<2: continue
    a,c=its[0],its[1]
    aobj=by_uuid.get(a.get('uuid')); cobj=by_uuid.get(c.get('uuid'))
    if not aobj or not cobj: continue
    pa,pc=aobj.GetPosition(),cobj.GetPosition()
    A=(MM(pa.x),MM(pa.y)); C=(MM(pc.x),MM(pc.y))
    m=__import__('re').search(r'\[(/[^\]]+)\]',a.get('description',''))
    if not m: continue
    net=b.FindNet(m.group(1))
    if not net: continue
    code=net.GetNetCode()
    path=astar_soft(A,C,code)
    if not path:
        print(f"#{idx+1} {m.group(1)}: NO PATH"); continue
    xs=crossing_points(path,code)
    print(f"#{idx+1} {m.group(1)}: {len(xs)} crossings")
    nodes=[A]+[p for p,_ in xs]+[C]
    fp=pcbnew.FootprintLoad('/usr/share/kicad/footprints/Resistor_SMD.pretty','R_0603_1608Metric')
    for j,(pos,d) in enumerate(xs):
        jfp=pcbnew.FootprintLoad('/usr/share/kicad/footprints/Resistor_SMD.pretty','R_0603_1608Metric')
        jfp.SetReference(f'JMP{idx+1:02d}_{j+1}'); jfp.SetValue('0R')
        # orient jumper perpendicular to crossing direction
        ang=math.degrees(math.atan2(d[1],d[0]))+90
        jfp.SetPosition(pcbnew.VECTOR2I(FM(pos[0]),FM(pos[1])))
        jfp.SetOrientationDegrees(ang)
        b.Add(jfp)
        for p in jfp.Pads(): p.SetNet(net)
        jumpers.append((idx+1,j+1,m.group(1),pos))
        # pad positions
        pads=list(jfp.Pads())
        pads.sort(key=lambda p:p.GetPosition().x)
        p1=(MM(pads[0].GetPosition().x),MM(pads[0].GetPosition().y))
        p2=(MM(pads[1].GetPosition().x),MM(pads[1].GetPosition().y))
        add_track(nodes[j],p1,code)
        nodes[j+1]=p2
    # final segment from last jumper pad2 to C
    add_track(nodes[-2],C,code)
    added+=len(xs)

print("jumpers placed:",len(jumpers),"tracks added:",added)
json.dump(jumpers,open(os.path.join(ROOT,'tools','audit','jumpers_final.json'),'w'),indent=1)
pcbnew.SaveBoard(PCB,b)
print("saved",PCB)
