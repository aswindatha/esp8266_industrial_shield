---
name: robu-part-search
description: Search robu.in for electronic components with live price, stock, SKU/MPN, specs and package dimensions. Use when sourcing parts for a BOM, pricing quantities, checking stock, or finding cheaper alternatives.
---

# Robu.in Part Search

Find, price and stock-check electronic components on **robu.in** (Indian
electronics store) from the command line, including bulk price tiers and
quantity-aware BOM totals.

**Use this skill when** a BOM, purchase list, `NEEDED_COMPONENTS.md` or a
"what should I buy" question needs parts sourced from robu.in.

## Requirements

- Python 3.8+ with `DrissionPage` and `beautifulsoup4`
  (`pip install -r requirements.txt`).
- Google Chrome or Microsoft Edge installed.
- Network access to robu.in.

`scripts/search_robu.py` sits beside this `SKILL.md`. Resolve paths
relative to this skill's directory:

```bash
python "<skill-dir>/scripts/search_robu.py" "LTV-356T"
```

If the portable kit installer was used, dependencies are already
installed and a smoke test has been run.

## Why it drives a real browser

robu.in is behind a Cloudflare JavaScript challenge. Plain `requests`,
`curl_cffi` and headless browsers get HTTP 403. The script launches the
system Chrome (headed, positioned off-screen), clears the challenge once,
then makes same-origin `fetch()` calls: `POST /api/search/` and a batched
`POST /api/proxy/graphql/` for product details. A query takes roughly
1-5 s after the first navigation; a cold Cloudflare check can take up to
about 60 s.

A Chrome window may briefly appear - this is expected.

## Usage

```bash
# single part: best pick + alternates, full specs
python scripts/search_robu.py "4 pin 5mm pluggable screw terminal"

# batch: one browser for all queries
python scripts/search_robu.py "60v buck converter" "4g lte antenna sma" --top 2 --json

# BOM table with quantities and bulk tiers
python scripts/search_robu.py "100nF 0805 50V" "LTV-356T" --qty 20,4 --table

# append results to a sourcing document
python scripts/search_robu.py "rtc module" --out NEEDED_COMPONENTS.md
```

| Flag | Meaning |
| --- | --- |
| `--top N` | Products fetched with full detail (default 3) |
| `--limit N` | API results per query (default 50) |
| `--fast` | Skip product pages; API fields only |
| `--qty N[,N]` | BOM quantity per query (last value repeats); applies the `moq_prices` tier |
| `--table` | Markdown BOM table plus a total |
| `--json` | Machine-readable output |
| `--out FILE` | Append a dated "Robu.in matches" section |

`--json` adds `bom_qty`, `unit_price_at_qty`, `ext_price`, `price_tier`
and `shortfall` to each `best` result.

## BOM workflow

1. Collect the gap list (BOM rows, `NEEDED_COMPONENTS.md`, a KiCad BOM).
2. Write one query per line item. Include pin count, pitch, voltage,
   package and connector type; drop filler words.
3. Batch the queries in one run with `--top 2 --table --qty ...`.
4. Check every `best` link, title and spec before ordering. The scorer
   ranks relevance; it does not guarantee the right part.
5. Add link, price, SKU/MPN, stock and key specs to the document. Note
   the date checked - prices and stock change.
6. If nothing matches, write "no robu.in match" and list the queries
   tried. Never invent a link.

## Ranking and confidence

- Title/MPN hits score 2; description/category hits score 0.5.
- Synonym expansion (`buck -> step-down/dc-dc/converter`, `rtc -> ds3231`,
  `4g -> lte/gsm` and similar).
- Numeric features (pins, pitch, V, A, MHz, GB) get bonuses and mismatch
  penalties - a 2.5 mm pitch part cannot beat a 5 mm query.
- Wrong-kind guard: -3 when no functional token hits the title.
- Widening: unmatched distinctive tokens (`rs485`, `sma`, `sps30`) trigger
  page 2 and a semantic retry. Semantic hits are accepted only with a
  real score, so gibberish queries return "no result".
- In-stock, top relevance, then cheapest among near-equal matches.
- `confidence`: `high` (specs confirm the query), `medium` (clean match,
  no spec conflict), `low` (conflict or weak match). **Open the link for
  `low` picks.**

## Notes

- Prices are in INR incl. GST; bulk tiers appear under `Bulk` or in
  `moq_prices`.
- `shipping_dims` and `shipping_weight` are package dimensions, not part
  dimensions. Real dimensions live in `specs` when published.
- Each run gets its own Chrome port and temporary profile, so parallel
  runs are safe.
- Respect the site: keep batches reasonable and avoid hammering it.

## Troubleshooting

- **403 or a "Just a moment" loop** - Chrome must be installed and able
  to run headed. Wait for the challenge, or open https://robu.in/ once
  manually in Chrome and retry.
- **`DrissionPage missing`** - run `pip install -r requirements.txt`.
- **Chrome not found** - install Chrome or Edge, or set the browser path.
- **No results** - simplify the query, drop filler words, try `--fast`,
  or check the exact MPN with `--json`.

## Version history

- 2.1.0 (2026-11-23): per-run browser isolation, Cloudflare retry,
  stricter semantic fallback, `--qty` and `--table`.
- 2.0.0: API-driven rewrite (search API plus GraphQL details).
