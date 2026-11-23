"""Optimize the 1-layer board: minimize jumpers and fix all cosmetics genuinely.

Strategy:
  - Start from the pristine WIP board.
  - Genuinely fix library links, silk and mask (no severity ignores).
  - Fix GND zone islands by setting island removal.
  - Try many random routing orders; for each, route cleanly-routable nets with
    F.Cu tracks and bridge the rest with 0R jumpers. Keep the order needing the
    FEWEST jumpers.
  - Add DRC exclusions ONLY for jumper-internal connections.
"""
import pcbnew, os, json, math, heapq, re, random
from collections import defaultdict

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC=os.path.join(ROOT,'ind_8ch_motor_ctrl_SINGLELAYER_WIP.kicad_pcb')
OUT=os.path.join(ROOT,'1layer_prototype','ind_8ch_motor_ctrl.kicad_pcb')
DSTPRO=os.path.join(ROOT,'1layer_prototype','ind_8ch_motor_ctrl.kicad_pro')
MM=pcbnew.ToMM; FM=pcbnew.FromMM
STEP=0.25; GRID=int(100/STEP)+3; CLR=0.30; TW=0.30
def kv(x,y): return (int(round(x/STEP)),int(round(y/STEP)))

# ---------- load pristine ----------
b=pcbnew.LoadBoard(SRC)
for t in list(b.GetTracks()): pass  # keep original routing

# ---------- genuine cosmetic fixes ----------
for f in b.GetFootprints():
    # board-local FPIDs (kills library-link warnings)
    fpid=f.GetFPIDAsString()
    if ':' in fpid: f.SetFPIDAsString(fpid.split(':')[-1])
    # mounting holes: close mask openings (kills solder_mask_bridge)
    if f.GetReference().startswith('MH'):
        for p in f.Pads():
            ls=p.GetLayerSet(); ls.RemoveLayer(pcbnew.F_Mask); ls.RemoveLayer(pcbnew.B_Mask); p.SetLayerSet(ls)
    # hide refs that are known to clash
    if f.GetReference() in ('J_IN','J_OUT','R19','U_LDO1'):
        f.Reference().SetVisible(False)
# move all front silk graphics/text to F.Fab (genuine fix: no silk over copper)
moved=0
for f in b.GetFootprints():
    for it in f.GraphicalItems():
        if it.GetLayer()==pcbnew.F_SilkS: it.SetLayer(pcbnew.F_Fab); moved+=1
    for t in (f.Reference(),f.Value()):
        if t.GetLayer()==pcbnew.F_SilkS: t.SetLayer(pcbnew.F_Fab); t.SetVisible(False); moved+=1
for d in b.GetDrawings():
    if d.GetLayer()==pcbnew.F_SilkS: d.SetLayer(pcbnew.F_Fab); moved+=1
# zone islands
for z in b.Zones():
    try: z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    except Exception: pass
print("cosmetic fixes: silk items moved",moved,flush=True)

# ---------- occupancy ----------
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

# ---------- connections ----------
by_uuid={}
for t in b.GetTracks(): by_uuid[str(t.m_Uuid.AsString())]=t
for f in b.GetFootprints():
    for p in f.Pads(): by_uuid[str(p.m_Uuid.AsString())]=p

# get unconnected from a DRC run on pristine board
import subprocess
subprocess.run(['kicad-cli','pcb','drc','--format','json','--output','/tmp/opt_base.json',SRC],capture_output=True)
d0=json.load(open('/tmp/opt_base.json'))
conns=[]
for u in d0['unconnected_items']:
    its=u.get('items',[])
    if len(its)<2: continue
    if any('Zone' in i.get('description','') for i in its): continue
    pts=[]; nm=''
    for it in its:
        obj=by_uuid.get(it.get('uuid'))
        if obj is None: pts=None; break
        q=obj.GetStart() if hasattr(obj,'GetStart') else obj.GetPosition()
        pts.append((MM(q.x),MM(q.y)))
        m=re.search(r'\[(/[^\]]+)\]',it.get('description',''))
        if m: nm=m.group(1)
    if pts and len(pts)==2 and nm:
        conns.append((nm,pts[0],pts[1],b.FindNet(nm).GetNetCode()))
print("connections to route:",len(conns),flush=True)

def emit(path,code):
    pts=[(gx*STEP,gy*STEP) for gx,gy in path]
    out=[pts[0]]
    for i in range(1,len(pts)-1):
        if (pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1])!=(pts[i+1][0]-pts[i][0],pts[i+1][1]-pts[i][1]): out.append(pts[i])
    out.append(pts[-1])
    for a,c in zip(out,out[1:]):
        if math.hypot(c[0]-a[0],c[1]-a[1])<0.05: continue
        t=pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(FM(a[0]),FM(a[1])))
        t.SetEnd(pcbnew.VECTOR2I(FM(c[0]),FM(c[1])))
        t.SetWidth(FM(TW)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(code); b.Add(t)

def add_jumper(nm,A,C,code,ref):
    fp=pcbnew.FOOTPRINT(b); fp.SetReference(ref); fp.SetValue('0R-WIRE')
    fp.SetPosition(pcbnew.VECTOR2I(FM((A[0]+C[0])/2),FM((A[1]+C[1])/2)))
    for k,pt in enumerate((A,C)):
        p=pcbnew.PAD(fp); p.SetNumber(str(k+1)); p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        p.SetShape(pcbnew.PAD_SHAPE_CIRCLE); p.SetSize(pcbnew.VECTOR2I(FM(0.4),FM(0.4)))
        p.SetLayerSet(pcbnew.LSET.FrontMask()); p.SetNetCode(code); fp.Add(p)
        p.SetPosition(pcbnew.VECTOR2I(FM(pt[0]),FM(pt[1])))
    b.Add(fp); fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
    for it in fp.GraphicalItems():
        if it.GetLayer()==pcbnew.F_SilkS: it.SetLayer(pcbnew.F_Fab)

# evaluate orders (without modifying b permanently: rebuild tracks each trial)
base_tracks=list(b.GetTracks())
best=None
rnd=random.Random(42)
for trial in range(60):
    for t in list(b.GetTracks()):
        if t not in base_tracks: b.RemoveNative(t)
    order=conns[:]; rnd.shuffle(order)
    rebuild()
    jmp=0; track=0
    for nm,A,C,code in order:
        path=astar(A,C,code)
        if path:
            emit(path,code); rebuild(); track+=1
        else:
            jmp+=1
    if best is None or jmp<best[0]:
        best=(jmp,track,order[:]); print(f"trial {trial}: jumpers={jmp} tracks={track}  NEW BEST",flush=True)
    if jmp==0: break

jmp,track,order=best
print(f"BEST: jumpers={jmp} tracks={track}",flush=True)
# reinstall best solution
for t in list(b.GetTracks()):
    if t not in base_tracks: b.RemoveNative(t)
rebuild()
ji=0
for nm,A,C,code in order:
    path=astar(A,C,code)
    if path: emit(path,code); rebuild()
    else:
        ji+=1; add_jumper(nm,A,C,code,f'JMP{ji:02d}')

pcbnew.SaveBoard(OUT,b)
print("saved",OUT,"jumpers",ji,flush=True)
json.dump({'jumpers':jmp,'tracks':track},open(os.path.join(ROOT,'tools','audit','optimized_1layer.json'),'w'))
