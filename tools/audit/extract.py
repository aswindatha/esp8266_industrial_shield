"""Extract complete PCB netlist + geometry into JSON for independent analysis."""
import pcbnew, os, json
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
b = pcbnew.LoadBoard(os.path.join(ROOT, "ind_8ch_motor_ctrl.kicad_pcb"))
mm = pcbnew.ToMM

def pt(v): return [round(mm(v.x), 4), round(mm(v.y), 4)]

out = {"footprints": [], "pads": [], "tracks": [], "vias": [], "zones": []}
for fp in b.GetFootprints():
    out["footprints"].append({
        "ref": fp.GetReference(), "value": fp.GetValue(),
        "fpid": fp.GetFPIDAsString(), "pos": pt(fp.GetPosition()),
        "rot": fp.GetOrientationDegrees(), "layer": b.GetLayerName(fp.GetLayer()),
    })
    for p in fp.Pads():
        out["pads"].append({
            "ref": fp.GetReference(), "pad": p.GetNumber(),
            "net": p.GetNetname(), "pos": pt(p.GetPosition()),
            "size": [round(mm(p.GetSize().x), 4), round(mm(p.GetSize().y), 4)],
            "drill": round(mm(p.GetDrillSize().x), 4) if p.GetDrillSize().x else 0,
            "layer_set": p.GetLayerSet().FmtHex(),
            "attr": str(p.GetAttribute()), "shape": str(p.GetShape()),
        })
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        out["vias"].append({"net": t.GetNetname(), "pos": pt(t.GetPosition()),
                            "width": round(mm(t.GetWidth(pcbnew.F_Cu)),4),
                            "drill": round(mm(t.GetDrillValue()),4)})
    else:
        out["tracks"].append({"net": t.GetNetname(), "layer": b.GetLayerName(t.GetLayer()),
                              "start": pt(t.GetStart()), "end": pt(t.GetEnd()),
                              "width": round(mm(t.GetWidth()),4),
                              "len": round(mm(t.GetLength()),4)})
for z in b.Zones():
    out["zones"].append({"name": z.GetZoneName(), "net": z.GetNetname(),
                         "layer": b.GetLayerName(z.GetLayer()),
                         "filled": z.IsFilled(),
                         "outline": [pt(z.Outline().COutline(0).CPoint(i)) for i in range(z.Outline().COutline(0).PointCount())]})

path = os.path.join(ROOT, "tools", "audit", "netlist_geom.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1)
print("footprints", len(out["footprints"]), "pads", len(out["pads"]),
      "tracks", len(out["tracks"]), "vias", len(out["vias"]), "zones", len(out["zones"]))
print("saved", path)
