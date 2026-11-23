import pcbnew, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b = pcbnew.LoadBoard(os.path.join(ROOT, "ind_8ch_motor_ctrl.kicad_pcb"))
out = os.path.join(ROOT, "tools", "board.dsn")
ok = pcbnew.ExportSpecctraDSN(b, out)
print("ExportSpecctraDSN:", ok, out, os.path.getsize(out) if os.path.exists(out) else "MISSING")
