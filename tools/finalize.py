"""Import routed session, add power/ground copper planes, refill, save."""
import pcbnew, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, "ind_8ch_motor_ctrl.kicad_pcb")
SES = os.path.join(ROOT, "tools", "board_route.ses")
MM = pcbnew.FromMM

b = pcbnew.LoadBoard(PCB)
print("tracks before SES:", len(list(b.GetTracks())))
ok = pcbnew.ImportSpecctraSES(b, SES)
print("SES import:", ok, "tracks:", len(list(b.GetTracks())),
      "vias:", len([t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]))

# ---- remove stale drawings outside the board --------------------------
for d in list(b.GetDrawings()):
    p = d.GetPosition()
    x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
    if x < -1 or x > 101 or y < -1 or y > 101:
        b.RemoveNative(d)


def add_zone(name, netname, layer, clearance, thermal_gap, spoke, min_thick):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(b.FindNet(netname))
    z.SetZoneName(name)
    z.SetLocalClearance(MM(clearance))
    z.SetThermalReliefGap(MM(thermal_gap))
    z.SetThermalReliefSpokeWidth(MM(spoke))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetMinThickness(MM(min_thick))
    try:
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    except Exception:
        pass
    poly = z.Outline()
    poly.NewOutline()
    for x, y in [(0.6, 0.6), (99.4, 0.6), (99.4, 99.4), (0.6, 99.4)]:
        poly.Append(MM(x), MM(y))
    b.Add(z)
    return z


# B.Cu: solid GND return plane
add_zone("GND_RETURN_BOTTOM", "/GND", pcbnew.B_Cu, 0.30, 0.30, 0.50, 0.20)
print("added B.Cu GND plane")

# F.Cu: 12V_PROT power plane (widens all motor-supply current paths)
add_zone("MOTOR_12V_POWER_TOP", "/12V_PROT", pcbnew.F_Cu, 0.30, 0.30, 0.50, 0.25)
print("added F.Cu 12V_PROT power plane")

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
print("zones filled")

pcbnew.SaveBoard(PCB, b)
print("saved", PCB)
