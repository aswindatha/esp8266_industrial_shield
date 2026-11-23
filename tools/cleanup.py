"""Cosmetic/DRC cleanup after routing — no net connectivity changes."""
import pcbnew, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, "ind_8ch_motor_ctrl.kicad_pcb")
MM = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))
b = pcbnew.LoadBoard(PCB)

# 1) move mounting holes slightly outward from neighboring copper
for ref, x, y in [("MH1", 14.5, 5.0), ("MH3", 14.5, 95.0)]:
    b.FindFootprintByReference(ref).SetPosition(V(x, y))
    print("moved", ref)

# 2) NC labels: move inboard so they don't collide with TB silk
for t in b.GetDrawings():
    if isinstance(t, pcbnew.PCB_TEXT) and t.GetText() == "NC":
        p = t.GetPosition()
        newx = 11.5 if pcbnew.ToMM(p.x) < 50 else 88.5
        t.SetPosition(V(newx, pcbnew.ToMM(p.y)))
print("moved NC labels inboard")

# 3) move overhanging TB silkscreen graphics onto a documentation layer
for ref in ("J_IN", "J_OUT"):
    fp = b.FindFootprintByReference(ref)
    fields = {}
    for name in ("Reference", "Value"):
        fields[name] = fp.Reference() if name == "Reference" else fp.Value()
    moved = 0
    for item in list(fp.GraphicalItems()):
        if item.GetLayer() != pcbnew.F_SilkS:
            continue
        bb = item.GetBoundingBox()
        l, r = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight())
        t, bo = pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())
        if l < 0.6 or r > 99.4 or t < 0.6 or bo > 99.4:
            item.SetLayer(pcbnew.Cmts_User)
            moved += 1
    for name, txt in fields.items():
        if txt is None:
            continue
        txt.SetLayer(pcbnew.F_SilkS if name == "Reference" else pcbnew.F_Fab)
        txt.SetPosition(V(14.0, 50.0) if ref == "J_IN" else V(86.0, 50.0))
    print("cleaned silk on", ref, "- moved", moved, "items")

# 4) reposition specific reference fields that land on copper / other silk
repos = {
    "D_TVS1": (16.0, 12.0, True),
    "C_BULK1": (29.0, 5.5, True),
    "C_BULK2": (41.0, 23.5, True),
    "C3": (33.0, 33.0, True),
}
for ref, (x, y, to_fab) in repos.items():
    fp = b.FindFootprintByReference(ref)
    if fp:
        fld = fp.Reference()
        fld.SetPosition(V(x, y))
        if to_fab:
            fld.SetLayer(pcbnew.F_Fab)
        print("moved reference", ref)

pcbnew.SaveBoard(PCB, b)
print("saved")
