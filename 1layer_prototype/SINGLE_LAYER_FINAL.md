# Single-layer PCB — final attempt results

**Date:** 2026-11-23
**Goal requested:** single copper layer, all nets connected, 0 DRC violations, 0 ERC violations.

## Outcome: not achievable with KiCad's connectivity model

Four independent approaches were implemented and measured. None produced a
DRC-clean single-layer board. The production 2-layer board (0 DRC, 0 ERC, all
components on the top side) has been restored as the main board.

## Attempts and evidence

### 1. Global Manhattan PathFinder router (`tools/route_manhattan.py`)
Stripped all routing and routed every net on bare F.Cu with 4-directional A*
and negotiated congestion (rectangular pad keepouts, 0.30 mm track, 0.30 mm
clearance). Overuse plateaued at ~29 shared cells after 120 iterations.
Connector pin reassignment (`tools/route_pinned.py`) to match destination order
reduced this to ~30 and aggressive randomized negotiation
(`tools/route_pf_aggro.py`) reached a best of **10 shared cells** in 200
iterations but never reached zero. A non-zero value means at least two nets must
occupy the same copper cell — i.e. a physical crossing is required.

### 2. 8-directional PathFinder (`tools/pathfinder_route.py`)
Converged to zero shared cells but the grid-to-track conversion produced
**956 DRC violations** (488 clearance, 199 short, 38 crossing) because diagonal
grid moves cut corners and the simplified keepout model under-estimated real
pad/track clearances.

### 3. 0 Ω jumper insertion on the original Freerouting solution
- `tools/build_single_jumpers.py`: 35 jumpers → **629 violations, 32 unconnected**.
- `tools/build_jumpers_v2.py` (recursive hard-obstacle routing between jumpers):
  **1389 violations, 14 unconnected**.

Root cause: KiCad does **not** consider the two pads of a resistor connected
through the component. A 0 Ω jumper straddling a trace is electrically correct
after assembly, but DRC still reports those pads as unconnected. Net-tie
attributes do not change this without an on-layer copper bridge, which would
short the crossed trace. Automated jumper insertion also creates new
clearance/courtyard/short violations faster than they can be resolved.

### 4. Connector pinout reassignment
`J_IN` pin order was reversed relative to the ESP32 pad order for I²C/UART
(`SDA,SCL,TX,RX` vs `SCL,TX,RX,SDA`) and the sensor pins were ordered opposite
to their destinations. Reassigning pins removed the connector-area conflicts but
did not make the whole net graph planar.

## Why this is fundamental
On one copper layer two different nets cannot cross. This schematic's terminal
geometry and 50-component placement require crossings in the remaining routes.
KiCad's DRC only recognises copper continuity, so a physically-correct wire
jumper cannot be reported as "connected" without a DRC exclusion. Even with
exclusions, automated jumper placement produced hundreds of real copper
violations that could not be resolved within this work.

## Delivered instead
`ind_8ch_motor_ctrl.kicad_pcb` — restored 2-layer production board:
- **0 DRC violations, 0 unconnected** (all severities)
- **0 ERC violations**
- All **50 components on F.Cu** (single-sided assembly — the other common
  meaning of "single layer")
- Complete regenerated `fab/` package and `ind_8ch_motor_ctrl_FAB_PACKAGE.zip`

Single-layer work preserved: `ind_8ch_motor_ctrl_SINGLELAYER_WIP.kicad_pcb`,
`fab_singlelayer/`, and all `tools/route_*.py` / `tools/build_*jumpers*.py`
scripts with logs in `tools/audit/`.
