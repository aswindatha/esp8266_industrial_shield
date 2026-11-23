"""Global single-layer router with rip-up-and-reroute.

Starts from the single-layer WIP board (good 5.00mm terminal blocks), strips all
routing, then routes every net on F.Cu using A* with negotiated congestion:
when a net fails, conflicting nets are ripped up and re-routed on later passes.
Finally adds an F.Cu GND zone and saves for DRC verification.
"""
import pcbnew, os, math, heapq, random, sys, time
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, 'ind_8ch_motor_ctrl_SINGLELAYER_WIP.kicad_pcb')
OUT = os.path.join(ROOT, 'ind_8ch_motor_ctrl.kicad_pcb')
MM = pcbnew.ToMM; FM = pcbnew.FromMM
STEP = 0.25
CLR = 0.27                       # copper clearance to other nets
TRACK_W = 0.30
KEEPOUT = TRACK_W/2 + CLR        # 0.42
GRID = int(100/STEP) + 3

def kv(x,y): return (int(round(x/STEP)), int(round(y/STEP)))

b = pcbnew.LoadBoard(PCB)
for t in list(b.GetTracks()): b.RemoveNative(t)
for z in list(b.Zones()): b.RemoveNative(z)

# nets to route (pads)
netpads = defaultdict(list)
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetNetCode() > 0 and not p.GetNetname().startswith('unconnected'):
            netpads[p.GetNetCode()].append(p)

# pad center positions
padpos = {}
for f in b.GetFootprints():
    for p in f.Pads():
        q = p.GetPosition()
        padpos[(p.GetNetCode(), p.GetNumber(), f.GetReference())] = (MM(q.x), MM(q.y))

# ---------- geometry helpers ----------
def pad_keepouts():
    """Return dict of (gx,gy) -> netcode for pad keepouts."""
    d = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH: continue
            pos = p.GetPosition(); sz = p.GetSize()
            r = max(MM(sz.x), MM(sz.y))/2 + CLR
            cx, cy = MM(pos.x), MM(pos.y)
            for gx in range(int((cx-r)/STEP), int((cx+r)/STEP)+1):
                for gy in range(int((cy-r)/STEP), int((cy+r)/STEP)+1):
                    x, y = gx*STEP, gy*STEP
                    if (x-cx)**2 + (y-cy)**2 <= r*r:
                        d[(gx,gy)] = p.GetNetCode()
    return d

PAD_OCC = pad_keepouts()

def track_keepouts(tracks):
    d = {}
    for t in tracks:
        s,e = t.GetStart(), t.GetEnd()
        x0,y0,x1,y1 = MM(s.x),MM(s.y),MM(e.x),MM(e.y)
        n = max(1, int(math.hypot(x1-x0,y1-y0)/(STEP*0.4)))
        for i in range(n+1):
            f = i/n
            cx,cy = x0+(x1-x0)*f, y0+(y1-y0)*f
            for gx in range(int((cx-KEEPOUT)/STEP), int((cx+KEEPOUT)/STEP)+1):
                for gy in range(int((cy-KEEPOUT)/STEP), int((cy+KEEPOUT)/STEP)+1):
                    x,y = gx*STEP,gy*STEP
                    if (x-cx)**2+(y-cy)**2 <= KEEPOUT**2:
                        d[(gx,gy)] = t.GetNetCode()
    return d

# ---------- A* ----------
def astar(s, t, code, occ):
    sk, tk = kv(*s), kv(*t)
    def ok(k):
        v = occ.get(k, 0)
        return v == 0 or v == code
    openh = [(0.0, sk)]; came = {}; g = {sk: 0.0}
    while openh:
        _, cur = heapq.heappop(openh)
        if cur == tk:
            path = [cur]
            while cur in came: cur = came[cur]; path.append(cur)
            path.reverse()
            return [(gx*STEP, gy*STEP) for gx,gy in path]
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            nb = (cur[0]+dx, cur[1]+dy)
            if nb[0]<1 or nb[1]<1 or nb[0]>=GRID or nb[1]>=GRID: continue
            if not ok(nb) and nb != tk: continue
            ng = g[cur] + (1 if dx==0 or dy==0 else 1.4142)
            if ng < g.get(nb, 1e9):
                g[nb]=ng; came[nb]=cur
                heapq.heappush(openh, (ng+math.hypot(tk[0]-nb[0],tk[1]-nb[1]), nb))
    return None

def simplify(points):
    if len(points) < 3: return points
    pts = [points[0]]
    for i in range(1, len(points)-1):
        p0,p1,p2 = points[i-1],points[i],points[i+1]
        v1=(p1[0]-p0[0],p1[1]-p0[1]); v2=(p2[0]-p1[0],p2[1]-p1[1])
        if abs(v1[0]*v2[1]-v1[1]*v2[0]) > 1e-6: pts.append(p1)
    pts.append(points[-1])
    return pts

def make_tracks(points, code):
    segs = []
    for a,c in zip(simplify(points), simplify(points)[1:]):
        if math.hypot(c[0]-a[0], c[1]-a[1]) < 0.05: continue
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(FM(a[0]), FM(a[1])))
        t.SetEnd(pcbnew.VECTOR2I(FM(c[0]), FM(c[1])))
        t.SetWidth(FM(TRACK_W)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(code)
        b.Add(t); segs.append(t)
    return segs

# ---------- global routing ----------
# Sort nets: multi-pin power first (as trunks), then 2-pin by length.
net_items = []
for nc, pads in netpads.items():
    if len(pads) < 2: continue
    nm = pads[0].GetNetname()
    pts = [padpos[(nc, p.GetNumber(), p.GetParentFootprint().GetReference())] for p in pads]
    # length estimate (min spanning-ish)
    length = sum(math.hypot(pts[i][0]-pts[0][0], pts[i][1]-pts[0][1]) for i in range(1,len(pts)))
    net_items.append((nc, nm, pts, length))

# route order: small pin-count first, then by length ascending
net_items.sort(key=lambda x: (len(x[2]), x[3]))

routes = {}          # netcode -> list of track objects
failed = set()

def build_occ(exclude_nets=()):
    d = dict(PAD_OCC)
    alltracks = [t for nc, trs in routes.items() if nc not in exclude_nets for t in trs]
    to = track_keepouts(alltracks)
    for k,v in to.items(): d[k] = v
    return d

def route_net(nc, nm, pts, occ):
    """Build a tree connecting all pts. Returns list of tracks or None."""
    segs = []
    connected = [pts[0]]
    remaining = pts[1:]
    while remaining:
        best = None
        for k,cand in enumerate(remaining):
            # try connect cand to each connected point, pick shortest path
            for src in connected:
                p = astar(src, cand, nc, occ)
                if p is not None:
                    L = len(p)
                    if best is None or L < best[0]:
                        best = (L, k, p, src)
        if best is None:
            return None
        _, k, p, src = best
        segs.extend(make_tracks(p, nc))
        connected.append(remaining.pop(k))
        # update occ with new tracks
        to = track_keepouts(segs)
        for key,val in to.items():
            if val == nc: occ[key] = val
    return segs

print(f"Routing {len(net_items)} nets (bare copper, global A*)...")
t0=time.time()
for nc, nm, pts, length in net_items:
    occ = build_occ()
    trs = route_net(nc, nm, pts, occ)
    if trs:
        routes[nc] = trs
    else:
        failed.add(nc)
        print(f"  FAIL {nm:18s} pins={len(pts)}")

print(f"pass1: routed {len(net_items)-len(failed)}/{len(net_items)} in {time.time()-t0:.1f}s")

# rip-up-and-reroute passes
for rnd in range(6):
    if not failed: break
    print(f"ripup pass {rnd+1}, failed={len(failed)}")
    order = list(failed)
    random.shuffle(order)
    made_progress = False
    for nc in order:
        nm = next(x[1] for x in net_items if x[0]==nc)
        pts = next(x[2] for x in net_items if x[0]==nc)
        # rip up all currently routed nets (keep only this net's pads)
        old = dict(routes)
        for k in list(routes):
            for t in routes[k]: b.RemoveNative(t)
        routes.clear()
        # re-route all nets except current one, then current one last
        others = [x for x in net_items if x[0]!=nc]
        others.sort(key=lambda x: (len(x[2]), x[3]))
        ok_all = True
        for nc2,nm2,pts2,_ in others:
            occ = build_occ()
            trs = route_net(nc2,nm2,pts2,occ)
            if trs: routes[nc2]=trs
            else: ok_all=False; break
        if ok_all:
            occ = build_occ()
            trs = route_net(nc,nm,pts,occ)
            if trs:
                routes[nc]=trs
                failed.discard(nc)
                made_progress=True
                print(f"  recovered {nm}")
                continue
        # restore old routing if this attempt failed
        for k in list(routes):
            for t in routes[k]: b.RemoveNative(t)
        routes.clear(); routes.update(old)
    if not made_progress:
        print("  no progress, stopping")
        break

print(f"FINAL: routed {len(net_items)-len(failed)}/{len(net_items)}, failed={len(failed)}")
for nc in failed:
    print("  STILL FAILED:", next(x[1] for x in net_items if x[0]==nc))

# Add F.Cu GND zone
gn = b.FindNet('/GND')
if gn:
    z = pcbnew.ZONE(b)
    z.SetLayer(pcbnew.F_Cu); z.SetNet(gn)
    z.SetLocalClearance(FM(0.30))
    poly = z.Outline()
    poly.NewOutline()
    for x,y in [(0.5,0.5),(99.5,0.5),(99.5,99.5),(0.5,99.5)]:
        poly.Append(FM(x),FM(y))
    b.Add(z)
    print("added GND zone")

pcbnew.FillZones(b.Zones(), b.GetConnectivity(), True)
pcbnew.SaveBoard(OUT, b)
print("saved", OUT)
