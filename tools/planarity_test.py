"""Test if the single-layer board's nets are routable on BARE F.Cu
(all tracks removed, only pads as obstacles). If most fail, the topology is
fundamentally non-planar with current pin assignments -> must reassign pins.
"""
import pcbnew, os, math, heapq, re
from collections import defaultdict

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,'ind_8ch_motor_ctrl_SINGLELAYER_WIP.kicad_pcb')
MM=pcbnew.ToMM; FM=pcbnew.FromMM
STEP=0.25; GRID=int(100/STEP)+3; CLR=0.27

b=pcbnew.LoadBoard(PCB)
for t in list(b.GetTracks()): b.RemoveNative(t)   # strip ALL routing
for z in list(b.Zones()): b.RemoveNative(z)       # strip zones too (bare copper test)

# collect pads per net
netpads=defaultdict(list)
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetNetCode()>0 and not p.GetNetname().startswith('unconnected'):
            netpads[p.GetNetCode()].append(p)

# occupancy from pads only
occ={}
def mark_circle(cx,cy,r,code):
    for gx in range(int((cx-r)/STEP),int((cx+r)/STEP)+1):
        for gy in range(int((cy-r)/STEP),int((cy+r)/STEP)+1):
            x,y=gx*STEP,gy*STEP
            if (x-cx)**2+(y-cy)**2<=r*r:
                k=(gx,gy)
                if k not in occ: occ[k]=code
for f in b.GetFootprints():
    for p in f.Pads():
        pos=p.GetPosition(); sz=p.GetSize()
        if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH: continue
        r=max(MM(sz.x),MM(sz.y))/2+CLR
        mark_circle(MM(pos.x),MM(pos.y),r,p.GetNetCode())

def kv(x,y): return (int(x/STEP),int(y/STEP))
def astar(s,t,code):
    sk,tk=kv(s[0],s[1]),kv(t[0],t[1])
    openh=[(0.0,sk)]; came={}; g={sk:0.0}
    def ok(k):
        v=occ.get(k,0); return v==0 or v==code
    while openh:
        f,cur=heapq.heappop(openh)
        if cur==tk:
            return True
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            nb=(cur[0]+dx,cur[1]+dy)
            if nb[0]<1 or nb[1]<1 or nb[0]>=GRID or nb[1]>=GRID: continue
            if not ok(nb) and nb!=tk: continue
            ng=g[cur]+(1 if dx==0 or dy==0 else 1.414)
            if ng<g.get(nb,1e9):
                g[nb]=ng; came[nb]=cur
                heapq.heappush(openh,(ng+math.hypot(tk[0]-nb[0],tk[1]-nb[1]),nb))
    return False

okc=0; fail=0; skipped=0
for nc,pads in netpads.items():
    if len(pads)<2: skipped+=1; continue
    nm=pads[0].GetNetname()
    if len(pads)==2:
        a,c=pads[0].GetPosition(),pads[1].GetPosition()
        r=astar((MM(a.x),MM(a.y)),(MM(c.x),MM(c.y)),nc)
        if r: okc+=1
        else:
            fail+=1
            print(f"FAIL {nm:16s} {MM(a.x):5.1f},{MM(a.y):5.1f} -> {MM(c.x):5.1f},{MM(c.y):5.1f}")
    else:
        skipped+=1
print(f"\nBARE-FCU: routable={okc} failed={fail} skipped(multi/none)={skipped}")
