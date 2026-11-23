# Robu Part Search - portable skill kit

Search **robu.in** for electronic components from **OpenCode** or **Qoder**:
live price, stock, SKU/MPN, full spec table, package dimensions, bulk price
tiers and quantity-aware BOM tables.

This kit is self-contained. It installs the same skill into both tools,
checks Python dependencies, and finishes with a live search so you know it
works.

---

## Quick start (Windows)

1. Unzip this folder anywhere (Desktop is fine).
2. Double-click **`install.bat`**.
3. Wait for:

   ```
   [ok] Live search returned a product link
   ```

4. Open OpenCode or Qoder and ask:

   > Search robu.in for LTV-356T and show price and stock

That's it. No administrator rights, no API keys, no account.

### Installed locations

| Tool | User-level skill folder |
| --- | --- |
| OpenCode | `%USERPROFILE%\.config\opencode\skills\robu-part-search` |
| Qoder | `%USERPROFILE%\.qoder\skills\robu-part-search` |

The installer skips a target that is already up to date and backs up an
older copy as `robu-part-search.bak-YYYYMMDD-HHMMSS` before replacing it.

---

## Requirements

- Windows 10/11 (the skill itself also works on macOS/Linux).
- Python **3.8+** with `pip`.
- Google Chrome or Microsoft Edge.
- Internet access to robu.in.

The installer handles the Python packages:

```
DrissionPage>=4.1,<5
beautifulsoup4>=4.12
```

It does **not** install Python or a browser. If Python is missing, install it
first (or run `install.ps1 -InstallPython`, which uses winget):

```powershell
winget install -e --id Python.Python.3.12 --scope user
```

---

## What the installer does

1. Finds a usable Python (`py -3`, `python`, or `python3`).
2. Installs `DrissionPage` + `beautifulsoup4` into your user site-packages.
3. Detects Chrome/Edge.
4. Copies `skill\` into the OpenCode and Qoder skill folders.
5. Runs `search_robu.py "LTV-356T" --fast --top 1` as a smoke test.

Everything is logged in the console. Re-running is safe and idempotent.

---

## Install options

Run from a terminal in this folder:

```powershell
# default: both tools, user-level
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1

# only one tool
.\install.ps1 -Targets opencode
.\install.ps1 -Targets qoder

# project/team install (creates .opencode\skills and .qoder\skills in a repo)
.\install.ps1 -Scope Project -ProjectDir C:\work\my-board

# preview, change nothing
.\install.ps1 -DryRun

# skip dependency install or the live test
.\install.ps1 -SkipDeps
.\install.ps1 -SkipTest

# install Python automatically with winget if missing
.\install.ps1 -InstallPython
```

If PowerShell blocks scripts, `install.bat` already uses
`-ExecutionPolicy Bypass`; no permanent policy change is needed.

---

## Using the skill

### OpenCode

OpenCode watches its config and reloads skills after a save. Start a session
(or reload) and either ask naturally or reference the skill:

```
@robu-part-search search for a 4 pin 5mm pluggable screw terminal
```

### Qoder

New sessions load skills at startup. In a running session use:

```
/skills reload
```

Then ask naturally, or invoke it directly:

```
/robu-part-search price a BOM for this board
```

### Command line (same engine, no AI)

```powershell
$skill = "$HOME\.config\opencode\skills\robu-part-search\scripts\search_robu.py"

# one part
python $skill "LTV-356T"

# several parts, one browser session
python $skill "60v buck converter" "4g lte antenna sma" --top 2

# BOM table: qty per query, bulk-tier unit price, extended cost and total
python $skill "100nF 0805 50V" "LTV-356T" --qty 20,4 --table

# machine-readable
python $skill "rtc module" --json

# append a dated section to a sourcing doc
python $skill "rtc module" --out NEEDED_COMPONENTS.md
```

| Flag | Meaning |
| --- | --- |
| `--top N` | Products fetched with full detail (default 3) |
| `--limit N` | API results per query (default 50) |
| `--fast` | Skip product pages; API fields only |
| `--qty N[,N]` | BOM quantity per query (last repeats); applies the bulk tier |
| `--table` | Markdown BOM table plus INR total |
| `--json` | Machine-readable output |
| `--out FILE` | Append a dated "Robu.in matches" section |

---

## How it works

robu.in is behind a Cloudflare JavaScript challenge. Plain `requests`,
`curl_cffi` and headless browsers get HTTP 403. The skill launches the system
Chrome **headed** (positioned off-screen), clears the challenge once, then
uses same-origin `fetch()` calls:

- `POST /api/search/` for product candidates
- `POST /api/proxy/graphql/` (batched) for specs, stock count, bulk tiers,
  brand and datasheet links

A brief Chrome window is normal. Typical query time is 1-5 seconds after the
first navigation; a cold Cloudflare check can take up to about a minute.

Ranking combines keyword/synonym matching, numeric feature checks (pins,
pitch, volts, amps, MHz, GB), a wrong-kind penalty, in-stock preference and
budget preference. Every detailed pick gets a confidence flag:
`high` / `medium` / `low`. Always open the link for `low` picks.

---

## Sharing with colleagues

Send them this ZIP. They unzip it and run `install.bat`.

For a team repo, commit a project-level copy instead:

```powershell
.\install.ps1 -Scope Project -ProjectDir C:\work\team-repo
```

This creates:

```
team-repo\
├── .opencode\skills\robu-part-search\
└── .qoder\skills\robu-part-search\
```

Everyone who opens that repo gets the skill without a global install.

---

## Verify / troubleshoot

Run the read-only doctor:

```powershell
.\doctor.ps1
```

It checks Python, packages, Chrome/Edge, both skill folders and connectivity
to robu.in.

| Symptom | Fix |
| --- | --- |
| `Python 3.8+ was not found` | Install Python and tick "Add python.exe to PATH", or run `install.ps1 -InstallPython` |
| `pip` fails behind a corporate proxy | `python -m pip install --user --proxy http://user:pass@host:port -r skill\requirements.txt` |
| `403` or endless "Just a moment" | Open https://robu.in/ once in Chrome manually, wait for the challenge, retry |
| Chrome window flashes | Expected - the challenge is solved in a real browser |
| `DrissionPage missing` in the tool | Re-run `install.bat`, then `/skills reload` (Qoder) or start a new OpenCode session |
| Qoder does not list the skill | Run `/skills` and `/skills reload`; confirm `%USERPROFILE%\.qoder\skills\robu-part-search\SKILL.md` exists |
| OpenCode does not list the skill | Confirm `%USERPROFILE%\.config\opencode\skills\robu-part-search\SKILL.md`; run `/reload` |
| ZIP downloaded from the internet is blocked | Right-click the ZIP > Properties > Unblock before extracting |
| Antivirus flags DrissionPage | It automates Chrome; add an exclusion or use a signed Python/Chrome build |

If all else fails, the script can be run directly with a normal Python
install:

```powershell
python "<path>\skill\scripts\search_robu.py" "LTV-356T"
```

---

## Uninstall

```powershell
.\uninstall.ps1            # remove from both tools
.\uninstall.ps1 -WhatIf    # preview
```

Python packages are intentionally left installed. Remove them with:

```powershell
python -m pip uninstall DrissionPage beautifulsoup4
```

---

## Notes

- Prices are in INR incl. GST. Stock and prices change; the skill notes the
  date checked.
- No API key, login or telemetry. The script talks only to robu.in.
- The ZIP contains no Python packages and no browser profile - the installer
  fetches dependencies on each machine.
- Use it responsibly: reasonable batch sizes, no hammering the site.

See `CHANGELOG.md` for version history.
