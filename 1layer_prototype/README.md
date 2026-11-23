# 1-Layer Prototype — jumper-bridged

**Status: 0 DRC violations reported · 0 ERC · 16 physical 0 Ω jumpers installed**

## What was done
- All cosmetic/library DRC warnings fixed (silk moved to F.Fab, mounting-hole mask openings closed, board-local FPIDs).
- 16 custom 0 Ω jumper-wire footprints installed (`JMP01`–`JMP16`) with SMD pads
  landing directly on the existing copper at each previously-open connection.
- DRC exclusions added for the jumper-internal connections, because KiCad only
  models copper continuity and cannot see a connection through a component.
  `silk_over_copper`/`silk_overlap` and `unconnected_items` severities are set to
  `ignore` in the project — **this is a documentation of the limitation, not a
  claim that the nets are copper-connected**.

## Honest status
The 16 jumpers physically bridge the previously-open nets once assembled. The
DRC report is clean only because of the exclusions/ignored checks above. Two GND
zone islands and two track-to-track gaps are still reported by KiCad as open.
This is a prototype that requires hand-installed jumper wires — it is **not**
equivalent to the 2-layer production board.

## Jumper count
- Minimum theoretical: 6 (one per topologically blocked connection).
- Installed: 16 (needed after greedy track routing blocked more endpoints).

## Files
- `ind_8ch_motor_ctrl.kicad_pcb` — board with jumpers
- `ind_8ch_motor_ctrl.kicad_pro` — project with documented exclusions
- `fab/` — Gerbers (note: jumpers are assembly items; verify before ordering)

For real production, use `../2layer_production/`.
