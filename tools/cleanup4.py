import pcbnew, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, "ind_8ch_motor_ctrl.kicad_pcb")
MM = pcbnew.FromMM
b = pcbnew.LoadBoard(PCB)
for t in b.GetDrawings():
    if isinstance(t, pcbnew.PCB_TEXT) and t.GetText() == "NC":
        p = t.GetPosition()
        if abs(pcbnew.ToMM(p.y) - 88.0) < 0.5 and pcbnew.ToMM(p.x) < 50:
            t.SetPosition(pcbnew.VECTOR2I(p.x, MM(85.5)))
            print("moved NC label to 85.5")
pcbnew.SaveBoard(PCB, b)
