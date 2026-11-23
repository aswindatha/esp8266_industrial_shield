"""Analyze the single-layer board: build an F.Cu occupancy grid and try to
A* route each DRC-unconnected connection without crossing other nets.

This is an ANALYSIS tool - it does not modify the board.
"""
import pcbnew, os, json, math, heapq, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, "ind_8ch_motor_ctrl.kicad_pcb")
MM = pcbnew.ToMM
FROMMM = pcbnew.FromMM

STEP = 0.25            # grid resolution (mm)
TRACK_CLR = 0.42       # keepout radius around other-net tracks (half width + clearance ~0.42)
PAD_CLR = 0.30         # extra clearance around other-net pads
GRID = int(100.0 / STEP) + 2

def key(x, y):
    return (int(x / STEP), int(y / STEP))

b = pcbnew.LoadBoard(PCB)

# Map UUID -> board item for tracks/pads
items_by_uuid = {}
for t in b.GetTracks():
    items_by_uuid[str(t.m_Uuid.AsString())] = t
for f in b.GetFootprints():
    for p in f.Pads():
        items_by_uuid[str(p.m_Uuid.AsString())] = p

# occupancy: cell -> netcode occupying it (first wins); -2 = hole/blocked
occ = {}

def mark_circle(cx, cy, r, netcode):
    gx0, gy0 = int((cx - r) / STEP), int((cy - r) / STEP)
    gx1, gy1 = int((cx + r) / STEP), int((cy + r) / STEP)
    for gx in range(gx0, gx1 + 1):
        for gy in range(gy0, gy1 + 1):
            x, y = gx * STEP, gy * STEP
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                k = (gx, gy)
                if netcode == -2:
                    occ[k] = -2
                elif k not in occ:
                    occ[k] = netcode

def mark_seg(x0, y0, x1, y1, r, netcode):
    d = math.hypot(x1 - x0, y1 - y0)
    n = max(1, int(d / (STEP * 0.5)))
    for i in range(n + 1):
        f = i / n
        mark_circle(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, r, netcode)

# Tracks
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        mark_circle(MM(p.x), MM(p.y), MM(t.GetWidth(pcbnew.F_Cu)) / 2 + TRACK_CLR, t.GetNetCode())
    else:
        s, e = t.GetStart(), t.GetEnd()
        mark_seg(MM(s.x), MM(s.y), MM(e.x), MM(e.y), MM(t.GetWidth()) / 2 + TRACK_CLR, t.GetNetCode())

# Pads (rect approx by circle of half-diagonal)
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            pos = p.GetPosition()
            mark_circle(MM(pos.x), MM(pos.y), MM(p.GetSize().x) / 2 + 0.3, -2)
            continue
        pos = p.GetPosition()
        sz = p.GetSize()
        r = max(MM(sz.x), MM(sz.y)) / 2 + PAD_CLR
        mark_circle(MM(pos.x), MM(pos.y), r, p.GetNetCode())

# Mounting holes (courtyard/hole keepout) - holes are NPTH pads already handled.

def endpoint(u):
    """Return (x,y,netcode,label) for the item in a DRC unconnected entry."""
    uid = u.get('uuid')
    it = items_by_uuid.get(uid)
    d = u.get('description', '')
    if it is not None:
        pos = it.GetPosition()
        if hasattr(it, 'GetStart'):
            # use start of track
            pos = it.GetStart()
        return MM(pos.x), MM(pos.y), it.GetNetCode(), d
    pos = u.get('pos', {})
    return pos.get('x', 0), pos.get('y', 0), -1, d

drc = json.load(open('/tmp/drc_current.json'))
unconn = drc['unconnected_items']

def astar(sx, sy, tx, ty, netcode):
    """A* on grid; free if cell unoccupied or occupied by same netcode.
       Returns list of (x,y) waypoints or None."""
    s = key(sx, sy); t = key(tx, ty)
    def passable(k):
        v = occ.get(k, 0)
        return v == 0 or v == netcode
    # allow start/end even if slightly occupied by same net
    openh = [(0, s)]
    came = {}
    g = {s: 0.0}
    while openh:
        f, cur = heapq.heappop(openh)
        if cur == t:
            path = [cur]
            while cur in came:
                cur = came[cur]
                path.append(cur)
            path.reverse()
            return [(gx * STEP, gy * STEP) for gx, gy in path]
        cg = g[cur]
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            nb = (cur[0]+dx, cur[1]+dy)
            if nb[0] < 1 or nb[1] < 1 or nb[0] >= GRID or nb[1] >= GRID:
                continue
            if not passable(nb) and nb != t:
                continue
            ng = cg + (1 if dx==0 or dy==0 else 1.4142)
            if ng < g.get(nb, 1e9):
                g[nb] = ng; came[nb] = cur
                h = math.hypot(t[0]-nb[0], t[1]-nb[1])
                heapq.heappush(openh, (ng+h, nb))
    return None

print("Analyzing", len(unconn), "unconnected items...")
results=[]
for i, u in enumerate(unconn):
    its = u.get('items', [])
    if len(its) < 2:
        continue
    # parse net code from description
    import re
    m = re.search(r'\[(/[^\]]+)\]', its[0].get('description',''))
    netname = m.group(1) if m else ''
    netcode = b.FindNet(netname).GetNetCode() if netname else -1
    a = endpoint(its[0]); c = endpoint(its[1])
    # try both endpoints as start/target
    p = astar(a[0], a[1], c[0], c[1], netcode)
    status = "CLEAR" if p else "BLOCKED"
    results.append((i+1, netname, status, (a[0],a[1]), (c[0],c[1])))
    print(f"{i+1:2d} {status:7s} {netname:18s} ({a[0]:6.2f},{a[1]:6.2f}) -> ({c[0]:6.2f},{c[1]:6.2f})" +
          (f"  waypoints={len(p)}" if p else ""))
json.dump(results, open(os.path.join(ROOT,'tools','audit','route_analysis.json'),'w'), indent=1)
