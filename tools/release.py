#!/usr/bin/env python3
"""
Production release packager.

Wraps kicad-cli to produce everything the fab and the CM need:

  production/gerbers/            F.Cu B.Cu F.Mask B.Mask F.SilkS B.SilkS Edge.Cuts
  production/gerbers/*.drl       Excellon, PTH and NPTH separate
  production/assembly/board.pos  centroid (CPL) in mm
  production/assembly/board.csv  same, CSV for the CM portal
  production/BOM.csv             BOM export from the schematic
  production/manifest.json       file list + sha256 + tool versions
  production/esp8266_controller_gerbers.zip

Refuses to run if the board is missing or kicad-cli is absent - a partial
release directory that looks complete is worse than none.

Usage:
  python tools/release.py --board hardware/board.kicad_pcb --sch hardware/board.kicad_sch
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROD = os.path.join(ROOT, "production")
GERB = os.path.join(PROD, "gerbers")
ASM = os.path.join(PROD, "assembly")


def run(cmd, dry=False):
    print("  $ " + " ".join(cmd))
    if dry:
        return 0, ""
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print("    FAILED: " + (p.stderr or p.stdout).strip()[:400])
    return p.returncode, p.stdout


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", default="hardware/board.kicad_pcb")
    ap.add_argument("--sch", default="hardware/board.kicad_sch")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    board = os.path.join(ROOT, args.board)
    sch = os.path.join(ROOT, args.sch)
    cli = shutil.which("kicad-cli")

    print("release: 180x100 single-layer industrial controller")
    if not cli:
        print("\nERROR: kicad-cli not on PATH.")
        print("  Windows: C:\\Program Files\\KiCad\\9.0\\bin\\kicad-cli.exe")
        print("  Add it to PATH, or pass it in by editing CLI below.")
        return 2
    if not os.path.exists(board):
        print("\nERROR: board not found: %s" % board)
        print("  Export the netlist and run 'Update PCB from Schematic' first,")
        print("  then place with tools/place_from_csv.py and route.")
        return 2

    for d in (GERB, ASM):
        os.makedirs(d, exist_ok=True)

    ok = True
    ok &= run([cli, "pcb", "export", "gerbers", "--output", GERB + os.sep,
               board], args.dry_run)[0] == 0
    ok &= run([cli, "pcb", "export", "drill", "--output", GERB + os.sep,
               "--format", "excellon", "--excellon-units", "mm",
               "--excellon-zeros-format", "decimal",
               "--excellon-separate-th", "--drill-origin", "absolute",
               board], args.dry_run)[0] == 0
    ok &= run([cli, "pcb", "export", "pos", "--output",
               os.path.join(ASM, "board.pos"), "--format", "ascii",
               "--units", "mm", "--use-drill-file-origin", board],
              args.dry_run)[0] == 0
    ok &= run([cli, "pcb", "export", "pos", "--output",
               os.path.join(ASM, "board.csv"), "--format", "csv",
               "--units", "mm", "--use-drill-file-origin", board],
              args.dry_run)[0] == 0
    if os.path.exists(sch):
        ok &= run([cli, "sch", "export", "bom", "--output",
                   os.path.join(PROD, "BOM.csv"), sch], args.dry_run)[0] == 0
    else:
        print("  WARN: %s missing - BOM not exported" % sch)

    if not ok:
        print("\nrelease INCOMPLETE - one or more exports failed. Do not ship.")
        return 1

    if not args.dry_run:
        files = []
        for root, _, fs in os.walk(GERB):
            for f in fs:
                p = os.path.join(root, f)
                files.append(dict(path=os.path.relpath(p, ROOT),
                                  sha256=sha256(p), bytes=os.path.getsize(p)))
        for f in ("board.pos", "board.csv"):
            p = os.path.join(ASM, f)
            if os.path.exists(p):
                files.append(dict(path=os.path.relpath(p, ROOT),
                                  sha256=sha256(p), bytes=os.path.getsize(p)))
        man = dict(project="esp8266_industrial_shield",
                   board="180x100 mm, 2-layer stackup used as single-layer (B.Cu routing)",
                   generated=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   kicad_cli=cli, files=files)
        with open(os.path.join(PROD, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(man, f, indent=2)
        shutil.make_archive(os.path.join(PROD, "esp8266_controller_gerbers"),
                            "zip", GERB)
        print("wrote %d files + manifest.json + gerber zip" % len(files))

    print("release OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
