# Per-Board Manufacturing Cost — ind_8ch_motor_ctrl

**Date:** 2026-11-24 · **Currency:** INR incl. GST · **Qty basis:** 5 boards

## 1. Components (Robu.in, verified live, per board)

| Item | Robu SKU | Qty/board | Unit ₹ | Ext ₹ |
|---|---|---:|---:|---:|
| 0R 1206 resistor | R137882 | 5 | 0.17 | 0.85 |
| 10k 1206 resistor | R179282 | 1 | 0.15 | 0.15 |
| 330R 1206 resistor (now 220R in 2L) | R189319 | 8 | 0.31 | 2.48 |
| 2.2k 1206 resistor | R179336 | 4 | 0.12 | 0.48 |
| 4.7k 1206 resistor | R138163 | 6 | 0.15 | 0.90 |
| 10uF 1206 25V X7R | R111769 | 4 | 3.33 | 13.32 |
| 220uF 25V SMD electrolytic | R183176 | 2 | 2.01 | 4.02 |
| 33uH SRR1260-330M | R158560 | 1 | 74.00 | 74.00 |
| ESP32-WROOM-32E-N4 | R186288 | 1 | 349.00 | 349.00 |
| XL1509-5.0 | R241995 | 1 | 42.00 | 42.00 |
| AMS1117-3.3 fixed | R193008 | 1 | 4.81 | 4.81 |
| ULN2803A | R194519 | 1 | 40.00 | 40.00 |
| LTV-827S | 1087779 | 6 | 36.00 | 216.00 |
| SMBJ15A-13-F | R190689 | 1 | 22.00 | 22.00 |
| SS34 | 649691 | 2 | 1.72 | 3.44 |
| **Components per board** | | | | **773.45** |
| Components for 5 boards | | | | 3867.25 |

Not on Robu.in: 2 × 20-pos 5.08 mm terminal blocks (J_IN, J_OUT) — source separately.
LTV-827S stock: only 18 pcs (30 needed for 5 boards) — order early.

## 2. PCB fabrication per board

| Board | Fab | ₹/board (5 pcs) | Source |
|---|---|---:|---|
| 2-layer | cuCircuits | 338.55 | live Gerber quote |
| 2-layer | Lion Circuits | 375.40 | live instant quote (₹1,877/5) |
| 1-layer | cuCircuits | not obtained | capabilities API supports layers=1; quote websocket blocked in this environment |
| 1-layer | Lion Circuits | not offered | instant quote lists 2/4/6/8 only; manual quote needed |

## 3. Total per board (excluding terminal blocks, shipping, assembly)

| Configuration | Components | PCB (cuCircuits) | Jumpers | Total ₹/board |
|---|---:|---:|---:|---:|
| 2-layer production | 773.45 | 338.55 | — | **1112.00** |
| 2-layer (Lion PCB) | 773.45 | 375.40 | — | **1148.85** |
| 1-layer prototype | 773.45 | TBD | 2.72 | **776.17 + PCB** |

## 4. Notes
- Component prices include GST; Robu.in prices/stock change — verify before ordering.
- 1-layer PCB needs a manual quote from either fab; both can make single-sided boards.
- Add terminal blocks (~₹150–250 each), shipping and assembly to get landed cost.
