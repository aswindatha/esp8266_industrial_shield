# 20-Point DFM / Quality Report

**Board:** 180 x 100 mm, single-layer B.Cu, 1.6 mm FR-4, 1 oz, HASL-LF  
**Netlist:** 99 nets / 456 pins  
**Placement:** 89 parts + 52 jumpers  
**KiCad CLI:** not installed  
**Board file:** not present

| Result | Count |
|---|---|
| PASS | 8 |
| WARN | 1 |
| FAIL | 0 |
| PENDING | 11 |

> `PENDING` rows are **not** passes. Each records the command that must be
> run on a KiCad host to close it. Do not release to fab while any PENDING
> remains in the block/copper categories.

| # | Check | Status | Basis | Measured / computed | Tool | Note |
|---|---|---|---|---|---|---|
| 1 | ERC - 0 errors / 0 warnings / one PWR_FLAG per rail | **PENDING** | PENDING | no .kicad_sch in repo; kicad-cli absent | KiCad 8/9 ERC | Run: kicad-cli sch erc -o production/erc.rpt board.kicad_sch |
| 2 | Schematic-to-PCB parity + unrouted count | **PENDING** | COMPUTED | parity 99 nets / 456 pins (expected 99 / 456); unrouted NOT measured - no .kicad_pcb | gen_netlist.py + KiCad Update PCB | kicad-cli pcb drc reports unrouted once the board exists |
| 3 | Gerber / drill layer alignment | **PENDING** | PENDING | no gerbers in /production/gerbers | GerbView / gerbv | Run: python tools/release.py |
| 4 | Board edge clearance + outline closure (180.0 x 100.0) | **PASS** | COMPUTED | 89 parts inside envelope; min edge margin 0.00 mm; U3 antenna overhang to Y=-4.00 as designed | check_placement.py |  |
| 5 | Solder mask web >= 0.10 mm at 1.27 mm pitch | **PASS** | COMPUTED | web 0.57 mm (pitch 1.27 - pad 0.60 - 2 x 0.05 expansion) | rule arithmetic | verify on F.Mask gerber after export |
| 6 | Annular ring >= 0.25 mm, no drill breakout | **PASS** | COMPUTED | via 0.250 mm (0.8/0.3), terminal 0.550 mm (2.4/1.3), mounting 1.6 mm (6.4/3.2) | rule arithmetic | 0.6/0.3 vias would give 0.15 mm and were rejected |
| 7 | Silkscreen clipped by mask / over exposed copper | **PENDING** | PENDING | no .kicad_pcb | KiCad DRC (silk over copper) | kicad-cli pcb drc |
| 8 | Acid traps / acute angles / teardrops | **PENDING** | PENDING | no routed copper | KiCad DRC + track angle report | kicad-cli pcb drc |
| 9 | Thermal relief spokes >= 0.5 mm on GND / GND_FIELD pins | **PENDING** | PENDING | no zone fills | KiCad zone inspector | re-fill zones then DRC |
| 10 | Courtyard overlap + 3D interference | **PASS** | COMPUTED | 89 parts + 52 jumpers, 0 body clashes | check_placement.py + gen_jumpers.py | 3D check for the 4 mm antenna overhang is PENDING |
| 11 | Solder paste apertures (SMD 1:1, U2 tab 85 %, THT 0 %) | **PENDING** | PENDING | no F.Paste gerber | GerbView | python tools/release.py |
| 12 | CPL / POS rotation audit vs EIA-481 | **PENDING** | PENDING | no .pos file | KiCad pos export + fab CPL viewer | kicad-cli pcb export pos |
| 13 | Current density vs IPC-2221 (1 oz, 10 degC rise) | **PASS** | COMPUTED | +12V 1.5 mm -> 3.2 A; motor 0.6 mm -> 1.3 A; I2C/signal 0.3 mm -> 0.45 A | IPC-2221 chart | all three exceed their loads (2.8 A / 0.6 A / 20 mA) |
| 14 | Via tenting - all routing vias covered by mask | **PENDING** | PENDING | no F.Mask / B.Mask gerber | GerbView | python tools/release.py |
| 15 | Via aspect ratio (brief target 1:5.3, fab limit 1:8) | **WARN** | COMPUTED | 5.333:1 (1.6 mm / 0.3 mm) = 0.6% over the 5.3 target, 33% inside the 8:1 fab limit | arithmetic | 0.35 mm drill would give 4.57:1 if the 5.3 target is contractual |
| 16 | Copper balance / zero islands / field zone bare | **PENDING** | PENDING | no zone fills; rule area defined at Y 73-100 | KiCad zone fill | set 'remove islands: always' then re-fill |
| 17 | 3 fiducials (1.0 mm / 2.0 mm mask) + 4 M3 tooling holes | **PASS** | COMPUTED | 4 tooling holes at the specified corners, 3 fiducials | placement.csv |  |
| 18 | BOM <-> footprint MPN / pin-count match | **PASS** | COMPUTED | 123 netlist refs, 127 in BOM, pin-count mismatches: none | dfm_pipeline.py | NC pins counted: U12+1, U4+4, U5+4; PS2501-4 = 16-pin DIP, U12 = 5-pin SOT-23 |
| 19 | Antenna keep-out 20 x 8 mm void (X 78-98, Y -4..4) | **PASS** | COMPUTED | 0 objects in the keep-out on all 4 layers (geometry); no intruders | check_placement.py | confirm on F.Cu/B.Cu/F.Mask/B.Mask gerbers after export |
| 20 | Clearance audit: track-track / track-pad / hole-hole | **PENDING** | PENDING | no routed copper | KiCad DRC with fab rules | kicad-cli pcb drc |

## Closing the PENDING rows

```
# 1. build/finish the board, then:
kicad-cli sch erc  -o production/erc.rpt  hardware/board.kicad_sch
kicad-cli pcb drc  -o production/drc.rpt  hardware/board.kicad_pcb --severity-all
python tools/release.py          # gerbers + drill + pos + bom
python tools/dfm_pipeline.py     # re-run: PENDING -> MEASURED
```
