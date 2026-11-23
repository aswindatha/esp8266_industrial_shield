# esp8266_industrial_shield

Industrial 8-channel motor controller (ESP32-WROOM-32E), 100 × 100 mm.

## Repository structure

| Path | What it is |
|---|---|
| **`2layer_production/`** | **FINAL, fabrication-ready board.** 0 DRC, 0 ERC, complete fab package and quotation. Use this. |
| **`1layer_prototype/`** | Single-layer conversion experiment. **Not fabrication-ready** (18 unconnected). Study only. |
| `tools/` | Routing, auditing and BOM scripts used to verify the boards. |
| `robu-search/` | Portable Robu.in part-search skill kit (installed into OpenCode). |

The root-level `ind_8ch_motor_ctrl.*` files are the working copy of the
2-layer production board (identical to `2layer_production/`).

## 2-layer production board — status

- **PCB DRC:** 0 violations, 0 unconnected (all severities)
- **ERC:** 0 violations
- **Production audit:** 23/23 checks PASS (`python3 tools/production_audit.py`)
- **Layers:** 2 Cu, 716 track segments, 83 vias, 50 components all on F.Cu
- **Min features:** 0.2624 mm track, 0.2516 mm clearance, 0.20 mm drill, 0.30 mm copper-to-edge
- **Fab package:** `2layer_production/ind_8ch_motor_ctrl_FAB_PACKAGE.zip` (24 files)

See `2layer_production/README.md` and `FINAL_VERIFICATION.md` for full evidence.

## Prototype quotation (5 boards, 2026-11-23)

| Item | ₹ |
|---|---:|
| PCB (cuCircuits, FR4 TG135, 1.6 mm, HASL-RoHs, tested) | 1,692.75 |
| Components (Robu.in, verified) | 3,860.55 |
| **Subtotal (excl. terminal blocks & shipping)** | **5,553.30** |

Source: `COST_REPORT.md`.

## Important limitations

- **Single-layer:** not achievable as a DRC-clean board with the current netlist
  and KiCad's copper-only connectivity model. Full analysis in
  `SINGLE_LAYER_FINAL.md` and `1layer_prototype/README.md`.
- **India compliance:** WPC ETA required for the ESP32 2.4 GHz radio; RoHS CoCs
  needed. See `INDIA_MANUFACTURING_REPORT.md`.
- **Firmware:** ESP32 IO0/EN are not broken out — pre-flash firmware.
- **Next revision:** add an input fuse, flyback diodes and extra decoupling
  capacitors via a proper re-layout (they could not be inserted into the
  finished copper without breaking DRC).

## Reproduce verification

```bash
kicad-cli pcb drc --exit-code-violations 2layer_production/ind_8ch_motor_ctrl.kicad_pcb
kicad-cli sch erc --exit-code-violations 2layer_production/ind_8ch_motor_ctrl.kicad_sch
python3 tools/production_audit.py
```
