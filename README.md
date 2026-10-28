# ESP8266 Industrial Shield — 8× Motor / 16× Isolated Input Controller

180 × 100 mm single-layer industrial controller. ESP-12F, 12 V input, 8 × 300 mA unidirectional motor channels, 16 × opto-isolated 12 V field inputs, ultrasonic port, I²C expanders.

> **Build status — read first.**
> The design, netlist, placement, jumper schedule and DFM automation are complete and validated in this repository.
> The **routed `.kicad_pcb` and `.kicad_sch` do not exist yet**, and KiCad is not installed in the environment that produced this pack.
> **11 of the 20 DFM checks are `PENDING`** and must be closed on a KiCad host before the board goes to fab. They are not passes — see [§6](#6-20-point-dfm--quality-sign-off).

---

## 1. System overview

```
    12 V ──► J1 ──► F1 PTC ──► D1 SMAJ15A ──► D2 SS54 ──► +12V ─┬──► ULN2803 COM ×2
    2P                                                           ├──► J3–J10 pin 1 (M+)
                                                                 └──► R29 0R ──► FLD_12V
                       ┌──────────────┴─────────────┐
                       │  XL1509-5.0  150 kHz       │  L1 33 µH, D3 SS34, C4 220 µF
                       └──────────────┬─────────────┘
                                      │ +5V ──┬──► U2 AMS1117-3.3 ──► +3V3 ──► ESP-12F U3
                                              ├──► J2 pin 1 (ultrasonic VCC)
                                              └──► U12 74AHC1G34 (TRIG buffer)

  U3 GPIO4/5 (SDA/SCL, 4.7 k) ◄──► U4 0x20 (motors) ──► U6/U7 ULN2803 ──► J3–J10
                             ◄──► U5 0x21 (inputs) ◄── U8–U11 PS2501-4 ◄── J11–J26
  U3 GPIO12 ──8 mm──► U12 ──► J2.2 TRIG        J2.3 ECHO ──1 k/2 k──► U3 GPIO14
```

**Ground topology — discrete split, single star:**

| Net | Members | Bridge |
|---|---|---|
| `GND` (logic) | U3, U4, U5, opto emitters, all logic decoupling, RN1–RN8 | — |
| `GND_FIELD` (power return) | J1.2, D1, D3, C1–C5, C15/C16, C19, U1 pins 5–8, U6/U7 pin 9 | **R31 0 Ω 1206 at (30, 24)** |

### Electrical ratings

| Parameter | Value |
|---|---|
| Input | 12 V DC nominal, 9–15 V operating, 2.8 A continuous / 3.7 A peak |
| Logic rails | +5 V @ 0.5 A, +3.3 V @ 0.36 A peak (ESP TX burst) |
| Motor outputs | 8 × low-side, 300 mA each, 2 Darlington channels paralleled per motor |
| Field inputs | 16 × 12 V sink, 9 mA per channel (1.2 k), active-low at the expander |
| Isolation | Functional barrier at the optocouplers; **galvanic only if R29 is removed and the field is fed separately** |

---

## 2. Manufacturing specification

| Item | Specification |
|---|---|
| Board | 180.0 × 100.0 mm, rectangular, 4 × M3 |
| Copper | **Single layer — routing on B.Cu only**; F.Cu carries pads, thermal pours and 0 Ω jumpers |
| Stackup | 1.6 mm FR-4 (CEM-1 acceptable for < 2 A trunks) / 1 oz (35 µm) |
| Finish / mask / silk | HASL-LF / green LPI both sides / white |
| Min track & space | 0.25 / 0.25 mm (I²C 0.30 / 0.254) |
| Vias | **0.8 mm pad / 0.3 mm drill** — 0.25 mm annular. 0.6/0.3 was rejected: it gives 0.15 mm |
| Holes | terminals 1.3 mm / 2.4 mm pad; M3 3.2 mm NPTH |
| Edge clearance | ≥ 0.5 mm copper-to-edge, ≥ 3.0 mm at terminal boundaries |
| Mask | 0.05 mm expansion, ≥ 0.10 mm web (0.57 mm achieved at 1.27 mm pitch) |
| Fiducials | 3 × 1.0 mm copper, 2.0 mm mask opening |
| Panel | 2-up, 5 mm rails, V-score or 3 mm mouse bites |

### Fixed features

| Feature | Geometry |
|---|---|
| Isolation moat | X 6–160, Y 71–73, 2.0 mm, **both copper layers**, flared at both ends |
| Field zone | Y 73–100 — **no copper pour**, ~90 % bare laminate |
| Antenna keep-out | X 78–98, Y −4…4, void on F.Cu / B.Cu / F.Mask / B.Mask |
| U6/U7 collector pours | 12 × 25 mm on F.Cu, **zero vias** |
| D2 pour | ≥ 150 mm² each pad + 8 × 0.3 mm vias |

---

## 3. Jumper schedule (52 × 0 Ω)

Single-layer routing forces every crossing onto F.Cu. Group A uses **1206** (power), the rest **0805** (signal). Full per-jumper register: [`tools/jumpers.csv`](tools/jumpers.csv).

| Refs | Group | Net(s) | Pkg | Coordinates (X,Y) mm |
|---|---|---|---|---|
| JMP1–JMP6 | A | `+12V` ×6 | 1206 | (104,18) (116,18) (128,18) (140,18) (152,18) (164,18) |
| JMP7–JMP10 | B | `GND_FIELD` ×4 | 0805 | (148,22.5) (154,22.5) (160,22.5) (166,22.5) |
| JMP11–JMP14 | C | `SDA`, `SCL`, `SDA`, `SCL` | 0805 | (122,50) (130,50) (138,50) (146,50) |
| JMP15–JMP26 | D | `OPT1_COL`…`OPT12_COL` | 0805 | (32,66) (42,66) (52,66) (62,66) (72,66) (82,66) (92,66) (102,66) (112,66) (122,66) (132,66) (142,66) |
| JMP27–JMP42 | E | `FL1_N`…`FL16_N` | 0805 | (15,88.5) (25,88.5) (35,88.5) (45,88.5) (55,88.5) (65,88.5) (75,88.5) (85,88.5) (95,88.5) (105,88.5) (115,88.5) (125,88.5) (135,88.5) (145,88.5) (155,88.5) (165,88.5) |
| JMP43–JMP46 | F | `TXD0`, `RXD0`, `RST`, `GPIO0` | 0805 | (134,21.5) (137,21.5) (140,21.5) (143,21.5) |
| JMP47–JMP50 | G | `+3V3`, `+3V3`, `+5V`, `+5V` | 0805 | (132,57) (136,57) (140,57) (144,57) |
| JMP51–JMP52 | H | `ECHO` ×2 | 0805 | (24,30) (32,30) |

**Status: `PLANNED`.** Positions are collision-free against `placement.csv` (verified) and sit inside their routing corridors, but a jumper is a consequence of the route order. Re-run `python tools/gen_jumpers.py` after the route and reconcile each row against the actual crossing. Group D (12 of 16 collectors) is the count most likely to move.

> **Why E is 16, not 8.** Each field channel has two connections to the common `FLD_12V` bus — the terminal pin 1 and the LED anode. Whichever side the bus takes, one per-channel trace must cross it. That is a certain crossing family.

Rules: never jumper `SW_NODE`, the moat, the keep-out or a collector line; all jumpers on F.Cu; B.Cu stays an unbroken stitched ground; every jumper silkscreened.

---

## 4. Connector map

| Ref | Type | Pin 1 | Pin 2 | Pin 3 | Pin 4 |
|---|---|---|---|---|---|
| **J1** | 2P 5.00 mm, left | `+12V_RAW` | `GND_FIELD` | — | — |
| **J2** | 4P 5.00 mm, left | `+5V` | `TRIG` (5 V buffered) | `ECHO` (5 V in) | `GND` |
| **J3–J10** | 2P 5.00 mm, right | `+12V` (M+) | `MOTn_N` (M−) | — | — |
| **J11–J26** | 2P 5.00 mm, bottom | `FLD_12V` | `FLn_N` (signal) | — | — |
| **J27** | 4P 5.00 mm, top | `+3V3` **OUT** | `TXD0` | `RXD0` | `GND` |

Channel mapping: `J3→M1 … J10→M8` (U4 GPA0–GPA7 → U6/U7), `J11→ch1 … J26→ch16` (U8→U5 GPA0-3, U9→GPA4-7, U10→GPB0-3, U11→GPB4-7).

**No bare headers, no JST, no unpopulated pads for field I/O.** J27 pin 1 is an *output* — never back-power it from a USB-TTL adapter.

---

## 5. Repository layout

```
design/     netlist generator, BOM, placement, review, layout plan
  gen_netlist.py        123 parts / 99 nets / 456 pins, re-validates on every run
  NETLIST.csv           one row per connected pin
  placement.csv         88 anchors: X, Y, rotation, body size, zone
  check_placement.py    206 geometry rules (keep-out, moat, 15/20/25 mm rules)
  02_bom.csv            34 lines, MPN + package + INR pricing
tools/      automation
  gen_jumpers.py        52-jumper schedule + collision check
  dfm_pipeline.py       20-point DFM harness -> production/DFM_REPORT.md
  place_from_csv.py     pcbnew placement + outline + rule areas
  release.py            kicad-cli gerbers / drill / pos / BOM / manifest
production/ DFM report + release artefacts
```

```bash
python design/gen_netlist.py        # regenerate netlist, must stay 99/456
python design/check_placement.py    # 206 checks, must stay 0 fail
python tools/gen_jumpers.py         # 52 jumpers, 0 collisions
python tools/dfm_pipeline.py        # writes production/DFM_REPORT.md
python tools/release.py             # needs kicad-cli + a routed board
```

---

## 6. 20-point DFM quality sign-off

Generated by `tools/dfm_pipeline.py` → [`production/DFM_REPORT.md`](production/DFM_REPORT.md).
**PASS 8 · WARN 1 · FAIL 0 · PENDING 11.**

| # | Check | Status | Basis | Evidence |
|---|---|---|---|---|
| 1 | ERC 0/0, PWR_FLAG per rail | **PENDING** | — | no `.kicad_sch`; `kicad-cli sch erc` |
| 2 | Schematic↔PCB parity, unrouted | **PENDING** | parity computed | 99 nets / 456 pins ✓; unrouted needs the board |
| 3 | Gerber / drill alignment | **PENDING** | — | no gerbers; `tools/release.py` |
| 4 | Edge clearance, outline closure | **PASS** | COMPUTED | 88 parts inside 180×100; U3 overhang to Y −4 as designed |
| 5 | Mask web ≥ 0.10 mm | **PASS** | COMPUTED | **0.57 mm** (1.27 − 0.60 − 2×0.05) |
| 6 | Annular ring ≥ 0.25 mm | **PASS** | COMPUTED | via **0.250**, terminal 0.550, M3 1.600 |
| 7 | Silk clipped by mask | **PENDING** | — | `kicad-cli pcb drc` |
| 8 | Acid traps / acute angles | **PENDING** | — | DRC + track-angle report |
| 9 | Thermal spokes ≥ 0.5 mm | **PENDING** | — | zone inspector after fill |
| 10 | Courtyard / 3D interference | **PASS** | COMPUTED | 88 parts + 52 jumpers, **0 body clashes** |
| 11 | Paste apertures | **PENDING** | — | needs F.Paste gerber |
| 12 | CPL rotation audit | **PENDING** | — | needs `.pos` |
| 13 | Current density (IPC-2221) | **PASS** | COMPUTED | 1.5 mm → 3.2 A; 0.6 mm → 1.3 A; 0.3 mm → 0.45 A |
| 14 | Via tenting | **PENDING** | — | needs F.Mask/B.Mask gerber |
| 15 | Via aspect ratio | **WARN** | COMPUTED | **5.333:1** = 0.6 % over the brief's 5.3 target, 33 % inside the 8:1 fab limit |
| 16 | Copper balance / islands / field zone | **PENDING** | — | rule area defined; needs fill |
| 17 | 3 fiducials + 4 tooling holes | **PASS** | COMPUTED | MH1–MH4 at (5,5)(175,5)(5,95)(175,95); FID1–3 |
| 18 | BOM ↔ footprint MPN / pin count | **PASS** | COMPUTED | 127 BOM refs, 0 mismatches (NC pins counted: U4+4, U5+4, U12+1) |
| 19 | Antenna keep-out void | **PASS** | COMPUTED | 0 objects in X 78–98, Y −4…4 |
| 20 | Clearance audit | **PENDING** | — | `kicad-cli pcb drc` with fab rules |

### Open engineering items before fab

1. **WARN 15** — 1.6 mm / 0.3 mm = 5.333:1 against a 5.3 target. Either accept (the fab allows 8:1) or drill 0.35 mm for 4.57:1.
2. **Confirm the PS2501-4 package** — DIP-16 vs gull-wing `PS2501L-4`. Different footprint; unfixable after fab.
3. **Confirm U12's SOT-23-5 pinout** — A/GND/NC/Y/VCC is the TI DBV convention; check the exact vendor.
4. **11 PENDING rows** — close them on a KiCad host, then re-run `dfm_pipeline.py`.

---

## 7. Assembly and flashing

**Boot straps (must hold at reset):**

| Pin | Required | Fitted |
|---|---|---|
| GPIO0 | HIGH = run, LOW = flash | R3 10 k pull-up + SW1 to GND |
| GPIO2 | HIGH | R5 10 k pull-up |
| GPIO15 | LOW | R4 10 k pull-down |
| GPIO12 (MTDI) | **LOW** | R6 10 k at 3.4 mm from pad 6 |

**Flashing via J27**

```
Pin 1  3V3  <- OUTPUT ONLY. Do not feed 3.3 V in; it back-drives the AMS1117.
Pin 2  TXD0 115200 8N1   (boot log at 74880 Bd is normal)
Pin 3  RXD0
Pin 4  GND
```

Manual sequence: hold **SW1 (FLASH)**, pulse **SW2 (RESET)**, release SW1, then upload. Firmware sets U4 `IODIR=0x00` / `OLAT=0x00` before any motor command; RN5/RN6 hold the ULN inputs low during boot regardless.

**First power-up**

1. 12 V only, **no motors, no field wiring**. Measure `+12V`, `+5V` = 5.0 ±0.15, `+3V3` = 3.3 ±0.1.
2. Confirm `GND`–`GND_FIELD` continuity **only through R31** (measure 0 Ω across it, and > 1 MΩ anywhere else).
3. Check the ESP boots (74880 Bd banner on J27 TX).
4. Fit one motor, verify direction and that the ULN package stays < 60 °C after 10 min at 300 mA.
5. Field inputs: apply 12 V to J11 pin 1 and pull pin 2 to 0 V — U5 GPA0 reads **0**.

**Thermal**: 4 motors simultaneous max unless the firmware implements a duty model — 8 channels at once puts U6/U7 at Tj ≈ 122 °C in a 50 °C enclosure.

---

## 8. Licence / provenance

Designed from the requirements set in this repository. Part numbers are Indian-market (Robu.in / Mouser IN) and priced ex-GST, ex-assembly: **≈ ₹2 063** for one board.
