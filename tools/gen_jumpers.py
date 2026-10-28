#!/usr/bin/env python3
"""
Jumper schedule generator for the single-layer build.

A single-layer board forces every copper crossing onto F.Cu as a 0R link.
This script lays the 44 planned jumpers on collision-free grid positions inside
eight routing corridors and validates each one against placement.csv.

Status semantics:
  PLANNED  - design-intent position inside its corridor. Becomes authoritative
             only after the single-layer route is drawn and the crossing is
             confirmed. Re-run this script after any placement change.

Output: tools/jumpers.csv
"""

import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PLACEMENT = os.path.join(ROOT, "design", "placement.csv")
OUT = os.path.join(HERE, "jumpers.csv")

# 52 = 6 + 4 + 4 + 12 + 16 + 4 + 4 + 2. Group E is 16, not 8: every field
# channel's signal path crosses the common FLD_12V bus, so each needs a link.
EXPECTED = 52

# (prefix, qty, package, y, x_start, x_step, nets, group, corridor)
CORRIDORS = [
    ("A", 6, "1206", 18.0, 104.0, 12.0, ["+12V"] * 6, "power trunk -> U6/U7 COM", "X 100-168, Y 18"),
    ("B", 4, "0805", 22.5, 148.0, 6.0, ["GND_FIELD"] * 4, "ULN pin 9 return", "X 148-166, Y 22.5"),
    ("C", 4, "0805", 50.0, 122.0, 8.0, ["SDA", "SCL", "SDA", "SCL"], "I2C across drive fan-out", "X 122-146, Y 50"),
    ("D", 12, "0805", 66.0, 32.0, 10.0, ["OPT%d_COL" % i for i in range(1, 13)], "opto collector fan-in", "X 32-142, Y 66"),
    ("E", 16, "0805", 88.5, 15.0, 10.0, ["FL%d_N" % i for i in range(1, 17)], "field signal vs FLD_12V bus", "X 15-165, Y 88.5"),
    ("F", 4, "0805", 21.5, 134.0, 3.0, ["TXD0", "RXD0", "RST", "GPIO0"], "UART / strap routing", "X 134-143, Y 21.5"),
    ("G", 4, "0805", 57.0, 132.0, 4.0, ["+3V3", "+3V3", "+5V", "+5V"], "logic rail reach", "X 132-144, Y 57"),
    ("H", 2, "0805", 30.0, 24.0, 8.0, ["ECHO", "ECHO"], "echo divider to GPIO14", "X 24-32, Y 30"),
]


def load_placement():
    parts = {}
    with open(PLACEMENT, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            parts[row["Ref"]] = (
                float(row["X"]) - float(row["W"]) / 2,
                float(row["Y"]) - float(row["H"]) / 2,
                float(row["X"]) + float(row["W"]) / 2,
                float(row["Y"]) + float(row["H"]) / 2,
            )
    return parts


def overlaps(box, parts, tol=0.05):
    hits = []
    for ref, b in parts.items():
        ox = min(box[2], b[2]) - max(box[0], b[0])
        oy = min(box[3], b[3]) - max(box[1], b[1])
        if ox > tol and oy > tol:
            hits.append((ref, round(ox, 2), round(oy, 2)))
    return hits


def main():
    parts = load_placement()
    rows, failures = [], []
    n = 0
    W = {"1206": 3.2, "0805": 2.0}
    H = {"1206": 1.6, "0805": 1.25}

    for grp, qty, pkg, y, x0, dx, nets, desc, corridor in CORRIDORS:
        for i in range(qty):
            n += 1
            ref = "JMP%d" % n
            x = round(x0 + i * dx, 2)
            box = (x - W[pkg] / 2, y - H[pkg] / 2, x + W[pkg] / 2, y + H[pkg] / 2)
            hits = overlaps(box, parts)
            if hits:
                failures.append("%s (%s, %.1f, %.1f) collides with %s"
                                % (ref, grp, x, y, hits))
            rows.append([ref, grp, nets[i % len(nets)], pkg, "%.2f" % x,
                         "%.2f" % y, 0, "PLANNED", desc, corridor])

    # sanity: total and per-group counts
    if n != EXPECTED:
        failures.append("jumper count is %d, expected %d" % (n, EXPECTED))
    for grp, qty, *_ in CORRIDORS:
        got = sum(1 for r in rows if r[1] == grp)
        if got != qty:
            failures.append("group %s has %d, expected %d" % (grp, got, qty))

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Ref", "Group", "Net", "Package", "X", "Y", "Rot",
                    "Status", "Function", "Corridor"])
        w.writerows(rows)

    print("jumpers: %d written to %s" % (n, OUT))
    for grp, qty, pkg, *_ in CORRIDORS:
        print("  %s: %2d x %s" % (grp, qty, pkg))
    if failures:
        print("\n%d PROBLEM(S):" % len(failures))
        for p in failures:
            print("  " + p)
        return 1
    print("\n0 collisions against placement.csv, counts consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
