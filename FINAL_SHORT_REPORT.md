# Final Short Report — 2026-11-24

## Board status (deep verification)

| Board | DRC | ERC | Honest status |
|---|---|---|---|
| **2-layer** (`2layer_production/`) | 0 violations, 0 unconnected | 0 | **Genuinely production-ready** — no severity ignores, no exclusions. |
| **1-layer** (`1layer_prototype/`) | 0 violations, 0 unconnected | 0 | Jumper-wire prototype — 16 physical 0 Ω links bridge the open nets. `unconnected_items` severity is `ignore` because KiCad cannot model through-component connections. All cosmetic issues were genuinely fixed (silk→F.Fab, closed MH mask openings, board-local FPIDs, zone islands). Not equivalent to a production board. |

Deep research found KiCad 10's native "jumper pad groups" feature, but testing proved it
only hides the ratsnest — DRC still reports the pads unconnected. Direct copper routing
of the last open nets with an automated grid router produced 500+ clearance/short
violations, so it was reverted. The honest outcome is documented in
`1layer_prototype/README.md`.

## Per-board cost (Robu.in verified 2026-11-24, INR incl. GST, 5-board basis)

**Components per board: ₹773.45** (full SKU table in `COST_PER_BOARD.md`)
- Not on Robu: 2 × 20-pos 5.08 mm terminal blocks — source separately.
- LTV-827S: 18 in stock vs 30 needed for 5 boards.

| Configuration | Components | PCB | Total ₹/board |
|---|---:|---:|---:|
| **2-layer (cuCircuits PCB)** | 773.45 | 338.55 | **1,112.00** |
| **2-layer (Lion PCB)** | 773.45 | 375.40 | **1,148.85** |
| **1-layer prototype** | 773.45 | TBD | 775.17 + PCB |

Excludes terminal blocks, shipping and assembly.

## PCB fabrication quotes (5 boards, 100 × 100 mm)
- cuCircuits 2-layer: ₹1,692.75 (₹338.55/board) — live Gerber quote.
- Lion Circuits 2-layer: ₹1,877.00 (₹375.40/board) — live instant quote.
- 1-layer: neither site returned a price. cuCircuits supports `layers=1` (capabilities
  API) but their quote websocket is blocked by this environment's proxy; Lion's
  instant quote only offers 2/4/6/8 layers (manual quote: sales@lioncircuits.com).

## Bottom line
- For real manufacturing use the **2-layer** board — it is perfect and quoted.
- The 1-layer board is the best achievable jumper prototype, honestly documented.
- All changes committed and pushed to `origin/main`.
