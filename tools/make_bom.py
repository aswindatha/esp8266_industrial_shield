"""Generate a board-accurate BOM and placement report from the final PCB."""
import pcbnew, os, collections, csv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
b = pcbnew.LoadBoard(os.path.join(ROOT, "ind_8ch_motor_ctrl.kicad_pcb"))

rows = []
for fp in b.GetFootprints():
    ref = fp.GetReference()
    if ref.startswith("MH"):
        continue  # mounting holes are mechanical, listed separately
    rows.append((ref, fp.GetValue(), fp.GetFPIDAsString(),
                 len(list(fp.Pads())), fp.GetLayerName()))

rows.sort(key=lambda r: (r[1], r[0]))
with open(os.path.join(ROOT, "fab", "BOM.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Reference", "Value", "Footprint", "Pads", "Side"])
    w.writerows(rows)

# grouped BOM
groups = collections.defaultdict(list)
for ref, val, fp, pads, side in rows:
    groups[(val, fp)].append(ref)
with open(os.path.join(ROOT, "fab", "BOM_grouped.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Value", "Footprint", "Qty", "References"])
    for (val, fp), refs in sorted(groups.items()):
        w.writerow([val, fp, len(refs), ", ".join(sorted(refs))])

print("BOM lines:", len(rows), "grouped:", len(groups))
print("Mechanical holes:", sum(1 for fp in b.GetFootprints() if fp.GetReference().startswith("MH")))
