# Part 4 — Layout, Routing and DFM Constraints

Target: **170 × 100 mm, 2 layer, 1.6 mm FR-4, 1 oz (35 µm) copper, HASL-LF, green LPI mask** — comfortably inside what every Indian fab (PCB Power, LionCircuits, Protoserve, Calumet, Shogini) quotes as standard.

---

## 4.1 Stack-up

| Layer | Use | Copper |
|---|---|---|
| Top (F.Cu) | All SMD, signal routing, GND pour | 35 µm |
| Bottom (B.Cu) | GND pour + `+12V` distribution + motor returns | 35 µm |
| Core | FR-4, Tg 130–150 °C, 1.6 mm ±10 % | — |

Do **not** ask for controlled impedance — nothing here is high speed (the fastest edge is the 150 kHz buck, and the I²C bus is 100 kHz). A 4-layer board buys nothing except a cleaner RF ground under the ESP; if you later add Ethernet or an SD card, reconsider.

### 1-layer vs 2-layer — the real trade-off

| | Single sided | 2 layer (recommended) |
|---|---|---|
| Feasible? | **No.** 27 through-hole connectors on both long edges plus 60+ SMD parts cannot be routed without crossings, and the ESP-12F needs a ground reference under its body for the antenna to work. | Yes |
| Cost delta at 100 pcs, 170×100 | ≈ −₹40/board | baseline |
| EMI | Motor di/dt has no return path underneath → large loops | Bottom GND gives an image plane under every top trace |
| Thermal | No back-side copper to spread ULN2803 heat | Back-side pour + vias roughly halves θJA |
| Field isolation | No second layer to route the field bus away from logic | Field bus on the bottom, logic on top, moat between |

**Verdict: 2 layers, no compromise.** The only case for single-sided is a <20-piece prototype where you hand-etch — and even then the ESP-12F antenna will perform poorly.

---

## 4.2 Trace widths (IPC-2221, external layer, 1 oz, 10 °C rise)

A = (I / (0.048 · ΔT^0.44))^(1/0.725) mil², width = A / 1.378 mil.

| Net | Current | Minimum width | Use |
|---|---|---|---|
| `+12V` input (J1 → D2 → U1, motor bus) | 2.8–3.2 A | **1.5 mm** | 1.5 mm |
| `MOTn_N` (each motor) | 0.30 A | 0.20 mm | 0.5 mm |
| ULN2803 pin 9 → GND | 1.2 A per device | 0.40 mm | 0.8 mm + pour |
| `SW_NODE` | 0.6 A pk | 0.50 mm | 0.8 mm, ≤ 200 mm² loop |
| `+5V` | 0.5 A | 0.25 mm | 0.5 mm |
| `+3V3` | 0.36 A peak | 0.25 mm | 0.4 mm |
| `FLD_12V` field bus | 0.15 A total | 0.20 mm | 1.0 mm bus along the terminals |
| `OPTn_K` / `FLn_N` | 9 mA | 0.20 mm | 0.3 mm |
| `SDA` / `SCL` | — | 0.20 mm | 0.3 mm, matched length ±2 mm |

Key point: **0.25 mm is the fabrication floor, not a power rule.** 0.25 mm carries only ≈ 0.88 A at 10 °C rise. The `+12V` trunk must be 1.5 mm or a pour.

---

## 4.3 Floor plan

```
   X=0                                                                    X=170
Y=0  ┌────────────────────────────────────────────────────────────────────────┐
     │  J27(ultra)      ▓▓▓ ESP-12F ▓▓▓                                       │
     │                    ▲ antenna overhangs the top edge                    │
     │  ┌─────────┐      (no copper 13 × 16 mm, any layer)                    │
     │  │ J1 12V  │                                                           │
     │  │ F1 D1 D2│         ┌──────────┐        ┌────────────┐                │
     │  │ U1 buck │         │ U4 0x20  │  I2C   │ U5 0x21    │   ┌─────────┐  │
     │  │ L1 C4   │         │ motors   │◄──────►│ inputs     │   │ U6      │  │
     │  │ U2 LDO  │         └──────────┘        └────────────┘   │ ULN     │  │
     │  └─────────┘                                                │ M1-M4   │  │
     │  J2 UART                                     ┌──────────┐   └─────────┘  │
     │  H2 PROG                                     │ U8 U9    │   ┌─────────┐  │
     │                                              │ PS2501-4 │   │ U7      │  │
     │              ══════════ ISOLATION MOAT ══════│          │   │ ULN     │  │
     │                                              │ U10 U11  │   │ M5-M8   │  │
     │                                              └──────────┘   └─────────┘  │
     │   J11 J12 J13 J14 J15 J16 J17 J18 J19 J20 J21 J22 J23 J24 J25 J26      │
Y=100└────────────────────────────────────────────────────────────────────────┘
                                                    J3..J10 on the right edge
```

Anchors:
- **U3**: antenna end 4 mm outside the top edge; body centred at X = 82 mm.
- **J3–J10** (motors): right edge, 10 mm pitch, Y = 10…90 mm.
- **J11–J26** (fields): bottom edge, 10 mm pitch, X = 5…165 mm.
- **U6/U7**: within 15 mm of their motor terminals — the 0.3 A runs stay short.
- **U8–U11**: within 20 mm of the field terminals; **field pins (1–8) face the terminals**, logic pins (9–16) face U5.
- **J1**: top-left corner, away from the antenna.
- **J27**: top edge, ≤ 25 mm from U3 (TRIG/ECHO are short).

Why the ESP at the top centre: the antenna is the only RF-critical element; it needs a board edge, no copper, and distance from the 2.4 A motor switching. The ULN2803s are at the opposite corner of the RF keep-out.

---

## 4.4 Copper pour strategy

| Zone | Top pour | Bottom pour |
|---|---|---|
| Whole board | GND, 0.3 mm clearance | GND, 0.3 mm clearance |
| Under U3 body (not antenna) | GND, stitched | GND, stitched |
| **Under U3 antenna** | **none** | **none** — rule area, all layers |
| Isolation moat | **none** | **none** |
| ULN2803 collector area | GND-free; use `+12V`? **No** — leave the collector pads isolated, add a GND thermal pad beside them | GND pour, 6 vias per device |
| Power input | GND | `+12V` flood on the bottom from J1 to U1 |

Rules:
1. **One ground, not two.** A split ground plane forces return currents to detour and is the most common cause of "works on the bench, fails in the field". Use a single pour, and instead *place* the motor current path so it never crosses the ESP/opto region.
2. Star point: the ULN2803 GND pins, C19 negative, D1 anode and U1 pins 5–8 all connect to the pour within a 15 mm circle. That is the star; nothing else needs a special connection.
3. Stitching vias: 0.6/0.3 mm on a 5 mm grid around the board perimeter; 2 mm grid around U3's ground pads; 6 vias per ULN2803; 4 vias under the AMS1117 tab.
4. Minimum pour width between isolated nets: 0.4 mm (avoid slivers). Set `Zone ▸ Remove islands` = "always".

---

## 4.5 Isolation: moat, creepage and when a slot is actually needed

### The standard's answer

For a **12 V** working voltage, IPC-2221 Table 6-1 requires only ≈ 0.13 mm clearance (external, uncoated, ≤ 3050 m). IEC 62368-1 for 12 V SELV with pollution degree 2 gives 0.4 mm clearance / 0.8 mm creepage for functional insulation. **0.25 mm design rules already exceed both.**

So a 2 mm moat is not a compliance requirement — it is an **EMI, ground-loop and hipot** decision. Say so in your design review, or someone will ask why you added a milling operation for a 12 V board.

### Recommended moat (default)

- 2.0 mm copper-free strip on **both layers**, running the full length of the opto row, centred between the field pads and the logic pads of U8–U11.
- Continues 3 mm past the outermost optocoupler and then turns toward the board edge so no field copper can sneak around the end.
- Silkscreen a dashed line + `ISOLATION BARRIER` along the centre.
- **No vias, no traces, no pour** in the strip. Enforce with `Place ▸ Rule Area` → keep out tracks, vias, copper fill, footprints.

### Optional routed slot (only if you need hipot)

- 2.0 mm wide slot on `Edge.Cuts`, centred on the moat, spanning from 2 mm before U8 to 2 mm after U11.
- Clearance from the slot edge to any pad ≥ 1.0 mm; keep it ≥ 5 mm away from terminal-block mounting forces.
- Cost: one extra milling pass, typically ₹150–300 setup, and it can snag on conveyor rollers. It roughly doubles creepage across the barrier (≈ 2 mm + 2 × 1 mm of FR-4 thickness).
- **Do not** route the slot through the ULN2803 or ESP area — only the opto row.

### The isolation caveat that matters more than the slot

`R29` (0 Ω) ties `FLD_12V` to the board's `+12V`. With that fitted and the field devices powered from the same 12 V supply, **there is no galvanic isolation** — the opto only breaks the signal ground loop and blocks common-mode transients. Real isolation requires: remove R29, feed J11–J26 pin 1 from a separate field 12 V, and keep the field 0 V off the board. Document this on the silkscreen: `FLD 12V — ISOLATED FEED ONLY` next to R29.

---

## 4.6 Thermal management

### ULN2803ADWR — the hot spot

| Condition | Per device | θJA | Rise | Tj @ 50 °C ambient |
|---|---|---|---|---|
| 4 motors × 300 mA, bare SOIC-18W | 1.2 W | ≈ 60 °C/W | 72 °C | **122 °C** — at the 125 °C limit |
| + 2 cm² 1 oz pour on collector pins | 1.2 W | ≈ 48 °C/W | 58 °C | 108 °C |
| + pour + 6 vias to bottom pour + 2 oz Cu | 1.2 W | ≈ 40 °C/W | 48 °C | 98 °C |
| Firmware limits to 4 motors simultaneous | 0.6 W/device | 40 °C/W | 24 °C | 74 °C |

VCE(sat) assumption: 1.0 V per channel at 150 mA (datasheet 0.9 V typ at 100 mA, 1.1 V at 200 mA), 2 channels per motor, 300 mA per motor.

Layout actions:
1. **Pour on the collector pins (11–18)**: 2 × 25 × 12 mm of copper on the top layer, connected to pins 11–18 with 0.5 mm necks. The collectors are the heat source, so this copper must touch the collector pads — not the GND pad.
2. **No vias in the collector copper.** The collector node sits at up to 12 V when the channel is off and 0.9 V when on; a via there would short to the bottom GND plane. The collector pour therefore only spreads heat laterally and into the leads, which is still the dominant path for a SOIC-18.
3. **Separate GND thermal island**: a top-layer GND island butting the pin-9 end of the package, 10 × 8 mm, with 6 × 0.3 mm vias down to the bottom pour. It cools the package's ground lead and the board underneath without touching any collector.
4. 2 oz copper on the bottom if the enclosure is sealed and ambient > 45 °C.
5. Firmware interlock: limit to **4 motors energised simultaneously** unless a duty-cycle/thermal model is implemented. This is free and doubles the margin.
6. If the product must run all 8 continuously at 50 °C ambient, a clip-on SOIC-18 heatsink or a MOSFET stage (2 × TBD62083 or discrete AO3400 + flyback) is the correct answer. That is the point where this package stops being adequate.

### Other thermal points

| Part | Dissipation | Action |
|---|---|---|
| D2 SS34 (reverse diode) | 1.4 W at 2.8 A | 150 mm² pour on **both** pads, or fit SS54. This is the second-hottest part on the board. |
| U2 AMS1117 | 0.61 W | 200 mm² pour on the tab. **The tab is `+3V3`, not GND** — the classic SOT-223 mistake is to flood the tab into the ground plane. |
| U1 XL1509 | 0.6 W | GND pour under pins 5–8, 4 vias |
| R11–R26 | 0.145 W each @ 14.4 V | 1206 package, 2 mm pad-to-pad spacing so heat is not shared |

---

## 4.7 KiCad board setup

**Board Setup ▸ Design Rules ▸ Constraints**

| Constraint | Value |
|---|---|
| Minimum track width | 0.25 mm |
| Minimum clearance | 0.25 mm |
| Minimum via diameter / drill | 0.6 mm / 0.3 mm |
| Minimum through hole | 0.3 mm |
| Copper to board edge | 0.5 mm |
| Hole to hole | 0.5 mm |
| Solder mask clearance | 0.10 mm |
| Minimum silkscreen text height / thickness | 1.0 mm / 0.15 mm |
| Courtyard clearance | 0.25 mm |

**Net classes** (Board Setup ▸ Net Classes, then assign by pattern):

| Class | Track | Clearance | Patterns |
|---|---|---|---|
| `Default` | 0.25 | 0.25 | `*` |
| `PWR_12V` | 1.50 | 0.50 | `+12V`, `FLD_12V` |
| `PWR_5V` | 0.50 | 0.30 | `+5V` |
| `PWR_3V3` | 0.40 | 0.30 | `+3V3` |
| `MOTOR` | 0.60 | 0.30 | `MOT*`, `M*_DRV` |
| `FIELD` | 0.30 | 0.50 | `FL*`, `OPT*_K` |
| `I2C` | 0.30 | 0.25 | `SDA`, `SCL` |

**Custom rules** (Board Setup ▸ Custom Rules — verify syntax against your KiCad version):

```
(rule "12V trunk"
  (constraint track_width (min 1.5mm))
  (condition "A.NetName == '+12V'"))

(rule "motor return"
  (constraint track_width (min 0.6mm))
  (condition "A.NetName == 'MOT*'"))

(rule "field side spacing"
  (constraint clearance (min 0.5mm))
  (condition "A.NetName == 'FL*'"))
```

**Antenna keep-out** — `Place ▸ Rule Area` on both layers over the antenna footprint:
- keep out: tracks, vias, pads, copper pour, footprints
- polygon: 13 mm × 16 mm starting at the module's antenna end
- also add a 3 mm `no component` strip around it

---

## 4.8 DFM notes for Indian fabs

| Item | Requirement | Note |
|---|---|---|
| Layers / thickness | 2 / 1.6 mm | standard, no premium |
| Min track / space | 0.25 / 0.25 mm | most fabs do 0.15; you are safe |
| Min drill | 0.3 mm | vias 0.6/0.3 |
| Annular ring | ≥ 0.15 mm | terminal blocks get 0.25 mm |
| Terminal block drill | 1.3 mm PTH, 2.4 mm pad | 24 × 2-pole + 1 × 4-pole |
| Surface finish | HASL-LF | ENIG only if you need planarity (you do not) |
| Soldermask | green LPI both sides, white silk | |
| Fiducials | 3 × 1.0 mm copper, 2.0 mm mask opening, 5 mm from edges | required for pick-and-place |
| Panel | 2-up, 5 mm rails, V-score or 3 mm mouse bites | 170 × 100 fits a standard 18 × 24 panel 2-up |
| Copper balance | ≥ 30 % on each layer | add a thieving hatch if the bottom pour is sparse |

**Assembly order that avoids rework**
1. Bottom side (if any) → reflow → flip.
2. Top side SMD: U1, U2, U3, U4, U5, U6, U7, U8–U11, passives → reflow.
3. Inspect U3's 6 bottom pads for voids — this is the #1 field failure on ESP-12F boards.
4. THT: terminals, headers, switches → wave or hand solder.
5. Do **not** wash the board after fitting the HC-SR04 connector (JST-XH is not sealed).

---

## 4.9 Layout review checklist

- [ ] Antenna keep-out: no copper on **either** layer, 13 × 16 mm, module overhangs the edge.
- [ ] `SW_NODE` loop (U1 pin 2 → L1 → D3 → C4 → U1 GND) under 200 mm², and C4's return goes to U1's GND pins, not to the far side of the pour.
- [ ] `+12V` trunk ≥ 1.5 mm from J1 to U1 and to the ULN `COM` pins.
- [ ] ULN2803 pin 9 pour/neck ≥ 0.8 mm; four devices' return paths do not cross the ESP or opto area.
- [ ] AMS1117 tab pour is `+3V3` and isolated from the GND pour (check DRC for a short).
- [ ] D2 pads have ≥ 150 mm² copper each.
- [ ] Isolation moat is uninterrupted for its full length on both layers.
- [ ] Opto field pins face the field terminals; logic pins face U5. No field trace crosses the moat.
- [ ] I²C runs < 100 mm total, ≥ 2 mm from any motor trace, no parallel run > 20 mm.
- [ ] 16 field `1.2 k` resistors are in the field zone (they dissipate 0.1 W each and should not heat the optos).
- [ ] Every terminal block has a silkscreen channel number and a `+`/`−` or `M+`/`M−` marker.
- [ ] `J2` pin 1 marked `3V3 OUT` — back-powering the AMS1117 from a USB-TTL adapter is the most likely way to destroy this board.
- [ ] DRC: 0 errors, 0 unconnected, 0 courtyard overlaps.
