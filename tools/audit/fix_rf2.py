"""Phase 7 minimal, DRC-clean RF fix: remove plane copper under ESP32 antenna."""
import pcbnew, os
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PCB=os.path.join(ROOT,"ind_8ch_motor_ctrl.kicad_pcb")
MM=pcbnew.FromMM
b=pcbnew.LoadBoard(PCB)

# remove any earlier keepout (from the reverted attempt)
for z in list(b.Zones()):
    if z.GetIsRuleArea():
        b.RemoveNative(z)

z=pcbnew.ZONE(b)
z.SetIsRuleArea(True)
z.SetLayerSet(pcbnew.LSET.AllCuMask())
z.SetZoneName("ESP32_ANTENNA_KEEPOUT")
z.SetDoNotAllowZoneFills(True)
# tracks/vias/pads remain allowed so existing legal routing is untouched
z.SetDoNotAllowTracks(False)
z.SetDoNotAllowVias(False)
z.SetDoNotAllowPads(False)
poly=z.Outline(); poly.NewOutline()
for x,y in [(55.0,0.0),(73.0,0.0),(73.0,14.8),(55.0,14.8)]:
    poly.Append(MM(x),MM(y))
b.Add(z)
print("added zone-only antenna keepout")

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(PCB,b)
print("saved")
