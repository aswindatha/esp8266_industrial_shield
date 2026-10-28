#!/usr/bin/env python3
"""
Place footprints and board frame in KiCad from design/placement.csv.

Runs inside KiCad's bundled Python (pcbnew). NOT executed in this repository's
environment - KiCad is not installed on the machine that generated the design
pack, so this script is delivered as the placement step you run locally.

    "C:\\Program Files\\KiCad\\9.0\\bin\\python.exe" tools/place_from_csv.py \
        --board hardware/board.kicad_pcb

Prerequisites: the .kicad_pcb already contains the 123 footprints (annotated,
imported via Update PCB from Schematic). This script only positions them.

Steps:
  1. move every footprint to its placement.csv coordinate and rotation
  2. draw the 180 x 100 mm Edge.Cuts rectangle
  3. add the three Rule Areas: antenna keep-out, isolation moat, bare field zone
  4. save and report anything that could not be matched
"""

import argparse
import csv
import os
import sys

try:
    import pcbnew
except ImportError:
    sys.exit("pcbnew not importable - run this with KiCad's bundled python.exe")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PLACEMENT = os.path.join(ROOT, "design", "placement.csv")

BOARD_W, BOARD_H = 180.0, 100.0


def v(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def rect(board, x0, y0, x1, y1, layer, width=0.1):
    for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                 ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(v(*a))
        s.SetEnd(v(*b))
        s.SetLayer(layer)
        s.SetWidth(pcbnew.FromMM(width))
        board.Add(s)


def rule_area(board, name, x0, y0, x1, y1):
    """Copper-free rule area on all copper layers."""
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    for setter in ("SetDoNotAllowCopperPour", "SetDoNotAllowTracks",
                   "SetDoNotAllowVias", "SetDoNotAllowPads",
                   "SetDoNotAllowFootprints"):
        try:
            getattr(z, setter)(True)
        except Exception:
            pass
    try:
        z.SetLayerSet(pcbnew.LSET.AllCuMask())
    except Exception:
        z.SetLayer(pcbnew.B_Cu)
    try:
        z.SetZoneName(name)
    except Exception:
        pass
    o = z.Outline()
    o.NewOutline()
    for pt in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        try:
            o.Append(v(*pt))
        except Exception:
            o.AppendCorner(v(*pt), -1)
    board.Add(z)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--frame-only", action="store_true",
                    help="only draw the outline and rule areas")
    args = ap.parse_args()

    board = pcbnew.LoadBoard(args.board)

    if not args.frame_only:
        rows = {}
        with open(PLACEMENT, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows[r["Ref"]] = (float(r["X"]), float(r["Y"]), float(r["Rot"]))

        placed, missing = 0, []
        for fp in board.GetFootprints():
            ref = fp.GetReference()
            if ref not in rows:
                if ref not in ("MH1", "MH2", "MH3", "MH4") and not ref.startswith("FID"):
                    missing.append(ref)
                continue
            x, y, rot = rows[ref]
            fp.SetPosition(v(x, y))
            fp.SetOrientationDegrees(rot)
            placed += 1
        print("placed %d footprints" % placed)
        if missing:
            print("not in placement.csv: %s" % ", ".join(sorted(missing)))

    rect(board, 0, 0, BOARD_W, BOARD_H, pcbnew.Edge_Cuts)
    rule_area(board, "ANTENNA_KEEPOUT", 78.0, -4.0, 98.0, 4.0)
    rule_area(board, "ISOLATION_MOAT", 6.0, 71.0, 160.0, 73.0)
    rule_area(board, "FIELD_ZONE_NO_COPPER", 0.0, 73.0, 180.0, 100.0)
    print("outline 180.0 x 100.0 + 3 rule areas written")

    board.Save(args.board)
    print("saved %s" % args.board)
    print("NOTE: the antenna keep-out rectangle extends to Y=-4, outside the")
    print("      board outline. KiCad allows it; the fab clips it at the edge.")


if __name__ == "__main__":
    main()
