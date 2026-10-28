#!/usr/bin/env python3
"""
Placement validator for the 8x motor / 16x field ESP8266 controller.

Checks placement.csv against the mechanical and electrical placement rules
in the layout brief. Exit code 1 if any rule FAILS.

Coordinate system: KiCad PCB editor, origin at the TOP-LEFT board corner,
X to the right, Y downward, millimetres. Board 180 x 100.
"""

import csv
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_W, BOARD_H = 180.0, 100.0
EDGE_CLEAR = 0.5

# ESP-12F antenna keep-out (antenna end at Y = -4, module centre X = 88)
KEEPOUT = (78.0, -4.0, 98.0, 4.0)          # x0, y0, x1, y1
PAD6 = (80.4, 14.6)                        # GPIO12 pad centre
PAD8 = (80.4, 18.6)                        # VCC pad centre

# edge connector rows that butt against each other and may touch
ROWS = {
    "motors": ["J%d" % n for n in range(3, 11)],
    "fields": ["J%d" % n for n in range(11, 27)],
}


def load():
    parts = {}
    with open(os.path.join(HERE, "placement.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            parts[row["Ref"]] = {
                "x": float(row["X"]), "y": float(row["Y"]),
                "rot": float(row["Rot"]),
                "w": float(row["W"]), "h": float(row["H"]),
                "zone": row["Zone"], "note": row["Note"],
            }
    return parts


def box(p):
    return (p["x"] - p["w"] / 2, p["y"] - p["h"] / 2,
            p["x"] + p["w"] / 2, p["y"] + p["h"] / 2)


def dist(a, b):
    return math.hypot(a["x"] - b[0], a["y"] - b[1])


def overlap(a, b, tol=0.05):
    ax0, ay0, ax1, ay1 = box(a)
    bx0, by0, bx1, by1 = box(b)
    ox = min(ax1, bx1) - max(ax0, bx0)
    oy = min(ay1, by1) - max(ay0, by0)
    return ox > tol and oy > tol, round(ox, 2), round(oy, 2)


def main():
    parts = load()
    fails, warns, lines = [], [], []

    def check(ok, label, detail):
        (lines if ok else fails).append(
            ("PASS " if ok else "FAIL ") + label + ": " + detail)

    # 1. board bounds -------------------------------------------------------
    for ref, p in parts.items():
        x0, y0, x1, y1 = box(p)
        if ref == "U3":
            ok = x0 >= EDGE_CLEAR and x1 <= BOARD_W - EDGE_CLEAR and y0 >= -4.01
            check(ok, "bounds " + ref, "antenna overhang allowed to Y=-4")
            continue
        ok = (x0 >= -0.01 and y0 >= -0.01
              and x1 <= BOARD_W + 0.01 and y1 <= BOARD_H + 0.01)
        check(ok, "bounds " + ref, "box %.1f,%.1f-%.1f,%.1f" % (x0, y0, x1, y1))

    # 2. antenna keep-out ---------------------------------------------------
    kx0, ky0, kx1, ky1 = KEEPOUT
    for ref, p in parts.items():
        if ref == "U3":
            continue
        x0, y0, x1, y1 = box(p)
        inside = not (x1 <= kx0 or x0 >= kx1 or y1 <= ky0 or y0 >= ky1)
        check(not inside, "keepout " + ref, "clear of antenna zone")

    # 3. connector rows -----------------------------------------------------
    for i, ref in enumerate(ROWS["motors"]):
        p = parts[ref]
        check(abs(p["x"] - 175.0) < 0.01 and abs(p["y"] - (15 + 10 * i)) < 0.01,
              "row motors " + ref, "x=175 y=%d" % (15 + 10 * i))
    for i, ref in enumerate(ROWS["fields"]):
        p = parts[ref]
        check(abs(p["y"] - 95.0) < 0.01 and abs(p["x"] - (15 + 10 * i)) < 0.01,
              "row fields " + ref, "x=%d y=95" % (15 + 10 * i))
    check(abs(parts["J1"]["x"] - 5) < 0.01 and abs(parts["J1"]["y"] - 15) < 0.01,
          "J1 left edge", "x=5 y=15")
    check(abs(parts["J2"]["x"] - 5) < 0.01, "J2 left edge", "x=5")
    check(abs(parts["J27"]["y"] - 5) < 0.01, "J27 top edge", "y=5")

    # 4. surge network within 15 mm of J1 -----------------------------------
    for ref in ("F1", "D1", "D2"):
        d = dist(parts[ref], (parts["J1"]["x"], parts["J1"]["y"]))
        check(d <= 15.0, "surge " + ref, "%.1f mm from J1 (limit 15)" % d)

    # 5. GPIO12 strap net --------------------------------------------------
    d_r6 = dist(parts["R6"], PAD6)
    check(d_r6 <= 6.0, "R6 to GPIO12", "%.1f mm (limit 6)" % d_r6)
    d_u12 = dist(parts["U12"], PAD6)
    check(d_u12 <= 10.0, "U12 to GPIO12", "%.1f mm (limit 10)" % d_u12)

    # 6. ESP decoupling ----------------------------------------------------
    d_c10 = dist(parts["C10"], PAD8)
    check(d_c10 <= 5.0, "C10 to VCC pad", "%.1f mm" % d_c10)

    # 7. ULN to motor terminals -------------------------------------------
    for uln, motors in (("U6", range(3, 7)), ("U7", range(7, 11))):
        d = min(dist(parts[uln], (parts["J%d" % m]["x"], parts["J%d" % m]["y"]))
                for m in motors)
        check(d <= 20.0, "ULN " + uln, "%.1f mm to nearest motor terminal" % d)

    # 8. mounting holes vs connectors --------------------------------------
    for hole in ("MH1", "MH2", "MH3", "MH4"):
        for ref, p in parts.items():
            if not ref.startswith("J") or ref == hole:
                continue
            bad, ox, oy = overlap(parts[hole], p)
            if bad:
                check(False, "hole " + hole, "overlaps " + ref)

    # 9. body overlaps (connectors in the same row are allowed to butt) ----
    row_of = {}
    for name, refs in ROWS.items():
        for r in refs:
            row_of[r] = name
    refs = sorted(parts)
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            if row_of.get(a) and row_of.get(a) == row_of.get(b):
                continue
            bad, ox, oy = overlap(parts[a], parts[b])
            if bad:
                fails.append("FAIL overlap %s/%s: %.2f x %.2f mm" % (a, b, ox, oy))

    # 10. isolation moat is empty of parts ---------------------------------
    mx0, my0, mx1, my1 = 6.0, 71.0, 160.0, 73.0          # moat band
    for ref, p in parts.items():
        if ref.startswith("U") and ref in ("U8", "U9", "U10", "U11"):
            continue                                       # optos straddle it
        x0, y0, x1, y1 = box(p)
        if not (x1 <= mx0 or x0 >= mx1 or y1 <= my0 or y0 >= my1):
            warns.append("WARN moat %s: body enters the moat band" % ref)

    print("placement check - board %.0f x %.0f mm, %d parts"
          % (BOARD_W, BOARD_H, len(parts)))
    for line in lines:
        print("  " + line)
    for w in warns:
        print("  " + w)
    for f_ in fails:
        print("  " + f_)
    print("\n%d pass, %d warn, %d fail" % (len(lines), len(warns), len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
