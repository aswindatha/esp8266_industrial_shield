# Engineering Review — findings, pin contention and timing

Severity: **C** = will not work / will fail in the field, **H** = fix before release, **M** = fix if the environment is harsh, **L** = informational.

---

## C1 — A PCF8574 cannot drive a ULN2803. This is the one blocking defect in the stated architecture.

| Parameter | Value |
|---|---|
| PCF8574 high-level output | quasi-bidirectional, **100 µA** current source (NXP datasheet) |
| ULN2803 input current at V_I = 3.3 V | (3.3 − 1.4) / 2.7 k = **0.70 mA** |
| Ratio | **7 : 1** |

The expander is asked to hold the Darlington input above its 1.4 V threshold with a 100 µA source while the input demands 700 µA. The node collapses to ≈ 1.4 V, the Darlington sits at the edge of conduction, V_CE stays high and the motor sees a fraction of its current while the package dissipates the difference. It will look like "weak motors that get hot", and it will get worse as the parts warm up.

This is a drive-strength contention, not a logic-level one: 3.3 V is a perfectly good logic level for a ULN2803.

**Resolved in this design:** two `MCP23017-E/SO` replace four `PCF8574T`. Push-pull outputs are rated 25 mA, 35× the requirement, and the part count drops from 4 ICs to 2 with 8 spare I/O left over.

If you must keep the PCF8574 (stock, price), insert a `74HCT244` (or 74AHCT244) between the motor expander and the ULN2803 inputs, powered from 5 V. HCT inputs accept 3.3 V (V_IH = 2.0 V) and the outputs source the 0.9 mA the ULN wants at 5 V. Do **not** try to fix it with a 4.7 k pull-up — the pull-up would hold the ULN input partially on when the expander pulls low.

---

## C2 — GPIO12 is a strapping pin and the ultrasonic trigger is wired straight to it

GPIO12 is **MTDI**, sampled at reset to choose the internal flash regulator: LOW = 3.3 V flash, HIGH = 1.8 V flash. Get it wrong and the ESP8266 boot-loops before it ever reaches your code.

The HC-SR04 `Trig` line is the only external connection on that pin. Every HC-SR04 clone has a different input structure; some fit a pull-up on Trig, and long wiring picks up the motor switching. A 3.3 V-only sensor interface also means the sensor's 5 V CMOS input (V_IH ≈ 3.5 V) is being driven **below** its own specification — it usually works, and it is not guaranteed.

**Resolved:** `R6` 10 k pull-down on `TRIG`, fitted at the module, and the trace kept under 25 mm. **Verify** on the first article: power the board with the sensor disconnected and with it connected, and confirm the ESP boots in both cases. If your sensor batch has a pull-up on Trig, add a 74HCT1G34 buffer instead of the direct connection.

---

## C3 — Motors twitch (or run) during power-up and after every reset

`MCP23017` powers up with `IODIR = 0xFF` — every port is an input, high-Z. For the ~200 ms until the ESP8266 boots and writes `IODIR`, the eight ULN2803 inputs float. A floating Darlington input is an antenna next to 2.4 A of switching current: it will turn on.

**Resolved:** `RN5`/`RN6`, 10 k pull-downs on all eight `Mn_DRV` lines. They cost 16 ₹ and remove the fault class entirely. Do not omit them because "firmware sets the pins early" — the boot ROM runs before your firmware.

---

## H1 — `SMAJ28A` clamps above the buck converter's absolute maximum

| Part | Clamping voltage | Downstream limit |
|---|---|---|
| SMAJ28A | **45.4 V** at 8.8 A | XL1509 V_IN abs max = **40 V** |
| SMAJ18A | 29.2 V at 13.7 A | OK |
| SMAJ15A | 24.4 V at 16.4 A | OK, and 15 V standoff still covers a 13.8 V rail |

A surge that the TVS is supposed to absorb will drive the buck input above 40 V and destroy it — the protector and the protected part fail together. Change to **SMAJ15A** for a 12 V adapter input, or SMAJ18A if the input can reach 18 V. Keep SMAJ28A only if the source is genuinely capable of 28 V (automotive load dump), and in that case use a 60 V-rated buck instead.

---

## H2 — D2 (SS34, reverse polarity) is the second-hottest part on the board

2.8 A × 0.5 V = **1.4 W** in an SMA. θ_JA ≈ 75 °C/W with minimal copper → 105 °C rise → T_j ≈ 130 °C at 25 °C ambient. It is also rated 3 A average while carrying 2.8 A continuous — 93 % of rating.

**Options, in order of preference:**
1. `SS54` (5 A) + 150 mm² pour on both pads — cheapest change, buys rating margin and lower V_F.
2. P-channel MOSFET reverse protection (`DMP3098L` or `IRF9540N`): ≈ 20 mΩ × 2.8 A = 56 mW instead of 1.4 W. Costs one part and a gate zener.
3. Keep SS34 and add the copper + a firmware duty limit.

---

## H3 — 0.25 mm is a fabrication floor, not a power rule

The stated "minimum 0.25 mm trace/space" is the process minimum. At 1 oz and 10 °C rise, 0.25 mm carries only **0.88 A**. The 12 V trunk carries 2.8 A.

| Current | Width needed (1 oz, 10 °C) |
|---|---|
| 0.3 A | 0.10 mm |
| 1.0 A | 0.30 mm |
| 2.0 A | 0.76 mm |
| 3.0 A | 1.37 mm |

Use **1.5 mm** for `+12V`, 0.8 mm + pour for each ULN2803 ground return, 0.5 mm for `MOTn_N`. See Part 4 §4.2.

---

## H4 — "Isolated inputs" are only isolated if you remove R29

With `R29` fitted (default) the field LED anodes are tied to the board's own `+12V`. If the field switches return to the same PSU 0 V, current flows through the supply and the opto only breaks the *signal* loop. That is useful (it kills ground loops and blocks common-mode transients) but it is **not** galvanic isolation, and it will not pass a hipot test.

Real isolation = remove R29, feed `J11–J26` pin 1 from a separate field 12 V, and keep the field 0 V off the board. The layout moat in Part 4 §4.5 supports either build with no PCB change. Put this in the product manual — customers will assume "optocoupler" means "isolated" and wire it accordingly.

---

## H5 — 1.2 k / 0805 would be over-dissipated at 14.4 V

I = (14.4 − 1.2)/1200 = 11 mA; P = I²R = **145 mW**. An 0805 is 125 mW. At nominal 12 V it is 97 mW — still 78 % of rating.

**Resolved:** R11–R26 are specified as **1206, 0.25 W**. If you must use 0805, change to 1.5 k (7.2 mA, 78 mW) — still 6× the CTR requirement.

---

## H6 — I²C rise time at 400 kHz with 4.7 k pull-ups

t_r = 2.2 · R · C_b. Fast-mode limit is 300 ns.

| R_pull | Max bus capacitance at 400 kHz | Max at 100 kHz |
|---|---|---|
| 4.7 k | 29 pF | 97 pF |
| 2.2 k | 62 pF | 207 pF |

The bus here is two ICs and ≈ 40 mm of trace, so C_b ≈ 20–25 pF. 4.7 k works at 400 kHz on paper with almost no margin, and comfortably at 100 kHz. The MCP23017 supports 400 kHz; the PCF8574 does not (100 kHz max).

**Decision:** run the bus at **100 kHz**, keep 4.7 k. 16 input bits + 8 output bits take ≈ 0.6 ms per full cycle — 1.6 kHz refresh, far more than any mechanical sensor needs. If you later need 400 kHz, drop to 2.2 k and re-measure the rise time with a scope.

---

## H7 — Software I²C + WiFi: the timing is legal but not clean

The ESP8266 has **no hardware I²C** — `Wire` bit-bangs on GPIO4/5. Each byte takes ≈ 90 µs at 100 kHz with interrupts disabled. That is legal for the bus (the MCP23017 does not need clock stretching) but it adds up to ~0.5 ms of WiFi latency per transaction.

Consequences:
- Do not call the expanders from a timer ISR.
- Batch the reads: one 2-byte read from U5 covers all 16 inputs.
- The PCF8574 cannot clock-stretch, so if you ever switch back to it, a WiFi interrupt landing mid-byte still produces valid timing — the bus just runs slower. No fix required, but do not raise the clock to compensate.

---

## H8 — Optocoupler speed limits what these inputs can ever do

PS2501 t_r/t_f = 3 µs / 5 µs typical, with a 10 k pull-up the fall is opto-dominated. Add the I²C poll interval and the practical ceiling is **≈ 500 Hz–1.6 kHz** for the whole bank.

This is fine for switches, floats, proximity and limit switches. It is **not** usable for encoders, flow meters or anything above a few hundred hertz. If you need pulse counting, route that one signal to a spare ESP GPIO (GPIO13 is free) with a hardware interrupt and keep the opto bank for slow signals.

---

## M1 — ULN2803 thermal: fine at 25 °C, marginal at 50 °C

4 motors per device × 300 mA × 1.0 V = 1.2 W, θ_JA ≈ 60 °C/W → 72 °C rise → T_j = 122 °C at 50 °C ambient, 3 °C from the limit. See Part 4 §4.6 for the copper and firmware mitigations, and the point at which a MOSFET stage becomes the right answer.

Paralleling two Darlington channels is **not** current sharing by specification — the datasheet gives no sharing guarantee. At 150 mA per channel against a 500 mA rating there is enough margin that even 70/30 sharing (210 mA) is safe. The real benefit is halved V_CE and spread heat, not extra current capability. Do not parallel channels on a 500 mA-per-motor design without checking this.

---

## M2 — AMS1117 tab is V_OUT, not GND

SOT-223 pin 2 and the tab are the 3.3 V output. A ground pour over the tab is a dead short. Flood the tab with a **3.3 V** pour of ≈ 200 mm² and keep the DRC clearance to the GND plane. This is the single most common layout error on AMS1117 boards, and it usually survives the first power-up because the pour is on the top layer and the short is under the part.

---

## M3 — Buck runs in DCM at this load; that is acceptable but know why

ΔI = (12 − 5) × 5 / (12 × 150 k × 33 µ) = 0.59 A p-p, while the actual load is only ≈ 0.42 A. The converter is discontinuous at light load: efficiency drops a few percent and output ripple rises to ≈ 40 mV — still 0.8 % of 5 V. No action. Do not "fix" it by dropping to 10 µH; that would push the ripple current to 2 A p-p and stress D3.

---

## M4 — UART header back-power

`J2` pin 1 exposes `+3V3` so an adapter can sense the rail. If the adapter also *supplies* 3.3 V, it back-feeds the AMS1117 output, which has no reverse-blocking. `H2` is the recommended programming port (2.54 mm, RST + GPIO0 included). Silkscreen `J2` pin 1 as `3V3 OUT`.

---

## M5 — Keep the TVS downstream of the fuse

D1 sits after F1 so the fuse protects the TVS from a sustained over-voltage. Keep that order; a TVS directly across the connector will fail short and take the supply down with no fuse to clear it.

---

## L1 — Clock and boot timing notes (no defects, just facts to design around)

| Item | Value | Implication |
|---|---|---|
| ESP8266 clock | 26 MHz crystal **inside** the module | Never add an external crystal; never route under the module's crystal area |
| Flash clock | 80 MHz QIO on GPIO6–11 | Those pins are internal to the module — not available, do not try |
| Boot strap sampling | at power-on reset, after V_DD valid | EN RC = 10 k × 100 nF = 1 ms, which guarantees the straps settle after the 3.3 V ramp |
| Boot log baud | 74880 Bd | Your terminal will show garbage at 115200 — expected, not a fault |
| RST pulse | ≥ 200 µs low | SW2 with 100 nF gives ≈ 1 ms — fine |
| `pulseIn` worst case | 30 ms per measurement (HC-SR04 timeout) | Blocks the loop; keep one sensor or use a state machine |
| Soft WDT | 3.2 s default | 16 blocking ultrasonic reads would trip it — another reason for one sensor |
| I²C transaction | 0.6 ms for the whole bank at 100 kHz | 1.6 kHz refresh ceiling |
| Opto propagation | 3–5 µs | Do not poll faster than the opto can settle |

---

## L2 — Creepage is not the constraint at 12 V

IPC-2221 Table 6-1 wants ≈ 0.13 mm at 12 V; IEC 62368-1 wants 0.4 mm clearance / 0.8 mm creepage for functional insulation. A 2 mm moat is 5–15× the requirement and is there for EMI and optional hipot, not compliance. A routed slot is **not** required by either standard at this voltage — treat it as a product decision with a milling cost, not a rule.

---

## L3 — Expander address plan

| Device | A2 A1 A0 | 7-bit address |
|---|---|---|
| U4 | 0 0 0 | 0x20 |
| U5 | 0 0 1 | 0x21 |

If you revert to PCF8574, note that **PCF8574 and PCF8574A have different base addresses** (0x20 vs 0x38) and the same part number prefix in some catalogues. Mixing them on one board produces "device not found" that looks like a wiring fault.

---

## Verification required before you release the Gerbers

| # | Check | Why |
|---|---|---|
| 1 | **PS2501-4 package** — the Robu listing says "PS2501-4" (DIP-16) while the brief says SOIC-16. `PS2501L-4` is the gull-wing SMD version and needs a different footprint. | A wrong footprint is unfixable after fabrication. Measure the part you actually have. |
| 2 | **ESP-12F pin 1** — hover it in KiCad; it must be the pad nearest the antenna on the left edge (`RST`). | The KiCad symbol packs the 6 bottom pads into pins 9–14; a wrong assumption shifts every right-side signal by one. |
| 3 | **ULN2803ADWR vs ULN2803A** — ADWR is the SOIC-18 **wide** body (7.5 mm, `SOIC-18W_7.5x11.6mm_P1.27mm`); the plain ULN2803A is DIP-18 (`DIP-18_W7.62mm`). | Both are sold as "ULN2803"; the footprint does not swap. |
| 4 | **Terminal block mechanical drawing** — 5.00 mm pitch, 1.3 mm pins, body depth vs board edge. | 25 connectors; a 0.5 mm error breaks every one. |
| 5 | **HC-SR04 Trig threshold** — measure V_IH or test-boot with the sensor fitted. | See C2. |
| 6 | **MCP23017 price/stock** in India (≈ ₹180 vs ₹55 for PCF8574). | Decides C1's resolution path. |
| 7 | **SMAJ15A vs SMAJ28A** decision with the actual 12 V source. | See H1. |
| 8 | **Board outline vs enclosure** — antenna overhang needs clearance to any metal. | A metal lid 5 mm above the antenna detunes it. |
