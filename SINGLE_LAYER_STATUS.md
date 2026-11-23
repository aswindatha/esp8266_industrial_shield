# Single-Layer Conversion — Status & Plan

**Date:** 2026-11-23  
**2-layer design:** preserved in `ind_8ch_motor_ctrl_2LAYER_backup.zip` and `backup_2layer/`  
**Working board:** `ind_8ch_motor_ctrl.kicad_pcb` — now **single-layer** (F.Cu only)

---

## 1. What was completed

| Item | Result |
|---|---|
| 2-layer backup + ZIP | `ind_8ch_motor_ctrl_2LAYER_backup.zip` (522 KB) — PCB, schematic, project, fab/, README, audit report |
| Copper layers | **F.Cu only** — no B.Cu tracks, **0 vias**, GND zone on F.Cu |
| Terminal blocks | Replaced 5.08 mm CUI (103.25 mm body, 1.3–1.9 mm overhang) with **5.00 mm Altech AK100 20-position** — body 101.05 mm, **0.53 mm overhang per end**, pin pitch exactly 5.00 mm, pin span 95 mm |
| Board outline | 100.0 × 100.0 mm, unchanged |
| Component placement | Re-planned 4 times; final layout has **zero courtyard overlaps, shorts or clearance errors** |
| Routing | Freerouting 2.5.0, single-layer mode (`--router.layers.routable=true,false`), 513 tracks |
| Fabrication outputs | `fab_singlelayer/` (Gerbers F.Cu/Mask/Silk/Paste/Edge.Cuts, drills, POS, BOM) |

## 2. Honest status: **NOT fabrication-ready**

The single-layer autorouter resolved **136 of 154** connections. **18 unrouted connections remain** (down from 71 in the original single-layer attempt, but not zero):

| # | Net | Endpoints |
|---|---|---|
| 1–2 | `/3V3_RAIL` | local track-to-track gaps |
| 3–5 | `/GND` | mostly resolved by the F.Cu GND zone; residual islands |
| 6–9 | `/M3_DRV`, `/M5_DRV`, `/M6_DRV`, `/M7_DRV` | optocoupler (U2/U3/U4, x70) → ULN2803 inputs (x82) |
| 10–11 | `/I2C_SCL`, `/I2C_SDA` | pull-ups → ESP32 pins 36/33 |
| 12–13 | `/UART_TX`, `/UART_RX` | J_IN pins 11/12 → ESP32 pins 35/34 |
| 14–16 | `/SENS1_COL`, `/SENS3_COL`, `/SENS4_COL` | sensor optocouplers/pull-ups → ESP32 pins 8/6/7 |
| 17 | `/M1_GPIO` | ESP32 pin 13 → R2 |
| 18 | `/SENS2_A` | R10 → U5 pin 3 |

Remaining DRC: 18 unconnected + 4 benign library warnings + 10 cosmetic silk/mask warnings. No shorts or clearance errors.

## 3. Why it cannot be finished automatically

I attempted to resolve the remaining crossings with 0 Ω jumpers (1206 and 0402), tested three placement algorithms:
- midpoint placement → landed on existing traces (shorts),
- free-space grid search → jumper-to-jumper and footprint collisions,
- exact-rectangle search along each blocked path → only 5 of 19 could be legally placed.

The topology is fundamentally non-planar: the ESP32 has used pins on **both** sides of the module, while J_IN (all inputs) is on the left edge and the motor chain runs left-to-right. On one copper layer this requires roughly 15–20 physical wire bridges at specific crossing points, which must be placed by a designer with full visibility of the routing — not reliably by automation.

## 4. Recommended path to completion (choose one)

**Option A — finish single-layer with jumpers (recommended if single-layer is mandatory):**
1. For each of the 18 connections above, identify the blocking trace.
2. Place a 0 Ω 1206 jumper perpendicular to that trace with its pads on opposite sides (physically bridging over it).
3. Re-run Freerouting on F.Cu only; repeat until 0 unrouted.
4. Re-run DRC, regenerate Gerbers/drill/POS/BOM.
5. Accept ~15–20 extra BOM lines and manual jumper installation.

**Option B — change the architecture:**
- Move MCU strapping/I²C/UART sensor signals to a small mezzanine or use an ESP32 module with castellated pins on one side only; or
- Relax to 2 copper layers (the preserved backup is fully routed, DRC-clean and fab-ready).

**Option C — accept 2-layer with single-sided assembly:** If "single layer" meant *components on one side* rather than *one copper layer*, the backed-up 2-layer design already satisfies that and is production-ready.

## 5. Files

- `ind_8ch_motor_ctrl.kicad_pcb` — current single-layer WIP board
- `fab_singlelayer/` — WIP fabrication outputs (do **not** order until 0 unrouted)
- `tools/place_single*.py`, `tools/build_single_layer.py`, `tools/add_jumpers*.py` — conversion experiments
- `tools/audit/drc_single_final.json`, `drc_single_zone2.json` — evidence
- `ind_8ch_motor_ctrl_2LAYER_backup.zip` — restore point (fully routed 2-layer)

---

**Verdict:** single-layer conversion is structurally complete and electrically clean, but **18 connections still require manual jumpers** before fabrication. The 2-layer backup remains the production-ready design.
