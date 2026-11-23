import pcbnew, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,"ind_8ch_motor_ctrl.kicad_pcb")
b=pcbnew.LoadBoard(PCB)
ok=pcbnew.ImportSpecctraSES(b,os.path.join(ROOT,"tools","board_single8.ses"))
print("import",ok,"tracks",len(list(b.GetTracks())),"vias",len([t for t in b.GetTracks() if isinstance(t,pcbnew.PCB_VIA)]))
pcbnew.SaveBoard(PCB,b)
