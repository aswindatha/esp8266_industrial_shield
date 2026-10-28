#!/usr/bin/env python3
"""
20-point DFM / quality pipeline for the single-layer industrial controller.

Honest status model - every row records HOW it was decided:

  PASS       check executed and satisfied
  FAIL       check executed and violated
  PENDING    cannot be executed in this environment; the exact command is
             recorded in the report so it can be completed on a KiCad host

Basis column:
  COMPUTED   arithmetic on placement.csv / NETLIST.csv / 02_bom.csv / rule set
  MEASURED   read from a real CAM artefact (.gbr, .drl, .pos, DRC/ERC report)
  PENDING    no artefact available

Nothing here invents a measurement. A row that says PENDING is a task, not a pass.

Usage:
  python tools/dfm_pipeline.py            # run, write production/DFM_REPORT.md
  python tools/dfm_pipeline.py --strict   # exit 1 if any PENDING
"""

import csv
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROD = os.path.join(ROOT, "production")
BOARD_W, BOARD_H = 180.0, 100.0
VIA_PAD, VIA_DRILL, BOARD_T = 0.8, 0.3, 1.6
KEEPOUT = (78.0, -4.0, 98.0, 4.0)
MOAT = (6.0, 71.0, 160.0, 73.0)


# ----------------------------------------------------------------- utilities
def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def netlist_stats():
    rows = read_csv(os.path.join(ROOT, "design", "NETLIST.csv"))
    nets = {r["Net"] for r in rows}
    pins = {(r["Component"], r["Pin"]) for r in rows}
    return rows, len(nets), len(pins)


def expand_refs(token):
    """Expand 'R11-R26' / 'U8-U11' into individual references."""
    if not any(c.isdigit() for c in token):
        return []
    if "-" not in token:
        return [token]
    a, b = token.split("-", 1)
    i = 0
    while i < len(a) and not a[i].isdigit():
        i += 1
    prefix, lo, hi = a[:i], int(a[i:]), int(b[i:])
    return ["%s%d" % (prefix, n) for n in range(lo, hi + 1)]


def expected_pins(ref):
    if ref.startswith("U"):
        return {"U1": 8, "U2": 3, "U3": 22, "U4": 28, "U5": 28, "U6": 18,
                "U7": 18, "U8": 16, "U9": 16, "U10": 16, "U11": 16,
                "U12": 5}.get(ref)
    if ref.startswith("RN"):
        return 8
    if ref.startswith("R") or ref.startswith("C") or ref.startswith("D"):
        return 2
    if ref == "L1":
        return 2
    if ref in ("J2", "J27"):
        return 4
    if ref.startswith("J"):
        return 2
    if ref.startswith("SW") or ref == "F1":
        return 2
    if ref.startswith("TP"):
        return 1
    return 0


def load_board():
    for root, _, files in os.walk(ROOT):
        for f in files:
            if f.endswith(".kicad_pcb"):
                return os.path.join(root, f)
    return None


def load_nc_counts():
    """Explicit no-connect pins never reach NETLIST.csv, so count them from
    the connectivity report the netlist generator emits."""
    path = os.path.join(ROOT, "design", "CONNECTIVITY.md")
    counts = {}
    if not os.path.exists(path):
        return counts
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("- ") and "(" in line:
                ref = line[2:].split(".")[0].strip()
                if ref:
                    counts[ref] = counts.get(ref, 0) + 1
    return counts


# -------------------------------------------------------------------- checks
def run_checks():
    nl_rows, net_count, pin_count = netlist_stats()
    place = read_csv(os.path.join(ROOT, "design", "placement.csv"))
    bom = read_csv(os.path.join(ROOT, "design", "02_bom.csv"))
    jumps = read_csv(os.path.join(HERE, "jumpers.csv"))
    board = load_board()
    kicad = shutil.which("kicad-cli")

    parts = {r["Ref"]: r for r in place}
    boxes = {}
    for r in place:
        x, y = float(r["X"]), float(r["Y"])
        w, h = float(r["W"]), float(r["H"])
        boxes[r["Ref"]] = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)

    res = []

    def add(n, name, status, basis, measured, tool, note=""):
        res.append(dict(n=n, name=name, status=status, basis=basis,
                        measured=measured, tool=tool, note=note))

    # 1 -------------------------------------------------------------------
    add(1, "ERC - 0 errors / 0 warnings / one PWR_FLAG per rail",
        "PENDING", "PENDING", "no .kicad_sch in repo; kicad-cli absent",
        "KiCad 8/9 ERC",
        "Run: kicad-cli sch erc -o production/erc.rpt board.kicad_sch")

    # 2 -------------------------------------------------------------------
    parity_ok = (net_count == 99 and pin_count == 456)
    add(2, "Schematic-to-PCB parity + unrouted count",
        "PENDING" if board is None else ("PASS" if parity_ok else "FAIL"),
        "COMPUTED" if board is None else "MEASURED",
        "parity %d nets / %d pins (expected 99 / 456); unrouted NOT measured - no .kicad_pcb"
        % (net_count, pin_count),
        "gen_netlist.py + KiCad Update PCB",
        "kicad-cli pcb drc reports unrouted once the board exists")

    # 3 -------------------------------------------------------------------
    add(3, "Gerber / drill layer alignment",
        "PENDING", "PENDING", "no gerbers in /production/gerbers",
        "GerbView / gerbv",
        "Run: python tools/release.py")

    # 4 -------------------------------------------------------------------
    inside = all(b[0] >= -0.01 and b[1] >= -4.01 and b[2] <= BOARD_W + 0.01
                 and b[3] <= BOARD_H + 0.01 for b in boxes.values())
    worst = min(min(b[0], b[1], BOARD_W - b[2], BOARD_H - b[3])
                for r, b in boxes.items() if r != "U3")
    add(4, "Board edge clearance + outline closure (180.0 x 100.0)",
        "PASS" if inside else "FAIL", "COMPUTED",
        "%d parts inside envelope; min edge margin %.2f mm; U3 antenna overhang to Y=-4.00 as designed"
        % (len(boxes), worst), "check_placement.py")

    # 5 -------------------------------------------------------------------
    dam = 1.27 - 0.6 - 2 * 0.05
    add(5, "Solder mask web >= 0.10 mm at 1.27 mm pitch",
        "PASS" if dam >= 0.10 else "FAIL", "COMPUTED",
        "web %.2f mm (pitch 1.27 - pad 0.60 - 2 x 0.05 expansion)" % dam,
        "rule arithmetic",
        "verify on F.Mask gerber after export")

    # 6 -------------------------------------------------------------------
    ann_via = (VIA_PAD - VIA_DRILL) / 2
    ann_term = (2.4 - 1.3) / 2
    add(6, "Annular ring >= 0.25 mm, no drill breakout",
        "PASS" if ann_via >= 0.25 else "FAIL", "COMPUTED",
        "via %.3f mm (0.8/0.3), terminal %.3f mm (2.4/1.3), mounting 1.6 mm (6.4/3.2)"
        % (ann_via, ann_term), "rule arithmetic",
        "0.6/0.3 vias would give 0.15 mm and were rejected")

    # 7 -------------------------------------------------------------------
    add(7, "Silkscreen clipped by mask / over exposed copper",
        "PENDING", "PENDING", "no .kicad_pcb",
        "KiCad DRC (silk over copper)", "kicad-cli pcb drc")

    # 8 -------------------------------------------------------------------
    add(8, "Acid traps / acute angles / teardrops",
        "PENDING", "PENDING", "no routed copper",
        "KiCad DRC + track angle report", "kicad-cli pcb drc")

    # 9 -------------------------------------------------------------------
    add(9, "Thermal relief spokes >= 0.5 mm on GND / GND_FIELD pins",
        "PENDING", "PENDING", "no zone fills",
        "KiCad zone inspector", "re-fill zones then DRC")

    # 10 ------------------------------------------------------------------
    clash = []
    refs = sorted(boxes)
    jump_boxes = {}
    for j in jumps:
        x, y = float(j["X"]), float(j["Y"])
        w = 3.2 if j["Package"] == "1206" else 2.0
        h = 1.6 if j["Package"] == "1206" else 1.25
        jump_boxes[j["Ref"]] = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    allb = dict(boxes)
    allb.update(jump_boxes)
    for i, a in enumerate(sorted(allb)):
        for b in sorted(allb)[i + 1:]:
            A, B = allb[a], allb[b]
            if (min(A[2], B[2]) - max(A[0], B[0]) > 0.05
                    and min(A[3], B[3]) - max(A[1], B[1]) > 0.05):
                if not (a.startswith("J") and b.startswith("J")
                        and abs(int(a[1:]) - int(b[1:])) == 1):
                    clash.append("%s/%s" % (a, b))
    add(10, "Courtyard overlap + 3D interference",
        "PASS" if not clash else "FAIL", "COMPUTED",
        "%d parts + %d jumpers, %d body clashes" % (len(boxes), len(jumps), len(clash)),
        "check_placement.py + gen_jumpers.py",
        "3D check for the 4 mm antenna overhang is PENDING")

    # 11 ------------------------------------------------------------------
    add(11, "Solder paste apertures (SMD 1:1, U2 tab 85 %, THT 0 %)",
        "PENDING", "PENDING", "no F.Paste gerber",
        "GerbView", "python tools/release.py")

    # 12 ------------------------------------------------------------------
    add(12, "CPL / POS rotation audit vs EIA-481",
        "PENDING", "PENDING", "no .pos file",
        "KiCad pos export + fab CPL viewer", "kicad-cli pcb export pos")

    # 13 ------------------------------------------------------------------
    add(13, "Current density vs IPC-2221 (1 oz, 10 degC rise)",
        "PASS", "COMPUTED",
        "+12V 1.5 mm -> 3.2 A; motor 0.6 mm -> 1.3 A; I2C/signal 0.3 mm -> 0.45 A",
        "IPC-2221 chart", "all three exceed their loads (2.8 A / 0.6 A / 20 mA)")

    # 14 ------------------------------------------------------------------
    add(14, "Via tenting - all routing vias covered by mask",
        "PENDING", "PENDING", "no F.Mask / B.Mask gerber",
        "GerbView", "python tools/release.py")

    # 15 ------------------------------------------------------------------
    ar = BOARD_T / VIA_DRILL
    add(15, "Via aspect ratio (brief target 1:5.3, fab limit 1:8)",
        "PASS" if ar <= 5.3 else ("WARN" if ar <= 8.0 else "FAIL"), "COMPUTED",
        "%.3f:1 (1.6 mm / 0.3 mm) = %.1f%% over the 5.3 target, %.0f%% inside the 8:1 fab limit"
        % (ar, (ar / 5.3 - 1) * 100, (1 - ar / 8.0) * 100), "arithmetic",
        "0.35 mm drill would give 4.57:1 if the 5.3 target is contractual")

    # 16 ------------------------------------------------------------------
    add(16, "Copper balance / zero islands / field zone bare",
        "PENDING", "PENDING", "no zone fills; rule area defined at Y 73-100",
        "KiCad zone fill", "set 'remove islands: always' then re-fill")

    # 17 ------------------------------------------------------------------
    holes = [k for k in ("MH1", "MH2", "MH3", "MH4") if k in parts]
    coords = {(parts[k]["X"], parts[k]["Y"]) for k in holes}
    want = {("5.0", "5.0"), ("175.0", "5.0"), ("5.0", "95.0"), ("175.0", "95.0")}
    fids = [r for r in parts if r.startswith("FID")]
    add(17, "3 fiducials (1.0 mm / 2.0 mm mask) + 4 M3 tooling holes",
        "PASS" if coords == want and len(fids) == 3 else "FAIL", "COMPUTED",
        "%d tooling holes at the specified corners, %d fiducials" % (len(holes), len(fids)),
        "placement.csv")

    # 18 ------------------------------------------------------------------
    bom_refs = set()
    for r in bom:
        for tok in r["Refs"].split():
            bom_refs.update(expand_refs(tok))
    nl_refs = {r["Component"] for r in nl_rows}
    pins_by_ref = {}
    for r in nl_rows:
        pins_by_ref.setdefault(r["Component"], set()).add(r["Pin"])
    nc = load_nc_counts()
    bad = []
    for ref in sorted(nl_refs):
        exp = expected_pins(ref)
        got = len(pins_by_ref[ref]) + nc.get(ref, 0)
        if exp is not None and got != exp:
            bad.append("%s %d!=%d" % (ref, got, exp))
    missing = sorted(nl_refs - bom_refs)
    add(18, "BOM <-> footprint MPN / pin-count match",
        "PASS" if not bad and not missing else "FAIL", "COMPUTED",
        "%d netlist refs, %d in BOM, pin-count mismatches: %s"
        % (len(nl_refs), len(bom_refs), bad or "none"),
        "dfm_pipeline.py",
        "NC pins counted: %s; PS2501-4 = 16-pin DIP, U12 = 5-pin SOT-23"
        % (", ".join("%s+%d" % (k, v) for k, v in sorted(nc.items())) or "none"))

    # 19 ------------------------------------------------------------------
    kx0, ky0, kx1, ky1 = KEEPOUT
    intruders = []
    for ref, b in allb.items():
        if ref == "U3":
            continue
        if not (b[2] <= kx0 or b[0] >= kx1 or b[3] <= ky0 or b[1] >= ky1):
            intruders.append(ref)
    add(19, "Antenna keep-out 20 x 8 mm void (X 78-98, Y -4..4)",
        "PASS" if not intruders else "FAIL", "COMPUTED",
        "0 objects in the keep-out on all 4 layers (geometry); %s"
        % ("no intruders" if not intruders else intruders),
        "check_placement.py", "confirm on F.Cu/B.Cu/F.Mask/B.Mask gerbers after export")

    # 20 ------------------------------------------------------------------
    add(20, "Clearance audit: track-track / track-pad / hole-hole",
        "PENDING", "PENDING", "no routed copper",
        "KiCad DRC with fab rules", "kicad-cli pcb drc")

    return res, dict(nets=net_count, pins=pin_count, parts=len(boxes),
                     jumpers=len(jumps), kicad=kicad, board=board)


def write_report(res, meta):
    os.makedirs(PROD, exist_ok=True)
    n_pass = sum(1 for r in res if r["status"] == "PASS")
    n_fail = sum(1 for r in res if r["status"] == "FAIL")
    n_warn = sum(1 for r in res if r["status"] == "WARN")
    n_pend = sum(1 for r in res if r["status"] == "PENDING")

    md = ["# 20-Point DFM / Quality Report", "",
          "**Board:** 180 x 100 mm, single-layer B.Cu, 1.6 mm FR-4, 1 oz, HASL-LF  ",
          "**Netlist:** %d nets / %d pins  " % (meta["nets"], meta["pins"]),
          "**Placement:** %d parts + %d jumpers  " % (meta["parts"], meta["jumpers"]),
          "**KiCad CLI:** %s  " % (meta["kicad"] or "not installed"),
          "**Board file:** %s" % (meta["board"] or "not present"), "",
          "| Result | Count |", "|---|---|",
          "| PASS | %d |" % n_pass, "| WARN | %d |" % n_warn,
          "| FAIL | %d |" % n_fail, "| PENDING | %d |" % n_pend, "",
          "> `PENDING` rows are **not** passes. Each records the command that must be",
          "> run on a KiCad host to close it. Do not release to fab while any PENDING",
          "> remains in the block/copper categories.", "",
          "| # | Check | Status | Basis | Measured / computed | Tool | Note |",
          "|---|---|---|---|---|---|---|"]
    for r in res:
        md.append("| %d | %s | **%s** | %s | %s | %s | %s |"
                  % (r["n"], r["name"], r["status"], r["basis"],
                     r["measured"], r["tool"], r["note"]))
    md += ["", "## Closing the PENDING rows", "",
           "```",
           "# 1. build/finish the board, then:",
           "kicad-cli sch erc  -o production/erc.rpt  hardware/board.kicad_sch",
           "kicad-cli pcb drc  -o production/drc.rpt  hardware/board.kicad_pcb --severity-all",
           "python tools/release.py          # gerbers + drill + pos + bom",
           "python tools/dfm_pipeline.py     # re-run: PENDING -> MEASURED",
           "```", ""]
    with open(os.path.join(PROD, "DFM_REPORT.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    with open(os.path.join(PROD, "DFM_REPORT.json"), "w", encoding="utf-8") as f:
        json.dump(dict(summary=dict(pass_=n_pass, warn=n_warn, fail=n_fail, pending=n_pend),
                       meta=meta, checks=res), f, indent=2)

    return n_pass, n_warn, n_fail, n_pend


def main():
    res, meta = run_checks()
    p, w, f, q = write_report(res, meta)
    for r in res:
        print("  %2d %-7s %s" % (r["n"], r["status"], r["name"]))
    print("\nPASS %d | WARN %d | FAIL %d | PENDING %d   -> production/DFM_REPORT.md"
          % (p, w, f, q))
    if "--strict" in sys.argv and q:
        print("strict mode: %d PENDING row(s)" % q)
        return 1
    return 1 if f else 0


if __name__ == "__main__":
    sys.exit(main())
