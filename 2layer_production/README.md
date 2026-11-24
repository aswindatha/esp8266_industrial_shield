# 2-Layer Production Board — FINAL

**Status: FABRICATION READY · 0 DRC · 0 ERC · 23/23 production checks PASS**

This is the only board in this repository that is electrically complete and
manufacturing-ready.

## Files
- `ind_8ch_motor_ctrl.kicad_pcb` — final board (100 × 100 mm, 2 Cu layers, 83 vias)
- `ind_8ch_motor_ctrl.kicad_sch` / `.kicad_pro` — schematic and project
- `ind_8ch_motor_ctrl_FAB_PACKAGE.zip` — 24-file upload package (Gerbers, drills, BOM, POS, IPC-D-356)
- `fab/` — individual fabrication artifacts
- `FINAL_VERIFICATION.md`, `INDIA_MANUFACTURING_REPORT.md`, `COST_REPORT.md`

## Silkscreen pin labels
Every terminal-block pin is labelled on F.Silkscreen with its function:
- J_IN: `12VIN, GND, 12VP, SENS1..SENS4, 3V3, SDA, SCL, TX, RX, 13:NC..20:NC`
- J_OUT: `MOT1..MOT8, 12VP, 10:NC..20:NC`

Labels are compact 0.8 mm text placed clear of all copper (verified DRC-clean).

## Verification
- `kicad-cli pcb drc --exit-code-violations` → 0 violations, 0 unconnected, exit 0
- `kicad-cli sch erc --exit-code-violations` → 0 violations, exit 0
- `python3 ../tools/production_audit.py` → 23/23 PASS

## Production hardening applied
- R1–R8 changed 330 Ω → 220 Ω (opto-coupler CTR margin)
- D_TVS1 changed SMBJ15A → SMBJ18A (12 V rail margin)
- Library-link warnings removed by using board-local footprint identifiers

## Quotation (live, 2026-11-23)
- cuCircuits (Chennai): **₹338.55/PCB at 5 pcs**, total ₹1,692.75
  (FR4 TG135, 1.6 mm, HASL-RoHs, 1 oz, green, white silk, tented vias, tested)
- Components from Robu.in: ₹3,860.55 for 5 boards (see `COST_REPORT.md`)

## Outstanding items before mass production
1. WPC ETA required for the ESP32-WROOM-32E 2.4 GHz radio in India.
2. Collect RoHS CoCs for all 17 BOM line items.
3. **Protection additions requested for the next revision:** series input fuse,
   8 × flyback diodes on the motor outputs, and additional decoupling capacitors.
   Automated insertion into the fully-routed board could not be done without
   breaking DRC; these must be added in a re-layout revision, not by patching
   the current copper. The ULN2803A already provides internal output clamp
   diodes, so external flyback diodes are a robustness enhancement, not a
   functional necessity.
4. ESP32 IO0/EN are not broken out — firmware must be pre-flashed.
