# 1-Layer Prototype — WORK IN PROGRESS (NOT FABRICATION READY)

**Status: 18 unconnected connections · NOT PRODUCTION READY · DO NOT ORDER**

This folder preserves the single-layer conversion experiment. It is supplied
for study and for a future re-layout; it is **not** a manufacturable board.

## Files
- `ind_8ch_motor_ctrl.kicad_pcb` — single-layer board (F.Cu only, 0 vias)
- `ind_8ch_motor_ctrl.kicad_sch` / `.kicad_pro` — schematic and project
- `fab/` — partial fabrication outputs (do not use)
- `SINGLE_LAYER_FINAL.md` — full technical explanation

## Current state
- DRC: **18 unconnected items** + library/silk warnings
- ERC: 0 violations
- Routing: 513 F.Cu tracks, 0 vias, single GND zone on F.Cu

## Why it cannot be finished as-is
The netlist requires ~14 physical crossings on one copper layer. The clearest
case is I²C/UART: `J_IN` orders the pins SDA–SCL–TX–RX top-to-bottom while the
ESP32 right-edge pads are ordered SCL–TX–RX–SDA. On one copper layer that
permutation cannot be routed without crossings.

KiCad DRC only recognises copper continuity. A 0 Ω jumper straddling a crossing
is electrically correct once assembled, but DRC always reports its two pads as
unconnected. Net-tie attributes do not change this without an F.Cu copper
bridge, which would short the crossed trace.

## Attempts already made (all failed to reach 0/0)
| Method | Result |
|---|---|
| Global Manhattan PathFinder router | plateaued at ~29 shared cells |
| Aggressive randomised negotiation | best 10 shared cells, never 0 |
| 8-directional PathFinder | converged but produced 956 DRC violations |
| 0 Ω jumper insertion (2 algorithms) | 629–1389 DRC violations |

## Path to a real single-layer board
1. Reassign connector pinouts so pin order matches destination order.
2. Reposition components to make the net graph planar.
3. Re-route from scratch with a stronger router (Freerouting needs Java 25;
   only Java 17 is installed here).
4. Where crossings remain, use 0 Ω jumpers and accept DRC exclusions for the
   jumper-internal connections (physically correct, but KiCad cannot model it).

Until those steps are completed, use the 2-layer board in `../2layer_production/`.
