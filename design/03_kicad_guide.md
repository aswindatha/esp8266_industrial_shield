# Part 3 — KiCad 8 / 9 Schematic Generation Procedure

> **Superseded in part.** Apply the ECOs in [`05_layout_execution_plan.md`](05_layout_execution_plan.md) §0 before drawing: J2 = ultrasonic, J27 = UART, U12 + C20 added, RN7/RN8 added, H1/H2/TP1–TP3 deleted, GND split into `GND`/`GND_FIELD` with R31, D1 = SMAJ15A, D2 = SS54.

Everything below applies to **KiCad 8.0 and 9.0** (identical menus; 9.0 only adds features we do not use). Work through the steps in order — the netlist in Part 1 is what you should end up with.

---

## 3.1 Project and sheet structure

1. **File ▸ New Project** → `MotorIO.kicad_pro` in a folder named `hardware/`.
2. In the root schematic (`MotorIO.kicad_sch`), set the page to **A3** (`File ▸ Page Settings`, paper A3, landscape). The 16-channel sheet will not fit on A4.
3. Add six child sheets with **Place ▸ Add Sheet** (name / file):

| Sheet name | File | Page size |
|---|---|---|
| `POWER` | `power.kicad_sch` | A4 |
| `MCU` | `mcu.kicad_sch` | A3 |
| `IO_EXPAND` | `ioexp.kicad_sch` | A4 |
| `MOTOR_DRV` | `motor_drv.kicad_sch` | A3 |
| `FIELD_IN` | `field_input.kicad_sch` | A2 |
| `ULTRA` | `ultrasonic.kicad_sch` | A4 |

4. Fill in the title block on every sheet: title, revision, date, company, and `Sheet: <n>/7`.

> **Hierarchy choice.** Strict hierarchy means every cross-sheet net appears twice (hierarchical label inside + sheet pin outside). For 24 bus nets (`M1_DRV`…`M8_DRV`, `OPT1_COL`…`OPT16_COL`) that is 48 extra clicks and a common source of wiring mistakes. The recommended pattern here is **sheets as drawing frames + global labels for inter-sheet nets**. Use hierarchical labels only if your team requires a strict sheet-pin review.

---

## 3.2 Symbols that are *not* in the stock libraries

Three parts need a custom symbol. Build them once in a project library `MotorIO.kicad_sym` (`File ▸ New Library`), then use them like any stock symbol.

### XL1509-5.0E1 (8-pin SOP)

| Pin | Name | Electrical type |
|---|---|---|
| 1 | VIN | power_in |
| 2 | SW | output (power_out causes ERC noise — use **output**) |
| 3 | FB | input |
| 4 | EN | input |
| 5 | GND | power_in |
| 6 | GND | power_in |
| 7 | GND | power_in |
| 8 | GND | power_in |

Graphic: rectangle 400×500 mil, VIN top-left, SW right, GND bottom, FB/EN left. Hide pins 5–8 behind pins named `GND` (stacked pins — KiCad merges them if they share a name).

### PS2501-4 (16-pin quad optocoupler) — pinout per the Renesas datasheet

| Pin | Name | Type | Pin | Name | Type |
|---|---|---|---|---|---|
| 1 | A1 | passive | 9 | E4 | passive |
| 2 | K1 | passive | 10 | C4 | passive |
| 3 | A2 | passive | 11 | E3 | passive |
| 4 | K2 | passive | 12 | C3 | passive |
| 5 | A3 | passive | 13 | E2 | passive |
| 6 | K3 | passive | 14 | C2 | passive |
| 7 | A4 | passive | 15 | E1 | passive |
| 8 | K4 | passive | 16 | C1 | passive |

Verify: the isolation-test note in the datasheet shorts **1–8 together and 9–16 together**, and anodes are **1,3,5,7** with cathodes **2,4,6,8**. Draw four independent opto units (unit A–D) so each channel is a separate symbol instance.

### 4× isolated resistor array (RN1-RN6)

Use the stock `Device:R_Pack04_Split` symbol — four units, pins 1/8, 2/7, 3/6, 4/5. That is exactly the YC164 internal wiring.

### Everything else is stock

| Ref | KiCad symbol | KiCad footprint |
|---|---|---|
| U2 | `Regulator_Linear:AMS1117-3.3` | `Package_TO_SOT_SMD:SOT-223-3_TabPin2` |
| U3 | `RF_Module:ESP-12E` | `RF_Module:ESP-12E` (verified: 22 pads, 6 bottom GND) |
| U4/U5 | `Interface_Expansion:MCP23017-E_SO` | `Package_SO:SOIC-28W_7.5x17.9mm_P1.27mm` |
| U6/U7 | `Transistor_Array:ULN2803A` | `Package_SO:SOIC-18W_7.5x11.6mm_P1.27mm` |
| U8–U11 | custom `PS2501-4` | `Package_DIP:DIP-16_W7.62mm` |
| D1 | `Device:D_TVS` | `Diode_SMD:D_SMA` |
| D2/D3 | `Device:D_Schottky` | `Diode_SMD:D_SMA` |
| D4–D19 | `Device:D` | `Diode_SMD:D_SOD-123` |
| L1 | `Device:L` | `Inductor_SMD:L_8x8mm` (check vendor drawing) |
| Q (none) | — | — |
| J1/J3–J26 | `Connector:Conn_01x02` | `TerminalBlock:TerminalBlock_bornier-2_P5.00mm` |
| J2 | `Connector:Conn_01x04` | `TerminalBlock:TerminalBlock_bornier-4_P5.00mm` |
| J27 | `Connector:Conn_01x04` | `Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical` |
| SW1/SW2 | `Switch:SW_Push` | `Button_Switch_SMD:SW_SPST_TL3342` |
| F1 | `Device:Polyfuse` | `Fuse:Fuse_1812_4532Metric` |
| TP1–TP6 | `Connector:TestPoint` | `Connector:TestPoint` (1.5 mm pad) |

> Library IDs occasionally shift between KiCad releases. If a name does not resolve, use the library browser filter on the value — the footprint geometry is what matters.

---

## 3.3 Power symbols and PWR_FLAG placement

Power symbols are **global** in KiCad, so a `+12V` placed on any sheet connects to `+12V` on every other sheet.

| Rail | Power symbol | PWR_FLAG needed? | Why |
|---|---|---|---|
| `+12V` | `power:+12V` | **Yes**, one, on the power sheet | Driven only by J1/F1/D2 (all passive) |
| `GND` | `power:GND` | **Yes**, one, on the power sheet | All GND pins are `power_in`; nothing is `power_out` |
| `+5V` | `power:+5V` | **Yes**, one, on the power sheet | L1 is passive, XL1509 SW is a switch node |
| `+3V3` | `power:+3V3` | **No** — U2 `VO` is `power_out` | Add only if ERC complains |
| `FLD_12V` | local label, not a power symbol | No | Every pin on it is passive |
| `VIN_RAW` / `VIN_A` | local labels | No | Passive only |

Rules of thumb:
- **Exactly one** PWR_FLAG per rail that needs it. Two `power_out` pins on one net is an ERC "conflict" error.
- Do **not** create a custom `+12V` symbol; use the stock one so the global net name stays canonical.
- Do not name a net `12V` or `3.3V` — use `+12V` / `+3V3` so the stock symbols and the labels agree.

---

## 3.4 Net label vocabulary

Copy this table into `docs/net_names.md` and keep it authoritative. **Avoid `/` in net names** — KiCad reads it as a hierarchy separator.

| Domain | Label | Style | Scope |
|---|---|---|---|
| Power | `+12V`, `+5V`, `+3V3`, `GND` | power symbol | global |
| Buck switch | `SW_NODE` | local | power sheet only |
| Input | `VIN_RAW`, `VIN_A` | local | power sheet only |
| Isolation | `FLD_12V` | local | field sheet only |
| Motor drive | `M1_DRV` … `M8_DRV` | **global label** | ioexp ↔ motor_drv |
| Motor return | `MOT1_N` … `MOT8_N` | local | motor_drv only |
| Opto logic | `OPT1_COL` … `OPT16_COL` | **global label** | field ↔ ioexp |
| Opto LED | `OPT1_K` … `OPT16_K` | local | field sheet only |
| Field wire | `FL1_N` … `FL16_N` | local | field sheet only |
| I²C | `SDA`, `SCL` | global label | mcu ↔ ioexp |
| UART | `TXD0`, `RXD0` | global label | mcu only |
| Ultrasonic | `TRIG`, `ECHO`, `ECHO_RAW` | global / local | mcu ↔ ultra |
| Expander spare | `EXP_B0` … `EXP_B7` | global label | ioexp ↔ mcu (H1) |
| Expander reset | `EXP1_RST`, `EXP2_RST` | local | ioexp only |

Global label shape: use **bidirectional** for `SDA`/`SCL`, **input** for signals entering a sheet, **output** for signals leaving. Shape is cosmetic, but it makes the ERC report readable.

---

## 3.5 Sheet-by-sheet construction

### Power sheet (`power.kicad_sch`)

1. Signal flow left → right: J1, F1, D1, D2, then U1 buck, then U2 LDO.
2. Place J1 and F1 first, wire `VIN_RAW`.
3. D1 across the rail **after** the fuse (so the fuse protects the TVS), D2 in series.
4. U1: pin 1 `+12V`, pin 2 `SW_NODE`, pin 3 `+5V`, pin 4 `+12V`, pins 5–8 `GND`.
   **Pin 3 (FB) goes to the output node**, not to a divider — the `-5.0` variant is fixed.
5. L1 between `SW_NODE` and `+5V`; D3 cathode on `SW_NODE`, anode on `GND`; C4/C5 on `+5V`.
6. U2: pin 3 `+5V`, pin 2 `+3V3`, pin 1 `GND`. Put C6 on the input, C7+C8 on the output.
7. Place the three PWR_FLAGs now, before leaving the sheet.
8. Add a text note: *"SW_NODE loop < 200 mm² — C4 return to U1 pin 5-8 ground directly."*

### MCU sheet (`mcu.kicad_sch`)

1. U3 in the centre, antenna pointing **right** in the drawing (it will point off the top edge in the layout).
2. Strapping resistors immediately around the module, each with a text note:
   - R3 `GPIO0` pull-up + SW1 to GND (label "FLASH — hold during reset")
   - R4 `GPIO15` pull-down ("must be LOW at boot")
   - R5 `GPIO2` pull-up ("must be HIGH at boot")
   - R6 `TRIG`/GPIO12 pull-down ("MTDI strap — must be LOW at boot")
3. R1/C12 on EN, R2/C18/SW2 on RST.
4. C10/C11 drawn **as a pair touching the VCC pin**, with a note "≤ 3 mm from pad 8".
5. J2 (4-pin) and H2 (1×6) on the left, H1 on the right.
6. TP1–TP6 at the edges with visible labels.

### Expander sheet (`ioexp.kicad_sch`)

1. U4 (motors) on the left, U5 (inputs) on the right.
2. Draw all 8 `Mn_DRV` global labels on U4 bank A in order; draw U4 bank B to `EXP_B0..B7`.
3. Draw U5 bank A = `OPT1_COL..OPT8_COL`, bank B = `OPT9_COL..OPT16_COL`.
4. Address straps: U4 pins 15/16/17 → GND (0x20); U5 pin 15 → +3V3, pins 16/17 → GND (0x21).
5. R9/R10 on RESET, C13/C14 decoupling.
6. Place **no-connect flags (X)** on U4 and U5 pins 11, 14, 19, 20.

### Motor sheet (`motor_drv.kicad_sch`)

1. U6 top, U7 bottom. Inputs on the left, outputs on the right.
2. For each motor, join the two input pins with a short wire and attach the `Mn_DRV` label **once** — this guarantees the pair can never diverge.
3. Same on the output side: join the two collector pins, then one wire to `MOTn_N` and J(n+2).2.
4. `COM` (pin 10) of both devices to `+12V`, each with a 100 nF (C15/C16) to GND.
5. `GND` (pin 9) of both to `GND`, with a note "1.2 A per device — 0.8 mm + pour".
6. RN5/RN6 between the drive labels and GND.

### Field input sheet (`field_input.kicad_sch`)

1. Draw **one** channel completely, check it, then replicate:
   ```
   FLD_12V ──┬── A1 ─┐
             │       │  U8
             │  K1 ──┼── OPTn_K ──┬── R(1.2k) ── FLn_N ── J pin 2
             │       │             │
             └── K ──┘           D (1N4148)   A on OPTn_K, K on FLD_12V
   ```
2. Select the channel group and use **Ctrl+C / Ctrl+V**, dragging each copy to the next 10 mm column. Re-annotate afterwards (`Tools ▸ Annotate Schematic`).
3. Keep the four devices as four columns of four channels (U8 ch1-4, U9 ch5-8, U10 ch9-12, U11 ch13-16).
4. Draw a **dashed graphical line** down the middle of every opto package and label it `ISOLATION BARRIER`. This is the visual contract for the layout.
5. R29 (`0R`) between `+12V` and `FLD_12V`, with the note *"remove + feed FLD_12V from the field supply for true galvanic isolation"*.

### Ultrasonic sheet

Straight left-to-right: J27 → R27 → node `ECHO` → R28 → GND, node `ECHO` to a global label, `TRIG` global label from J27 pin 2. Add a note "5 V echo → 3.33 V at GPIO14".

---

## 3.6 Annotation, footprints, ERC

1. **Tools ▸ Annotate Schematic** — annotate by sheet, "use first free number", then re-annotate back-annotation off.
2. **Tools ▸ Assign Footprints** — use the table in 3.2. Set the 5 mm terminals to `TerminalBlock_bornier-2_P5.00mm` and confirm the drill is 1.3 mm.
3. **Inspect ▸ Electrical Rules Checker** with these settings:
   - `Test for footprint conflicts` **on**
   - `Check for unconnected pins` **on**
   - Severity: `Power pin not driven` = error; `Label not connected` = error; `Pins of type power output and power output` = error.
4. Expected and acceptable ERC results after the power flags are in place:
   - 0 errors.
   - Warnings only for the 8 explicit no-connect pins (they are flagged as NC, so they should not warn at all).
5. **File ▸ Export ▸ Netlist** (KiCad format, `.net`) and diff it against `NETLIST.csv`. A quick way: open the `.net` file and check that the net count is **97**.

---

## 3.7 Schematic review checklist (print this)

- [ ] Every `+12V` / `+5V` / `+3V3` / `GND` symbol is the stock one, no custom power symbol.
- [ ] One PWR_FLAG each on `+12V`, `GND`, `+5V` — and nowhere else.
- [ ] U1 pin 3 (FB) wired to `+5V`, not left floating.
- [ ] U2 pin 2 and the SOT-223 tab are the same net (`+3V3`).
- [ ] Both ULN2803 `COM` pins on `+12V`; both `GND` pins on `GND`.
- [ ] All 8 `Mn_DRV` pairs joined **at the symbol**, not split by a wire stub.
- [ ] `R6` (10 k) present on `TRIG` — this is the GPIO12 strap guard.
- [ ] `RN5`/`RN6` present — without them the motors twitch at power-up.
- [ ] D4–D19 orientation: **cathode to `FLD_12V`**, anode to the `OPTn_K` node.
- [ ] 1.2 k resistors are **1206**, not 0805.
- [ ] `R29` populated (default) or intentionally removed for isolated field supply.
- [ ] Antenna note on the MCU sheet: "keep-out 13 × 16 mm, no copper any layer".
- [ ] All 8 NC pins marked with a no-connect flag.
- [ ] Sheet count 7/7, all title blocks filled.

---

## 3.8 Firmware bring-up sequence implied by this schematic

1. Set U5 `IODIR` = `0xFF` (inputs) and enable `GPPU` (internal 100 k) before reading.
2. Set U4 `IODIR` = `0x00`, `OLAT` = `0x00` **before** enabling the output drivers (`IODIR` write is the last step) — the hardware pull-downs cover the boot window, but make the first write explicit.
3. Read `OPTn_COL`: `1` = field line open, `0` = field line energised.
4. Never drive `TRIG` before the first `delay(200)` after reset, so the GPIO12 strap is sampled clean.
