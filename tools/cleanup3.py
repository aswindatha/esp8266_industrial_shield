"""Place mounting holes in verified free spots; revert FPID; nudge NC label."""
import pcbnew, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, "ind_8ch_motor_ctrl.kicad_pcb")
MM = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))
b = pcbnew.LoadBoard(PCB)

for ref, x, y in [("MH1", 15.5, 4.0), ("MH3", 14.0, 91.5)]:
    b.FindFootprintByReference(ref).SetPosition(V(x, y))
# nudge the one NC label that was near the old MH3 location
for t in b.GetDrawings():
    if isinstance(t, pcbnew.PCB_TEXT) and t.GetText() == "NC":
        p = t.GetPosition()
        if abs(pcbnew.ToMM(p.y) - 93.19) < 0.5:
            t.SetPosition(V(pcbnew.ToMM(p.x), 88.0))
print("mounting holes and NC label repositioned")
pcbnew.SaveBoard(PCB, b)

# revert FPID (board geometry matches the non-M3 library entry)
txt = open(PCB, encoding="utf-8").read()
txt = txt.replace('MountingHole:MountingHole_3.2mm_M3"', 'MountingHole:MountingHole_3.2mm"')
txt = txt.replace('"MountingHole_3.2mm_M3"', '"MountingHole_3.2mm"')
open(PCB, "w", encoding="utf-8").write(txt)
print("FPIDs reverted")
