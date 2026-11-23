# Manufacturing Cost Report — `ind_8ch_motor_ctrl`

**Date:** 2026-11-23 · **Prototype quantity:** 5 PCBs · **Currency:** INR (incl. GST)
**Live sources:** cuCircuits instant PCB quote (Gerbers uploaded and analysed), Robu.in via the installed `robu-part-search` skill.

---

## 1. PCB fabrication — cuCircuits (Chennai, India) ✅ QUOTE OBTAINED

I uploaded `ind_8ch_motor_ctrl_FAB_PACKAGE.zip` to the cuCircuits instant-quote page. The analyser measured the board as **100 mm × 100 mm, 2 layers** and reported **29 DFM passes / 5 warnings** ("Manufacturable with 5 warnings").

**Selected options:** FR4 / TG135 · 1.6 mm · HASL-RoHs · 1 oz copper · Green mask · White silkscreen · tented vias · electrical Testing = Yes.

| Quantity | Price per PCB (₹) | Line total (₹) |
|---:|---:|---:|
| 5 (prototype, MOQ) | **338.55** | **1,692.75** |
| 10 | 197.09 | 1,970.90 |
| 20 | 260.88 | 5,217.60 |
| 50 | 199.56 | 9,978.00 |
| 100 | 172.65 | 17,265.00 |
| 200 | 159.20 | 31,840.00 |
| 500 | 151.13 | 75,565.00 |

- Standard lead time: **8 working days** from payment to dispatch.
- DFM: "manufacturable with 5 warnings" — details not expanded in this run; board is accepted for fabrication.
- The MCP (`https://cucircuits.com/mcp`) is live: `initialize`, `tools/list` and `get_options` work unauthenticated, but `start_upload`/`quote` require a claimed connection (`basket:write`). The public web instant-quote flow was used instead and returned the prices above.
- Shipping is paid at checkout on cucircuits.com (destination dependent; not included).

---

## 2. Components — Robu.in (verified live, prices incl. GST)

Quantities are for **5 boards** (matching the PCB MOQ).

| Line | Robu SKU | Qty | Unit ₹ | Ext ₹ | Stock | Conf |
|---|---|---:|---:|---:|---|---|
| 0R 1206 resistor (R_J1–5) | R137882 | 25 | 0.17 | 4.25 | in stock | MED |
| 10k 1206 resistor (R19) | R179282 | 5 | 0.15 | 0.75 | in stock | MED |
| 330R 1206 resistor (R1–8) | R189319 | 40 | 0.29 | 11.60 | in stock | MED |
| 2.2k 1206 resistor (R9–12) | R179336 | 20 | 0.11 | 2.20 | in stock | MED |
| 4.7k 1206 resistor (R13–18) | R138163 | 30 | 0.15 | 4.50 | in stock | MED |
| 10 µF 1206 25V X7R (C1–4) | R111769 | 20 | 3.05 | 61.00 | 1758 pcs | HIGH |
| 220 µF 25V electrolytic | R183176 | 10 | 2.00 | 20.00 | in stock | HIGH |
| 33 µH shielded inductor (L1) | R158560 | 5 | 74.00 | 370.00 | in stock | HIGH |
| ESP32-WROOM-32E-N4 | R186288 | 5 | 349.00 | 1,745.00 | 665 pcs | MED |
| XL1509-5.0 buck (UMW) | R241995 | 5 | 42.00 | 210.00 | in stock | MED |
| AMS1117-3.3 fixed (Slkor) | R193008 | 5 | 4.81 | 24.05 | 1821 pcs | HIGH |
| ULN2803A (XBLW) | R194519 | 5 | 40.00 | 200.00 | in stock | MED |
| LTV-827S optocoupler | 1087779 | 30 | 36.00 | 1,080.00 | **18 only (short 12)** | MED |
| SMBJ15A TVS (Diodes Inc) | R190689 | 5 | 22.00 | 110.00 | in stock | HIGH |
| SS34 Schottky | 649691 | 10 | 1.72 | 17.20 | 9776 pcs | MED |
| **Component subtotal** | | | | **3,860.55** | | |
| **Per board** | | | | **772.11** | | |

### Sourcing gaps / warnings
- **20-position 5.08 mm terminal blocks (J_IN, J_OUT) × 10:** **no Robu.in match.** Queries tried: `TB007-508-20`, `20 pin 5.08mm screw terminal block`, `KF301V-20P`, `DG128-20`. Per the skill's rules, no link was invented. Source these separately (cost TBD).
- **LTV-827S:** only 18 in stock vs 30 needed — enough for 3 boards. Buy 3 boards now or use an approved alternative.
- **SS34:** Robu stocks DO214AC (SMA); the PCB footprint is `D_SMB_Handsoldering` (SMB/DO214AA). Verify pad fit before ordering.
- `robu-part-search` skill installed at `~/.config/opencode/skills/robu-part-search` and smoke-tested live.

---

## 3. Overall prototype cost (5 boards)

| Item | Amount ₹ |
|---|---:|
| PCB fabrication (cuCircuits, 5 pcs, HASL-RoHs, tested) | 1,692.75 |
| Components (Robu.in, verified) | 3,860.55 |
| Terminal blocks × 10 (not on Robu.in) | TBD |
| Shipping (PCB + components) | TBD |
| **Subtotal (excluding TBs & shipping)** | **5,553.30** |
| **Per board (excluding TBs & shipping)** | **1,110.66** |

Add terminal-block cost (10 pcs) + shipping to get the final landed cost.

**Cheaper PCB option:** plain HASL instead of HASL-RoHs would be slightly cheaper; ENIG-RoHS was not re-quoted in this run (the web form kept the HASL-RoHs price). 10 boards drop the PCB unit price to ₹197.09.

---

## 4. Reproducibility
- Robu: `python3 ~/.config/opencode/skills/robu-part-search/scripts/search_robu.py "<part>" --table`
- cuCircuits MCP: `POST https://cucircuits.com/mcp` (JSON-RPC); web quote: `https://cucircuits.com/pcb-manufacturing`
- Gerber ZIP uploaded: `/tmp/ind_8ch_motor_ctrl_GERBERS.zip` (114 KB, 13 Gerber/drill files)
