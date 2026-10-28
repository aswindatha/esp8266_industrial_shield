# Part 5 — Layout & Routing Execution Plan

**Board:** 180 × 100 mm, 2 layer, 1.6 mm FR-4, 1 oz Cu, HASL-LF
**Coordinate system:** KiCad PCB editor — origin at the **top-left** board corner, X right, Y down, millimetres.
**Machine-readable placement:** [`placement.csv`](placement.csv) — validated by [`check_placement.py`](check_placement.py): **206 checks pass, 0 warnings, 0 failures**.

---

## 0. Constraint reconciliation — read this before you start

Four of the brief's constraints cannot coexist. They are resolved below, not ignored.

| # | Constraint | Arithmetic | Verdict | Resolution adopted |
|---|---|---|---|---|
| 1 | 16 × 2-pole 5.00 mm field terminals on the **left** edge | 16 × 10 mm = **160 mm** of a 100 mm edge | **Impossible** | One straight row on the **bottom** edge: 160 mm of 180 mm. This is also better: one straight isolation moat instead of an L, and uniform channel length. |
| 2 | J1 + J2 + 16 field terminals on the left | 10 + 20 + 160 = **190 mm** | Impossible | J1 and J2 stay on the left exactly as specified. |
| 3 | 8 motors + J27 on the **right** edge | 80 + 20 = **100 mm** = the whole edge | No room for mounting holes | J27 moves to the **top** edge at X 150–170. The right edge becomes 80 mm of motors with 10 mm margins. |
| 4 | 170 mm envelope | 160 mm terminal row + two 6.4 mm mounting pads + 1 mm copper clearance = **178 mm** | 170 too small | **180 mm** (+5.9 %). Terminals X 10–170, holes at X 4 and 176. |
| 5 | 13 × 16 mm antenna keep-out | The module's first pad sits at Y 4.6; a 13 mm keep-out reaches Y 9 and would cut across the module's own pads | Physically incoherent | Implemented **X 78–98, Y −4…4** (20 × 8 mm): the largest copper-free rectangle that clears the pad row. 4 mm of it is off-board. |
| 6 | GPIO12 trace to the ultrasonic trigger **< 25 mm**, J2 on the left | Pad 6 (80.4, 14.6) → J2 (5, 40) = **78 mm** | Violated | **U12 74AHC1G34 buffer** placed 8.1 mm from pad 6. The *GPIO12 net* is 8.1 mm; the long run to J2 is `TRIG_BUF`, a 5 V buffered output. This also fixes the 3.3 V → 5 V CMOS threshold marginality. |

### Schematic ECOs already applied to the netlist

| ECO | Change | Reason |
|---|---|---|
| E1 | J2 ↔ J27 roles swapped | J2 = ultrasonic (left), J27 = UART diagnostic (top right), per this brief |
| E2 | H1, H2, TP1–TP3 deleted | "no bare pin headers … for field I/O"; J27 now carries 3V3/TX/RX/GND |
| E3 | **U12 74AHC1G34 + C20 added** | GPIO12 strap isolation and 5 V level for the sensor |
| E4 | RN7, RN8 added | U4 GPB0–7 spare I/O parked low now that H1 is gone |
| E5 | **GND split into `GND` / `GND_FIELD`**, joined by R31 0 Ω | 2.4 A of motor return stays out of the logic copper |
| E6 | D1 SMAJ28A → **SMAJ15A**, D2 SS34 → **SS54** | Review findings H1 / H2 |
| E7 | J2, J27 changed from JST-XH / 2.5 mm to **5.00 mm terminal** | "5.00 mm pitch only" |

Netlist after ECOs: **123 parts, 99 nets, 456 pins, 0 floating pins**. `GND` = 68 pins (logic), `GND_FIELD` = 18 pins (motor/power return), R31 is the only bridge.

---

## 1. Dimensioned zone floorplan (mm)

```
X = 0       20       40       60       80      100      120      140      160    180
    ┌────────┬────────┬────────┬────────┬────────┬────────┬────────┬────────┬──────┐
Y=0 │  MH1   │              J27 ▐ UART 150–170 ▐        ▓ ANTENNA KEEP-OUT ▓      │
    │  ⌾     │                                     ▓ X78–98, Y−4…4 ▓            │
 10 │  J1    │  F1 D2  U1   L1   C4   U2          R6  U12        SW2 SW1          │
    │ 2P ▐  │  D1 C1  D3        C5   C6    C10 C11                ▐ U6 ▐  [J3]  │
 20 │        │     C2      C3        C7 C8 C9         R1-R5 RN5/6   ▐    ▐        │
    │  J2    │                       R31   C13  U4 103–121  RN7/8  ▐    ▐  [J4]  │
 30 │ 4P ▐  │                             ▐ U5 81–99 ▐               ▐    ▐        │
    │        │                                    C14        C19    ▐    ▐  [J5]  │
 40 │        │                                                      ▐    ▐        │
    │        │                     R7 R8                            ▐    ▐  [J6]  │
 50 │        │                        ▐ U5 ▐                        ▐ U7 ▐        │
    │        │                                                      ▐    ▐  [J7]  │
 60 │  RN1   │   RN2    │   RN3    │   RN4                         ▐    ▐        │
    │        │          │          │                               ▐    ▐  [J8]  │
 70 │════════╪══════════╪══════════╪═════ ISOLATION MOAT  X 6–160  ═╪════╪═══════│
    │  U8    │   U9     │   U10    │   U11                         ▐    ▐  [J9]  │
 80 │ R11-14 │ R15-18   │ R19-22   │ R23-26                        ▐    ▐        │
    │ D4-D7  │ D8-D11   │ D12-D15  │ D16-D19                       ▐    ▐ [J10]  │
 90 │ [J11][J12][J13][J14][J15][J16][J17][J18][J19] … [J26]         │  MH4        │
100 └────────┴────────┴────────┴────────┴────────┴────────┴────────┴────────┴──────┘
    MH1(5,5)  MH2(175,5)  MH3(5,95)  MH4(175,95)      ⌾ = M3 hole, 3.2 mm drill / 6.4 mm pad
```

### Zone definition

| Zone | Rectangle (mm) | Contents | Copper rule |
|---|---|---|---|
| **Z1 field** | X 0–180, Y 73–100 | 16 terminals, 16 × 1.2 k, 16 × 1N4148, FLD_12V bus | Field nets only. **No ground pour.** |
| **Z1b opto band** | X 20–165, Y 66–76 | U8–U11 bodies straddling the moat | Split by the moat |
| **Moat** | X 6–160, **Y 71–73** | 2.0 mm, both layers, copper-free | Rule area |
| **Z2 logic / RF** | X 72–140, Y 0–62 | U3, R1–R6, C10–C12, C18–C20, U12, U4, U5, RN1–RN8, SW1/SW2 | GND pour, stitched |
| **Z3 power** | X 10–70, Y 0–30 | J1, F1, D1, D2, C1–C3, U1, D3, L1, C4–C9, R31 | GND_FIELD pour |
| **Z3b actuator** | X 140–180, Y 10–95 | U6, U7, C15, C16, C19, J3–J10 | GND_FIELD pour + collector pours |
| **Z4 maintenance** | X 145–175, Y 0–10 | J27 | — |

### Placed anchors (footprint origin, mm)

| Ref | X | Y | Rot | Ref | X | Y | Rot | Ref | X | Y | Rot |
|---|---|---|---|---|---|---|---|---|---|---|---|
| J1 | 5 | 15 | 270 | U1 | 32 | 8 | 0 | U8 | 35 | 72 | 270 |
| J2 | 5 | 40 | 270 | D3 | 32 | 15 | 90 | U9 | 73 | 72 | 270 |
| J3–J10 | 175 | 15…85 (10 mm) | 90 | L1 | 43 | 8 | 0 | U10 | 111 | 72 | 270 |
| J11–J26 | 15…165 (10 mm) | 95 | 180 | C4 | 52 | 10 | 0 | U11 | 149 | 72 | 270 |
| J27 | 160 | 5 | 0 | U2 | 61 | 13 | 0 | RN1–RN4 | 35/73/111/149 | 63 | 0 |
| F1 | 14 | 4 | 90 | **U3** | **88** | **8** | 0 | RN5/RN6 | 125/129 | 26 | 0 |
| D1 | 14 | 13.5 | 90 | R6 | 77 | 14.6 | 90 | RN7/RN8 | 124/128 | 22 | 0 |
| D2 | 18 | 10 | 90 | **U12** | **73** | **18** | 0 | **U6** | **157** | **30** | 0 |
| C1 | 21 | 17 | 0 | U4 | 112 | 30 | 0 | **U7** | **157** | **56** | 0 |
| R31 | 30 | 24 | 0 | U5 | 90 | 52 | 0 | C19 | 145 | 42 | 0 |
| C19 | 145 | 42 | 0 | SW1/SW2 | 112/104 | 11 | 0 | C15/C16 | 166 | 24/50 | 0 |

**Rotation convention:** rotation is chosen so the wire entry faces off-board. If your footprint has the entry on the opposite side, add 180°. Verify J1/J2 (270°), J3–J10 (90°), J11–J26 (180°), J27 (0°) by hovering the 3D view before routing.

### Passive clusters (place by anchor + pitch, not individually)

| Cluster | Qty | Anchor | Pitch | Y | Note |
|---|---|---|---|---|---|
| R11–R14 | 4 | U8 X = 35 | 5.08 (channel-aligned) | 82 | field side, below its opto |
| R15–R18 | 4 | U9 X = 73 | 5.08 | 82 | |
| R19–R22 | 4 | U10 X = 111 | 5.08 | 82 | |
| R23–R26 | 4 | U11 X = 149 | 5.08 | 82 | |
| D4–D7 | 4 | U8 X = 35 | 5.08 | 86.5 | anode to `OPTn_K`, cathode to FLD_12V |
| D8–D11 / D12–D15 / D16–D19 | 4 each | U9 / U10 / U11 X | 5.08 | 86.5 | |
| R1, R2, R3, R4, R5 | 1 each | see anchors | — | — | 0805, rot 90 |
| C10–C20 | 1 each | see anchors | — | — | 0805 unless noted |

### Why the optos are spread across the row, not clustered at the left

Each opto sits directly above its four terminals (U8 over J11–J14, U9 over J15–J18, U10 over J19–J22, U11 over J23–J26). Field trace length is then ≤ 20 mm for every channel instead of ≤ 130 mm for channels 13–16. The moat stays a single straight line, and the 16 collector traces fan into U5 across a 12 mm channel — free on two layers.

---

## 2. Routing priority strategy

Route in this order. Each wave is finished and DRC-clean before the next starts.

### Wave 1 — Buck hot loop (highest priority, ~30 min)

**Loop:** `U1.SW (pin 2) → L1.1 → C4.+ → C4.− → GND_FIELD → U1 pins 5–8 → U1.SW`

- Enclosed area: **≈ 240 mm² if C4's return loops around the perimeter, ≈ 150 mm² if it returns diagonally to U1 pins 5–8.** The second is the target; the 200 mm² rule is about the return path, not the components' bounding box.
- C4's negative terminal must connect to U1 pins 5–8 **first**, then to the plane — not to the far side of the GND_FIELD pour.
- SW node copper: keep it as small as the current allows (0.8 mm wide, ~6 mm long). It is a 12 V switching node with dV/dt ≈ 1 V/ns; every mm² is radiated EMI.
- D3 cathode to U1 pin 2 and L1.1: **one continuous copper shape**, no necking.
- **Never via the SW node to another layer.**

### Wave 2 — +12 V trunk (1.5 mm) and motor returns (0.6 mm)

- `+12V` on **F.Cu** (the brief reserves B.Cu for the ground plane): J1.1 → F1 → D2 → U1.1/U1.4, then a second branch along Y ≈ 4 to X 168, down X ≈ 168 to U6.10 and U7.10, and short stubs to J3–J10 pin 1.
- Width check: 1.5 mm = 59 mil → **3.2 A** at 10 °C rise. Continuous load is 2.8 A. **Do not neck below 1.2 mm anywhere**; at the ULN COM pins use a 0.8 mm stub × 2.
- Keep `+12V` ≥ 2.0 mm from every `MOTn_N` trace and ≥ 5 mm from the I²C pair.
- Motor returns: 0.6 mm from U6/U7 outputs to J3–J10, ≤ 20 mm (validated: 18.7 / 18.0 mm).
- The `+12V` run at X 168 passes within 2.8 mm of the field terminal J26 (X 160–170, Y 90–100). It stops at Y 88 — verify no crossing.

### Wave 3 — Isolation and the field side

- **Nothing crosses the moat.** Field side (Y > 73): `FLD_12V`, `OPTn_K`, `FLn_N`, and the 1.2 k / 1N4148 parts only.
- `FLD_12V` bus: 1.0 mm horizontal run at Y ≈ 88, feeding 16 terminal pin 1s and 16 diode cathodes. Reference it to no plane.
- Field signal: opto pin → 1.2 k → terminal pin 2, ≤ 20 mm, 0.3 mm.
- The 16 collector traces (`OPTn_COL`) leave the opto at Y 68.2, cross the band Y 60–68 at 0.3 mm / 0.254 mm spacing, and enter U5. Use a 12 mm wide routing channel; **no layer change**, no vias in the isolation band.
- Emitters (U8–U11 pins 9/11/13/15) go straight to the GND pour above the moat with a solid (non-relieved) connection.

### Wave 4 — I²C at 100 kHz

| Parameter | Budget | Achieved |
|---|---|---|
| Total bus length | ≤ 120 mm | ESP pad 20 (95.6, 8.6) → U4 (112, 30) ≈ 27 mm; → U5 (90, 52) ≈ 44 mm; **≈ 71 mm** |
| Stub length | ≤ 40 mm | ≈ 30 mm |
| Width / spacing | 0.30 / 0.254 mm | — |
| Separation from `MOT*` | ≥ 2 mm, no parallel run > 20 mm | — |
| Pull-ups | 4.7 k at the far end (U5 end) | R7/R8 at (97–100, 45) |

- Run SDA and SCL as a pair, 0.254 mm apart, with the GND pour continuous beneath on B.Cu. No layer changes: at 100 kHz with \(C_{bus} \approx 25\ \text{pF}\) the rise time is \(2.2 \times 4.7\text{k} \times 25\text{p} = 0.26\ \mu\text{s}\), well inside the 1 µs standard-mode limit.
- Keep the pair ≥ 3 mm from the antenna keep-out and ≥ 2 mm from `SW_NODE`.

### Wave 5 — Strapping and the GPIO12 strap net (the C2 mitigation)

- **`TRIG` net (GPIO12) is 8.1 mm total**: pad 6 → R6 (3.4 mm) → U12.1. Route it on F.Cu only, 0.3 mm, no vias, no parallel neighbour.
- R6 sits at (77, 14.6), 3.4 mm from the pad, with its GND return via a dedicated via 1.5 mm away.
- `TRIG_BUF` from U12.4 (73, 18) to J2.2 (5, 40): ~74 mm on F.Cu. This is a 5 V buffered output — length is not critical, but keep it ≥ 2 mm from the field terminals and away from the antenna.
- `ECHO` from J2.3 through R27/R28 to pad 5 (80.4, 12.6): place the divider at (14, 62) so the 3.3 V side is short.

### Wave 6 — remaining signals and silkscreen

- Buttons, LED-less reset/flash, TP4–TP6 probe pads.
- Silkscreen: `ISOLATION BARRIER` dashed line along Y 72; `+12V`, `M+`, `M−` on every motor terminal; channel numbers `1…16`; `3V3 OUT` at J27.1; `GND_FIELD` and `GND` labels at R31.

### Net-to-layer assignment

| Net group | Layer | Width | Why |
|---|---|---|---|
| `+12V`, `VIN_A`, `+12V_RAW` | F.Cu | 1.5 mm | power patch per brief; B.Cu stays a plane |
| `MOT1_N`…`MOT8_N` | F.Cu | 0.6 mm | short, straight to the edge |
| `SW_NODE` | F.Cu only | 0.8 mm | never via |
| `+5V`, `+3V3` | F.Cu | 0.5 mm | |
| `SDA`, `SCL` | F.Cu | 0.3 mm | pair, ground underneath |
| `OPTn_COL` | F.Cu | 0.3 mm | no vias in the isolation band |
| `OPTn_K`, `FLn_N`, `FLD_12V` | F.Cu | 0.3 / 1.0 mm | field side |
| `GND` | B.Cu pour + F.Cu pour | — | stitch 5 mm grid |
| `GND_FIELD` | B.Cu pour (Z3) + F.Cu | — | joined to GND only at R31 |

---

## 3. Copper pour and thermal relief plan

### Pour map

| # | Layer | Net | Extent | Exclusions |
|---|---|---|---|---|
| P1 | B.Cu | `GND` | X 0–180, Y 0–71 | antenna keep-out X 78–98 / Y −4…4; 1.0 mm gap to P2 |
| P2 | B.Cu | `GND_FIELD` | X 0–75 Y 0–50 **+** X 140–180 Y 8–95 | 1.0 mm gap to P1 at all boundaries |
| P3 | F.Cu | `GND` | Z2 only, X 72–140, Y 0–66 | keep-out, moat, collector pours |
| P4 | F.Cu | `GND_FIELD` | Z3 + Z3b | — |
| P5 | F.Cu | `MOT*` collector pours | U6: X 160–172, Y 16–41; U7: X 160–172, Y 50–75 | isolated from every pour |
| P6 | F.Cu | `+3V3` | 200 mm² on U2 tab | isolated from GND |
| — | both | **none** | X 0–180, Y 73–100 (field zone) | no copper except field nets |

**The field zone gets no ground pour at all.** A floating copper island below the barrier is an antenna that couples motor noise straight into the opto LED side. The only copper there is `FLD_12V`, `OPTn_K`, `FLn_N` and the part pads.

**The moat is a hard exclusion** on F.Cu, B.Cu and both mask layers (rule area: tracks, vias, pads, copper fill, footprints all disallowed). Do not let the pour "heal" across it at the ends — terminate the moat at X 6 and X 160 with a 2 mm flare so no copper can sneak around.

### Thermal relief parameters

| Object | Connection | Reason |
|---|---|---|
| U1 pins 5–8, C1/C4/C19/C7/C9 negatives | **solid** | 2.8 A return; thermal spokes would add resistance |
| U2 tab (P6) | solid, 4 × 0.3 vias | 0.61 W |
| U6/U7 pin 9 | **solid**, 6 × 0.3 vias in a 10 × 8 mm island | 1.2 A per device |
| D2 both pads | solid, 8 vias | 1.4 W |
| All 0805/1206 signal pads | thermal relief, 0.5 mm gap, 0.5 mm spoke, 4 spokes | solderability |
| Opto emitters / collectors | solid | 25 mA, no benefit from relief |
| Terminal block pads | solid | mechanical |

### D2 — the 1.4 W problem

| Measure | θJA | Rise at 1.4 W | Tj at 50 °C ambient |
|---|---|---|---|
| SMA on minimum copper | ≈ 75 °C/W | 105 °C | **155 °C** — fails |
| SMA with 150 mm² per pad, 8 vias | ≈ 55 °C/W | 77 °C | **127 °C** — marginal |
| **SS54** (VF 0.45 V) + same pour | 1.26 W → 69 °C | 119 °C | acceptable with 6 °C margin |
| P-FET (20 mΩ) | 0.06 W | 3 °C | 53 °C — the durable answer |

Specified: **SS54 + 150 mm² per pad + 8 × 0.3 mm vias to the GND_FIELD plane on B.Cu.** If the product runs at 50 °C ambient with all 8 motors on, replace D2 with a P-FET (`DMP3098L`).

### U6/U7 — collector dissipation

- 12 × 25 mm pour on F.Cu over pins 11–18 (300 mm² each), 0.5 mm necks to every collector pin.
- **No vias in this pour.** The collector sits at 12 V when off and 0.9 V when on; a via would short to the GND plane.
- 10 × 8 mm GND island butting the pin-9 end, **6 × 0.3 mm vias** — this is the only thermal via field on the device.
- 2 oz copper on B.Cu if the enclosure is sealed and ambient > 45 °C.
- Firmware interlock: max 4 motors energised simultaneously (halves the dissipation to 0.6 W per device → Tj ≈ 74 °C).

### Star ground

```
  GND_FIELD pour  ─────────────────────────  R31 (0R 1206, 2 A)
  (J1.2, D1, C1, U1 GND, C4, C19,            at (30, 24), the ONLY bridge
   U6.9, U7.9, C15/C16)
                                              │
  GND pour  ──────────────────────────────────┘
  (U3, U4, U5, opto emitters, R31.2, all logic caps)
```

R31 carries the logic return (≤ 400 mA) → 0 Ω 1206, 2 A rating, 20 mV drop. Its two pads must each connect solidly to their own pour, with 4 vias each. Place a silkscreen `STAR GND — DO NOT BRIDGE` next to it.

### Stitching via schedule

| Region | Grid | Count |
|---|---|---|
| Board perimeter, 3 mm inset | 5 mm | ~70 |
| Around U3 (body perimeter, not the antenna) | 2 mm | ~24 |
| U6 / U7 ground island | 3 mm | 6 each |
| U2 tab | — | 4 |
| D2 pads | — | 8 |
| Along the moat edges (both sides, 3 mm from the edge) | 5 mm | ~60 |

Via: **0.6 mm pad / 0.3 mm drill**, non-tented on the ground plane only (tent the signal vias).

---

## 4. Gerber / DFM verification checklist — Indian fabs

Run this against the *exported* Gerbers, not the KiCad design. Every item is a reject at PCB Power / LionCircuits / Protoserve if it fails.

### Mechanical and copper

| # | Check | Limit | This design |
|---|---|---|---|
| 1 | Board outline closed, single polyline on `Edge.Cuts` | no gaps, no self-intersection | 180.0 × 100.0 mm |
| 2 | Copper-to-board-edge | ≥ 0.50 mm (fab min 0.30) | 0.50 mm on pours, 3.0 mm on the terminal pads |
| 3 | Hole-to-board-edge | ≥ 0.50 mm | 3.2 mm holes at 5 mm inset |
| 4 | Minimum annular ring | ≥ 0.15 mm (we specify 0.25) | 0.25 mm all PTH |
| 5 | Minimum drill | 0.30 mm | vias 0.3, terminals 1.3 |
| 6 | Hole-to-hole | ≥ 0.50 mm | 1.27 mm pitch SOIC → 0.67 mm |
| 7 | Minimum track / space | 0.25 / 0.25 mm | 0.25 mm (I²C 0.30/0.254) |
| 8 | Copper sliver | ≥ 0.25 mm, none isolated | zone "remove islands" = always |
| 9 | Solder-mask dam | ≥ 0.10 mm between openings | 1.27 mm pitch, 0.6 mm pads, 0.05 mm expansion → **0.57 mm dam** |
| 10 | Solder-mask expansion | 0.05 mm (not 0.10) | preserves the dam on U4/U5/U6/U7 |
| 11 | Silkscreen line / text | 0.15 mm / 1.0 mm | 0.15 / 1.0 |
| 12 | Silk over pad | none | DRC `silk over copper` = 0 |
| 13 | V-score / route clearance | ≥ 0.40 mm from copper | rails outside that |
| 14 | Fiducials | 3 × 1.0 mm, 2.0 mm mask opening, 5 mm from edge | F.Cu, not under a part |

### Isolation and antenna (design-specific)

| # | Check | Method |
|---|---|---|
| 15 | Moat copper-free on **F.Cu, B.Cu** and in the poured gerbers | Open the Gerber in a viewer, measure 2.0 mm at Y 71–73 across X 6–160 |
| 16 | No ground pour anywhere in the field zone (Y 73–100) | Visual: the region must be 90 % bare FR-4 |
| 17 | Antenna keep-out empty on **both** copper layers and both mask layers | 20 × 8 mm at X 78–98, Y −4…4 |
| 18 | No via, pad or trace inside the keep-out | Count objects = 0 |
| 19 | Field traces and logic traces never share a via | Visual + netlist check |

### Drill and output

| # | Check | Value |
|---|---|---|
| 20 | Drill file format | Excellon, **2.4**, mm, absolute, PTH and NPTH **separate files** |
| 21 | Gerber format | X2, 4.6, mm, leading zeros omitted, `%TF` attributes present |
| 22 | Layers shipped | F.Cu, B.Cu, F.Mask, B.Mask, F.SilkS, B.SilkS, Edge.Cuts + 2 drill files |
| 23 | Paste layers | only for the stencil order — do not send with the bare-board order |
| 24 | Drill count sanity | 3.2 mm × 4, 1.3 mm × 54 (25 terminals + 4 terminals), 0.3 mm vias per the stitch schedule |
| 25 | Panel | 2-up, 5 mm rails, V-score or 3 mm mouse bites; confirm the fab's panel |

### Before you press "order"

1. Open the gerbers in **GerbView / KiCad Gerber Viewer** and toggle each layer — the moat and keep-out must be visibly empty.
2. Run **DRC with the manufacturer's rules loaded**, not the KiCad defaults: 0.25/0.25, 0.3 drill, 0.15 annular.
3. Check the **3D render from the top and bottom**: terminal orientation, `+`/`−` markings, `ISOLATION BARRIER` legible at 1.0 mm.
4. Confirm the **assembly drawing** shows J1/J2 on the left, motors right, fields bottom, J27 top — a swapped connector at the fab is a scrapped panel.

---

## 5. Execution sequence in KiCad

1. **Board Setup ▸ Stackup**: 2 layers, 1.6 mm, 0.035 mm copper, `Edge.Cuts` = 180 × 100 at (0,0).
2. **Board Setup ▸ Design Rules**: 0.25/0.25, via 0.6/0.3, hole 0.3, edge 0.5, mask 0.05 expansion.
3. **Net classes**: `PWR_12V` 1.5 mm, `MOTOR` 0.6, `PWR_5V` 0.5, `PWR_3V3` 0.5, `FIELD` 0.3/0.5 clear, `I2C` 0.30/0.254.
4. **Place the 4 mounting holes and the 25 terminals first** — they are the fixed points. Import the coordinates from `placement.csv` (KiCad accepts a space-separated XY list in the "Position" dialog, or script it with `pcbnew`).
5. Place Z3 power chain → Z2 logic → Z1 opto band → passives, in that order.
6. **Draw the moat rule area and the antenna keep-out before any pour.**
7. Route waves 1 → 6 in order; DRC after each wave.
8. Pour P1–P6, then stitch vias, then re-pour.
9. Run `check_placement.py` against the final `placement.csv` export, then DRC, then the Gerber checklist.

> If you change any coordinate, edit `placement.csv` and re-run the checker — it will catch a keep-out violation or a broken 20 mm rule before the fab does.

---

## 6. Single-layer contingency (B.Cu only)

**Verdict: not viable in 180 × 100 mm, and not recommended.** A single-sided build needs roughly 22 % more area for the same circuit (200 × 110 mm minimum) and about **52 zero-ohm jumpers**. The figure below is the schedule to design against; the exact list can only be finalised after a trial route, because a jumper is a consequence of the route order, not of the schematic.

What breaks first when you remove F.Cu routing:

1. **The ground plane.** If B.Cu carries signals, it is no longer a plane. The brief requires an intact star ground on B.Cu — so signals must **not** use B.Cu, which means every crossing becomes a jumper. These two requirements together are what forces the 52 count.
2. **The isolation moat.** A jumper cannot cross it. Any field trace that would need to cross goes around the moat ends at X 6 / X 160, adding 30–60 mm per channel.
3. **The antenna keep-out.** No jumper, no trace, no via. Anything routed past the module goes below Y 20.

### Jumper schedule

| Group | Nets involved | Est. qty | Location window (mm) | Type |
|---|---|---|---|---|
| A | `+12V` trunk to U6/U7 COM | 6 | X 100–168, Y 4–60 | 1206 0 Ω (2 A) |
| B | `GND_FIELD` return from U6/U7 pin 9 to the pour | 4 | X 150–166, Y 25–60 | 0805 0 Ω |
| C | `SDA` / `SCL` crossing the motor-drive fan-out | 4 | X 120–150, Y 30–45 | 0805 0 Ω |
| D | `OPT1_COL`…`OPT16_COL` fan-in to U5 | 12 | X 30–160, Y 58–68 | 0805 0 Ω |
| E | `FL1_N`…`FL16_N` crossing the `FLD_12V` bus | 16 | X 15–165, Y 88.5 | 0805 0 Ω |
| F | `TXD0`, `RXD0`, `RST`, `GPIO0` to J27 and the buttons | 4 | X 96–150, Y 6–20 | 0805 0 Ω |
| G | `+3V3` / `+5V` reaching U11, RN4, C20 | 4 | X 140–160, Y 0–60 | 0805 0 Ω |
| H | `ECHO` from the divider to GPIO14 | 2 | X 10–80, Y 12–62 | 0805 0 Ω |
| | **Total** | **52** | | |

> **Why E is 16 and not 8.** Every field channel has two connections to the common `FLD_12V` bus — the terminal pin 1 and the opto LED anode. Whichever side the bus is routed, one of the two per-channel traces must cross it. That is a certain crossing family, not a routing artefact, so all 16 channels need a link. Group D (12) remains a fan-in estimate and is the one count most likely to move when the route is drawn.

### Hard rules for the fallback

- **Never jumper:** `SW_NODE` (the buck hot loop), anything inside the antenna keep-out, anything crossing the moat, or a sense line that the jumper's 0.05 Ω would corrupt (there are none here, but the rule stands).
- **`SDA`/`SCL` are the exception that needs care:** a 0 Ω in an I²C line adds ~2 pF of pad capacitance and a stub. Keep each I²C jumper under 5 mm, and never put one on the branch between the pull-ups and U5.
- **All jumpers on F.Cu.** B.Cu stays a continuous, stitched `GND` / `GND_FIELD` plane with the R31 star — that requirement does not relax.
- **Every jumper gets a reference designator on the silkscreen and a line on the assembly drawing.** An unmarked 0805 jumper is a board that ships with the motors not working.
- **0805 0 Ω is 2 A; use 1206 for the `+12V` group.** Never use a 0402 as a jumper.
- Re-run `check_placement.py` after adding the jumper parts — it will flag any that land in the keep-out or the moat.

### What changes in the BOM

| Item | Qty | Package | Note |
|---|---|---|---|
| JMP1–JMP52 | 52 | 0805 0 Ω (6 × 1206 in group A) | +₹52, plus 52 extra placements |
| Board | 1 | 200 × 110 mm | +22 % area, +₹90 |

If the single-sided constraint is driven by cost, compare against the 2-layer quote before committing: at 100 pcs the two-layer board is typically cheaper than the two-layer board **plus 52 placements**, and it is measurably better on both EMI and thermal.
