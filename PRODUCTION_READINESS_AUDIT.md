# Production Readiness Audit — `ind_8ch_motor_ctrl`

**Audit date:** 2026-11-22  
**Auditor:** Principal Hardware & PCB Design Verification Engineer (independent, zero-assumption)  
**Toolchain:** KiCad 10.0.8 (`pcbnew`, `kicad-cli`), ngspice-46 (KiCad-bundled DLL), Python 3.10/3.11, Freerouting 2.5.0  
**Artifacts:** `tools/audit/*.json`, `tools/audit/*_out.txt`, `tools/audit/*.cir`

> This audit did **not** rely on `README.md` or prior reports. Every result below was
> re-derived from the files on disk.

---

## 1. Executive verdict

| Scope | Verdict | Rationale |
|---|---|---|
| **Bare-board fabrication** | **GO** | DRC: 0 unconnected, 0 clearance/short/courtyard/hole/silk violations. Gerber/drill/BOM/POS cross-verified. 0.2 mm laser drills require an advanced-capability fab. |
| **PCBA assembly** | **CONDITIONAL GO** | All parts placeable; POS/BOM exact. 4 references are on `F.Fab` only (no silk). Five redundant 0 Ω links may be DNP'd. |
| **Firmware production / first-article bring-up** | **NO-GO as designed** | `IO0` (ESP32 pin 25) is **unconnected and not exposed on any connector**, and `EN` is not exposed either — there is no hardware path to enter UART download mode after assembly. |
| **RF / WiFi performance** | **CONDITIONAL** | A zone-only antenna keepout was added (removing ~364 mm² of plane copper). One 22.5 mm `UART_TX` trace still crosses the antenna volume; RF tuning/validation is required before release. |

**Overall: not a clean production sign-off** until the two Major findings (M-01 IO0 boot access, M-02 residual antenna trace) are dispositioned.

---

## 2. Scorecard

| Domain | Result | Evidence |
|---|---|---|
| Schematic ERC | **PASS** — 0 violations, 0 unconnected | `tools/audit/erc_audit.json` (exit 0) |
| PCB DRC | **PASS (electrical/mechanical)** — 0 unconnected; 5 library-link warnings only | `tools/audit/drc_after_rf2.json` |
| Schematic↔PCB parity | **EXPECTED GAP** — 5 missing legacy connectors, 6 PCB-only parts | `tools/audit/drc_parity_audit.json` |
| Netlist topology | **PASS** — 164/164 checks | `tools/audit/phase3_out.txt` |
| SPICE simulation | **PASS (with documented macromodel limits)** | `tools/audit/sim*_out.txt` |
| Mechanical / DFM | **PASS with advisories** | `tools/audit/phase5_out.txt` |
| Copper pours | **PASS** — filled, 0 starved thermals; ground split into 2 regions (advisory) | `tools/audit/phase5_out.txt` |
| Gerber / drill | **PASS** — 9 layers, 100.0×100.0 mm, min feature 0.2624 mm, PTH/NPTH separated | `tools/audit/phase6*_out.txt` |
| BOM / POS / IPC-D-356 | **PASS** — 46 parts + 4 MH; 50/50 POS rows match to <0.01 mm | `tools/audit/phase6b_final.txt` |
| RF keepout | **FIXED (partial)** — plane copper removed; trace residual | `tools/audit/rf_keepout.py`, `fix_rf2.py` |

---

## 3. Phase-by-phase evidence

### Phase 1 — Workspace / build integrity
- `ind_8ch_motor_ctrl.kicad_pcb`: 729 148 B, sha256 `48C7C0B36262BBEC…`, saved 2026-11-22 22:13:00.
- `ind_8ch_motor_ctrl.kicad_sch`: 239 795 B, sha256 `99E68DA7286744B9…`, 2026-11-15.
- `ind_8ch_motor_ctrl.kicad_pro`: 16 922 B, sha256 `2145D3C42696ACAB…`, 2026-11-15.
- All `fab/` artifacts timestamped **after** the final PCB save (22:13:36–22:14:28) — regenerated after the RF fix.
- Script audit: `build_v2.py` net map is explicit and correct; `finalize.py` imports SES (overwrites routing by design) and adds two zones; `cleanup*.py` only moves silk/mounting holes; `make_bom.py` reads the final board. No silent net overrides found. **Note:** `cleanup3.py` performs a raw text replacement of the FPID — verified the resulting file parses and DRC-passes.

### Phase 2 — ERC / DRC / parity
- ERC exit 0: **0 violations, 0 unconnected**.
- DRC: **0 unconnected**, 5 warnings, all library-link:
  - `U_MCU1` footprint differs from library copy (board copy omits the library's large antenna-courtyard graphic — this omission is what allowed the RF intrusion below).
  - `MH1`–`MH4`: FPID `MountingHole:MountingHole_3.2mm` not in installed library (actual name `…_3.2mm_M3`).
- Ignored DRC checks: `missing_courtyard`, `track_not_centered_on_via`, `tuning_profile_track_geometries`, `footprint_filters_mismatch`, `footprint_type_mismatch` — **no electrical check disabled**.
- Parity: `missing_footprint` ×5 (J_PWR1, J_MOT1, J_SENS1, J_I2C1, J_PROG1); `extra_footprint` ×6 (J_IN, J_OUT, MH1–MH4). This is the expected consequence of the requested connector consolidation.

### Phase 3 — Electrical topology (164/164 PASS)
- **Power entry:** D1 anode→`12V_RAW`, cathode→`12V_PROT`; TVS cathode→`12V_PROT`, anode→`GND`; C_BULK1 +→`12V_PROT`, −→`GND`. Verified.
- **Buck:** U_BUCK1 pins 1/2/3/4/5-8 = `12V_PROT`/`SW_BUCK`/`5V_RAIL`/`GND`/`GND`. D2 cathode→`SW_BUCK`, anode→`GND`; L1 between `SW_BUCK` and `5V_RAIL`. Verified. **Datasheet check:** XL1509 pin 4 `~EN` is active-low ("drive low to turn on") — tying it to GND is **correct**.
- **LDO:** U_LDO1 1=`GND`, 2+tab=`3V3_RAIL`, 3=`5V_RAIL`. Verified.
- **ESP32:** all 27 checked pins match the WROOM-32E pinout; R19 10 k + C4 10 µF on EN; R13/R14 4.7 k I²C pull-ups; R15–R18 4.7 k sensor collector pull-ups (incl. input-only IO34/IO35). Verified.
- **Motor stage:** all 8 channels verified end-to-end (opto → ULN input → ULN sink → J_OUT). LED current 6.36 mA. ULN2803A internal 2.7 k series + 7.2 k/3 k base-emitter pull-downs confirmed by datasheet — no external pull-downs required.
- **Sensor stage:** all 4 channels verified; IF 4.91 mA @12 V, resistor dissipation 53 mW (safe).
- **Calculations:** τ(EN) = 100 ms (simulated 103 ms); TVS VRWM 15 V vs 14.4 V rail = 0.6 V (4.2 %) margin; ampacity 0.2624 mm → 0.91 A @10 °C, 0.35 mm → 1.12 A @10 °C.

### Phase 4 — SPICE (ngspice-46, headless via `ngspice.dll`)
- SIM1 power-up/load step: 12 V up in 1.2 ms; 5 V regulates to 4.998 V with ~3 mV droop under 0.4 A step; 3.3 V to 3.214 V with 86 mV droop (simplified averaged macromodel — absolute droop is model-dependent).
- SIM2 reset: EN crosses VIH (2.475 V) at **143 ms**, 90 % at 233 ms; measured τ 103 ms. Comfortably meets ESP32 reset timing.
- SIM3 motor: active-low LED drive confirmed (IF ≈ 6.8 mA → ULN saturates, `V(mot)`≈0 V); clamp holds switching peak at **12.7 V**. (Behavioral model shows a numerical undershoot artifact at switching edges — not a physical prediction.)
- SIM4 sensor sweep 0–24 V: logic threshold at **V_sens ≈ 2.2 V** (collector <1.65 V); IF 4.98 mA @12 V, 10.42 mA @24 V; collector saturates at 0.198 V.

### Phase 5 — Physical / DFM
- Edge.Cuts: 4 closed segments, exactly 100.0×100.0 mm (Gerber confirms 100.000 mm span).
- TB courtyards extend y −1.33…101.95 (≈1.3 mm top / 1.95 mm bottom overhang) — acceptable for edge-mounted terminal blocks, check enclosure.
- Mounting-hole copper clearance: 3.99 / 4.24 / 4.43 / 12.78 mm — ample. No courtyard defined on MH footprints (ignored check).
- Zones: F.Cu `12V_PROT` 3 polygons (main 5683 mm² + 2 islands 185.6/148.3); B.Cu `GND` 2 polygons (5269 + 1101.4 mm²). No starved thermals (DRC clean). Ground is split into two regions — advisory for return paths.
- 4 references (`C3`, `C_BULK1`, `C_BULK2`, `D_TVS1`) sit on `F.Fab`, not `F.SilkS` (moved by `cleanup.py` to clear silk violations) — assembly advisory.
- R_J1–R_J5: both pads on the **same net** (`3V3_RAIL`×2, `GND`×2, `12V_PROT`×1) — electrically redundant in a 2-layer board; can be DNP.

### Phase 6 — Fab package
- Gerber job: 9 files (Cu×2, Mask×2, Silk×2, Paste×2, Profile×1), X2 attributes present.
- Edge.Cuts Gerber: 100.000 × 100.000 mm.
- Drills: T1 0.20 mm (12 × PTH, ESP32 thermal pad), T2 0.30 mm (83 × via), T3 1.60 mm (40 × PTH, terminal-block pins), T4 3.20 mm (4 × **NPTH**, mounting holes). PTH/NPTH correctly separated.
- Min Gerber aperture 0.2624 mm — above standard 0.15 mm/6 mil capability.
- POS: 50 rows, **0 mismatches** (X, mirrored Y, rotation) vs PCB; all `top`.
- BOM: 46 rows = 46 non-MH footprints, exact set match.
- IPC-D-356: 352-line netlist present.

---

## 4. Critical & Major findings

### C-01 (CRITICAL, electrical/production) — No firmware download-mode access
- `U_MCU1` pad 25 (`IO0`) net = `unconnected-(U_MCU1-IO0-Pad25)`; pad 3 (`EN`/`MCU_EN`) is only on R19/C4, not on `J_IN` or `J_OUT`.
- No DTR/RTS circuit exists; only `UART_TX`/`UART_RX` are exposed (`J_IN.11/12`).
- **Consequence:** after assembly there is no way to hold IO0 low during reset to enter the ESP32 ROM download mode. Firmware can only be pre-flashed before reflow or the board must be modified.
- **Fix (next revision):** expose IO0 and EN on two spare `J_IN` positions (e.g., pins 13/14) with a 10 k pull-up on IO0, or add an auto-reset DTR/RTS transistor circuit.

### M-02 (MAJOR, RF/EMC) — Antenna copper (partially fixed)
- **Before fix (measured):** F.Cu 12V_PROT fill **98.11 mm²** and B.Cu GND fill **266.40 mm²** inside x55–73/y0–15.44; `UART_TX` **22.49 mm** of 0.35 mm trace at y≈3.34.
- **Fix applied:** zone-only keepout rule area `ESP32_ANTENNA_KEEPOUT` (x55–73, y0–14.8, all Cu) — removes plane copper; DRC returned to 5 benign warnings. **Post-fix measured: F.Cu plane 98.11 → 0.00 mm²; B.Cu plane 266.40 → 10.80 mm²** (`tools/audit/rf_area_fast.py`).
- **Residual:** the `UART_TX` trace (22.49 mm) still crosses the antenna volume. Full resolution requires re-autorouting that net below the keepout (the manual attempt collided with existing GND/3V3 routing) or relocating the module.
- **Action:** RF tune/validate (antenna efficiency, Wi-Fi RSSI) before production release.

### M-03 (MAJOR, design margin) — Opto CTR margin for ULN input drive
- LED IF = 6.36 mA; ULN2803 input current at 12 V ≈ (12−1.4)/2.7 k = 3.9 mA; required opto CTR ≈ 62 %.
- LTV-827S minimum CTR is typically 50 % at IF=5 mA → worst-case drive margin is insufficient.
- **Fix:** reduce R1–R8 from 330 Ω to 220 Ω (IF ≈ 9.5 mA) or select an LTV-827S CTR rank with ≥100 % minimum.

---

## 5. Minor / advisory
1. Schematic/PCB parity gap — 5 legacy connectors + 6 PCB-only parts; sync schematic if your flow checks parity.
2. Five 0 Ω jumpers R_J1–R_J5 are redundant (both pads same net) — DNP to save assembly cost.
3. Four references on `F.Fab` only — add to `F.SilkS` in a clearance-checked revision.
4. `U_MCU1` library mismatch (missing antenna courtyard graphic) — update footprint from library.
5. MH FPID legacy name — update to `MountingHole_3.2mm_M3`.
6. 0.20 mm drills (ESP32 thermal pad) — confirm fab supports ≤0.20 mm laser drilling.
7. Ground plane split into two B.Cu regions (1101 mm² secondary) — check return paths under the buck.
8. TVS standoff margin only 0.6 V at 14.4 V rail — consider SMBJ18A for harsh 12 V environments.
9. Sensor resistor dissipation 236 mW at 24 V continuous vs 250 mW 1206 rating — marginal; rate for 0.25 W or add series resistance.
10. Channel GPIO mapping is crossed (R1: M4_GPIO→M1_LED, R2: M1_GPIO→M2_LED, …) — firmware must map accordingly.
11. TB bodies overhang board edges by ~1.3/1.9 mm — verify enclosure clearance.

---

## 6. Fab-house order parameters

| Parameter | Value |
|---|---|
| Board size | 100.0 × 100.0 mm |
| Layers | 2 (F.Cu / B.Cu) |
| Material | FR-4, Tg≥130 °C |
| Finished thickness | 1.6 mm |
| Copper weight | 1 oz (35 µm) both layers |
| Surface finish | ENIG or HASL (specify) |
| Solder mask | Green, both sides |
| Silkscreen | White, top |
| Min trace / clearance | 0.2624 mm / 0.25 mm |
| Min drill | 0.20 mm (12 ×), 0.30 mm (83 ×), 1.60 mm (40 ×) |
| NPTH | 4 × 3.20 mm (mounting holes) |
| Copper-to-edge | 0.30 mm |
| Stackup | F.Cu / dielectric / B.Cu, symmetric |

**Upload ZIP checklist (`fab/`):** `ind_8ch_motor_ctrl-{F_Cu.gtl,B_Cu.gbl,F_Mask.gts,B_Mask.gbs,F_SilkS.gto,B_SilkS.gbo,F_Paste.gtp,B_Paste.gbp,Edge_Cuts.gm1,job.gbrjob}`, `ind_8ch_motor_ctrl.drl`, `BOM.csv`, `BOM_grouped.csv`, `pos.csv`, `netlist.ipc356`, `assembly_top.pdf`, `top.svg`.

---

## 7. Sign-off
Bare-board fabrication is **approved**. Production release is **held** pending disposition of C-01 (IO0 access) and M-02 (RF validation), and acknowledgement of M-03 (CTR margin).
