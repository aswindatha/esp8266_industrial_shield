# Changelog

## 1.0.0 - 2026-11-23

First portable release of the Robu Part Search kit.

- Bundles `search_robu.py` 2.1.0 (API-driven crawler).
- Installs as a user-level or project-level skill for OpenCode and Qoder.
- `install.ps1` / `install.bat`: Python detection, dependency install,
  browser check, idempotent copy with timestamped backups, live smoke test.
- `doctor.ps1`: read-only health check (Python, packages, browser, skill
  folders, network).
- `uninstall.ps1`: removes installed skill folders, leaves Python packages.
- `examples\demo.ps1`: three sample queries with BOM quantities.

### Crawler 2.1.0

- Per-run Chrome debug port and temporary profile, so parallel runs no
  longer corrupt each other.
- Cloudflare HTML interstitials trigger a re-navigation and retry instead
  of silently degrading to page scraping.
- Semantic fallback accepts a result only with a real score, so gibberish
  queries return "no result" instead of random parts.
- New `--qty` and `--table` for quantity-aware BOM output (bulk tier unit
  price, extended cost, stock shortfall, INR total).
- JSON output carries `bom_qty`, `unit_price_at_qty`, `ext_price`,
  `price_tier` and `shortfall`.

### Crawler 2.0.0

- API-driven rewrite: search API plus batched GraphQL product details.
