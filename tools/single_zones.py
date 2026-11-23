"""Add F.Cu GND plane to single-layer board and refill."""
import pcbnew, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,"ind_8ch_motor_ctrl.kicad_pcb")
MM=pcbnew.FromMM
b=pcbnew.LoadBoard(PCB)
for z in list(b.Zones()): b.RemoveNative(z)
z=pcbnew.ZONE(b); z.SetLayer(pcbnew.F_Cu); z.SetNet(b.FindNet("/GND"))
z.SetZoneName("GND_SINGLE"); z.SetLocalClearance(MM(0.30))
z.SetThermalReliefGap(MM(0.30)); z.SetThermalReliefSpokeWidth(MM(0.45))
z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL); z.SetMinThickness(MM(0.20))
poly=z.Outline(); poly.NewOutline()
for x,y in [(0.6,0.6),(99.4,0.6),(99.4,99.4),(0.6,99.4)]: poly.Append(MM(x),MM(y))
b.Add(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB,b)
print("GND zone added and filled")
