import pcbnew, os, collections, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, "ind_8ch_motor_ctrl.kicad_pcb")
b = pcbnew.LoadBoard(PCB)

bb = b.GetBoardEdgesBoundingBox()
print("Outline: %.2f x %.2f mm" % (pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())))
print("Footprints:", len(list(b.GetFootprints())))
tracks = list(b.GetTracks())
segs = [t for t in tracks if not isinstance(t, pcbnew.PCB_VIA)]
vias = [t for t in tracks if isinstance(t, pcbnew.PCB_VIA)]
print("Tracks:", len(segs), "Vias:", len(vias))
print("Zones:", [(z.GetZoneName(), b.GetLayerName(z.GetLayer())) for z in b.Zones()])

conn = {}
for ref in ("J_IN", "J_OUT"):
    f = b.FindFootprintByReference(ref)
    conn[ref] = [(p.GetNumber(), p.GetNetname() or "NC") for p in sorted(f.Pads(), key=lambda p: int(p.GetNumber()))]
    used = [(n, net) for n, net in conn[ref] if net != ""]
    print(f"{ref}: {len(used)} connected / 20 positions; NC = {20-len(used)}")
    print("   ", ", ".join(f"{n}:{net.strip('/')}" for n, net in used))

# net connectivity sanity
netpads = collections.Counter()
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetNetname():
            netpads[p.GetNetname()] += 1
print("Nets with pads:", len(netpads))

print("Fab files:", len([f for f in os.listdir(os.path.join(ROOT, "fab"))]))
