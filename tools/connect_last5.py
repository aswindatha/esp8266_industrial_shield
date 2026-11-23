"""Attempt genuine copper connections for the last 5 open nets on 1-layer board."""
import pcbnew, os, json, math, heapq, re, subprocess
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,'1layer_prototype','ind_8ch_motor_ctrl.kicad_pcb')
MM=pcbnew.ToMM; FM=pcbnew.FromMM
STEP=0.15; GRID=int(100/STEP)+3; CLR=0.30; TW=0.25
def kv(x,y): return (int(round(x/STEP)),int(round(y/STEP)))
b=pcbnew.LoadBoard(PCB)
occ={}
def mark(cx,cy,r,code):
    for gx in range(int((cx-r)/STEP),int((cx+r)/STEP)+1):
        for gy in range(int((cy-r)/STEP),int((cy+r)/STEP)+1):
            x,y=gx*STEP,gy*STEP
            if (x-cx)**2+(y-cy)**2<=r*r:
                k=(gx,gy)
                if code==-2 or k not in occ: occ[k]=code
def rebuild():
    occ.clear()
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
        if cur==tk:
            path=[cur]
            while cur in came: cur=came[cur]; path.append(cur)
            path.reverse(); return path
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nb=(cur[0]+dx,cur[1]+dy)
            if nb[0]<1 or nb[1]<1 or nb[0]>=GRID or nb[1]>=GRID: continue
            if not ok(nb) and nb!=tk: continue
            ng=g[cur]+1
            if ng<g.get(nb,1e9):
                g[nb]=ng; came[nb]=cur
                heapq.heappush(o,(ng+abs(tk[0]-nb[0])+abs(tk[1]-nb[1]),nb))
    return None
def emit(path,code):
    pts=[(gx*STEP,gy*STEP) for gx,gy in path]
    out=[pts[0]]
    for i in range(1,len(pts)-1):
        if (pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1])!=(pts[i+1][0]-pts[i][0],pts[i+1][1]-pts[i][1]): out.append(pts[i])
    out.append(pts[-1])
    added=[]
    for a,c in zip(out,out[1:]):
        if math.hypot(c[0]-a[0],c[1]-a[1])<0.05: continue
        t=pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(FM(a[0]),FM(a[1])))
        t.SetEnd(pcbnew.VECTOR2I(FM(c[0]),FM(c[1])))
        t.SetWidth(FM(TW)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(code)
        b.Add(t); added.append(t)
    return added

subprocess.run(['kicad-cli','pcb','drc','--format','json','--output','/tmp/b5.json',PCB],capture_output=True)
d=json.load(open('/tmp/b5.json'))
by_uuid={}
for t in b.GetTracks(): by_uuid[str(t.m_Uuid.AsString())]=t
for f in b.GetFootprints():
    for p in f.Pads(): by_uuid[str(p.m_Uuid.AsString())]=p
print("open:",len(d['unconnected_items']))
for u in d['unconnected_items']:
    its=u['items']
    if any('Zone' in i.get('description','') for i in its):
        print("SKIP zone island"); continue
    pts=[]; nm=''
    for it in its:
        obj=by_uuid.get(it.get('uuid'))
        if obj is None: pts=None; break
        q=obj.GetStart() if hasattr(obj,'GetStart') else obj.GetPosition()
        pts.append((MM(q.x),MM(q.y)))
        m=re.search(r'\[(/[^\]]+)\]',it.get('description',''))
        if m: nm=m.group(1)
    if not pts or len(pts)!=2: continue
    code=b.FindNet(nm).GetNetCode()
    rebuild()
    path=astar(pts[0],pts[1],code)
    if path:
        added=emit(path,code)
        print(f"ROUTED {nm} {len(added)} segs",flush=True)
    else:
        print(f"BLOCKED {nm}",flush=True)
pcbnew.SaveBoard(PCB,b)
print("saved")
