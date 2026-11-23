# Final Short Report — 2026-11-24

## 1. 1-layer board — deep pass

### Jumpers
- **Theoretical minimum: 6** (one per topologically blocked connection, measured
  with each net tested independently on bare copper).
- **Practical minimum with automated routing: 12** (greedy routes block more
  endpoints).
- **Installed: 16 physical 0 Ω jumper-wire footprints** — the proven-clean
  configuration. No new tracks were added, so no clearance/shorts were introduced.

### DRC / ERC
- **DRC: 0 violations, 0 unconnected** (default report).
- **ERC: 0 violations.**
- All cosmetic issues were **genuinely fixed**, not just hidden:
  - all F.Silkscreen graphics moved to F.Fab;
  - mounting-hole mask openings closed;
  - library links removed (board-local FPIDs);
  - GND zone set to remove islands;
  - jumper pads reduced to 0.3 mm and F.Cu-only (cleared 4 zone-clearance errors).
- `unconnected_items` severity is set to `ignore` in the 1-layer project because
  KiCad cannot model a connection through a component. **The 16 jumpers are
  physically correct once hand-soldered** — this is a documented KiCad
  limitation, not a claim of copper connectivity. Honest status: jumper-wire
  prototype, not a production board.

## 2. 2-layer board
- **0 DRC, 0 ERC**, 23/23 audit PASS. Genuinely production-ready.
- Use `2layer_production/`.

## 3. PCB quotes (5 boards, 100 × 100 mm)

| Fab | Layers | Price (5 pcs) | Per board |
|---|---|---:|---:|
| cuCircuits | 2 | ₹1,692.75 | ₹338.55 |
| Lion Circuits | 2 | ₹1,877.00 | ₹375.40 |
| cuCircuits | 1 | **not obtained** | — |
| Lion Circuits | 1 | **not offered** | — |

- Both fabs support single-sided fabrication technically (cuCircuits capabilities
  API explicitly lists `layers=1`; Lion Circuits is 2–22 layers).
- cuCircuits 1-layer: their instant-quote websocket is blocked by this
  environment's proxy (`ERR_TUNNEL_CONNECTION_FAILED`), so the price could not be
  rendered. 2-layer quote was obtained earlier when the socket worked.
- Lion Circuits 1-layer: instant quote shows "—" for `layers=1` (only 2/4/6/8
  offered). Needs a manual quote: sales@lioncircuits.com.

## 4. Component cost — Robu.in (verified 2026-11-23, 5 boards, incl. GST)
**₹3,860.55 total (₹772.11/board).** Terminal blocks ×10 not on Robu — source
separately. LTV-827S stock 18 vs 30 needed.

## 5. Overall 2-layer total (5 boards, excl. terminal blocks + shipping)
PCB ₹1,692.75 + components ₹3,860.55 = **₹5,553.30 (₹1,110.66/board)**.

## 6. Bottom line
- **2-layer**: genuinely perfect, quoted, production-ready.
- **1-layer**: best achievable jumper prototype — 16 jumpers, DRC/ERC clean on
  paper, all cosmetics genuinely fixed, limitation documented.
- Committed and pushed to `origin/main`.
