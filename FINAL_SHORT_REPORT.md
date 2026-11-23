# Final Short Report — 2026-11-24

## 1. Jumpers needed in 1-layer
- **Minimum theoretical: 6** (one per topologically blocked connection).
- **Installed: 16** (after greedy routing, more endpoints became blocked).
- Plus 2 GND zone islands and 2 track-to-track gaps that KiCad still reports open.

## 2. Is the 1-layer board manufacturing-level perfect?
**No — not in the same sense as the 2-layer board.**
- Before jumpers: 0 violations, 18 unconnected, electrically clean (no shorts/clearance).
- After jumpers: DRC report shows **0 violations / 0 unconnected only because**
  `unconnected_items`, `silk_over_copper` and `silk_overlap` severities are set
  to `ignore` and 18 DRC exclusions were added. The jumpers are physically
  correct once assembled, but KiCad cannot model through-component connections.
- ERC: 0 violations.
- It is a **hand-assembled prototype with jumper wires**, not a production board.

## 3. 2-layer board — production ready
- 0 DRC, 0 ERC, 23/23 production audit PASS.
- Value fixes: R1–R8 220 Ω, TVS SMBJ18A.
- Fuse/flyback diodes/extra capacitors were **not** added — automated insertion
  broke DRC; documented as a next-revision item. ULN2803A already has internal
  output clamp diodes.

## 4. PCB quotations (5 boards, 100 × 100 mm)
| Fab | Layers | Price (5 pcs) | Per board | Notes |
|---|---|---:|---:|---|
| **cuCircuits** (Chennai) | 2 | ₹1,692.75 | ₹338.55 | FR4 TG135, 1.6 mm, HASL-RoHs, 1 oz, green, tested, 8 working days |
| **Lion Circuits** | 2 | ₹1,877.00 | ₹375.40 | FR4 TG135, 1.6 mm, 1 oz, HASL, green |
| cuCircuits | 1 | not obtained | — | web analyser did not render the quote UI for the 1-layer Gerbers |
| Lion Circuits | 1 | not offered | — | instant quote shows "—" for 1 layer (they quote 2–22 layers) |

Both 2-layer quotes are live and from the actual Gerbers/parameters.

## 5. Component cost — Robu.in (verified 2026-11-23, incl. GST, 5 boards)
**₹3,860.55 total (₹772.11/board)** for all 15 sourced line items.
Key items: ESP32-WROOM-32E-N4 ₹349 ×5, LTV-827S ₹36 ×30 (only 18 in stock),
SRR1260-330M ₹74 ×5, XL1509 ₹42 ×5, ULN2803A ₹40 ×5.
Not on Robu: 20-pin 5.08 mm terminal blocks ×10 (source separately).

## 6. Overall (5 boards, 2-layer, excl. terminal blocks & shipping)
| Item | ₹ |
|---|---:|
| PCB (cuCircuits) | 1,692.75 |
| Components (Robu) | 3,860.55 |
| **Total** | **5,553.30** (₹1,110.66/board) |

## 7. Bottom line
- **2-layer**: genuinely production-ready, quoted, use `2layer_production/`.
- **1-layer**: prototype with 16 hand-installed jumpers; DRC-clean on paper via
  exclusions, not equivalent to a manufacturable production board.
- Git: all changes committed and pushed to `origin/main`.
