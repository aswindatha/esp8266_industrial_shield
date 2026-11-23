r"""
Build the industrial 100x100 mm, 2-layer version of ind_8ch_motor_ctrl.

- 100 x 100 mm outline
- Two 20-position 5.08 mm CUI terminal blocks on opposite (left/right) edges
  * J_IN  (left)  = all board INPUTS
  * J_OUT (right) = all board OUTPUTS
- Unused TB positions left unconnected and labelled NC
- Clean functional-block placement
- 2-layer stackup; B.Cu reserved for a solid ground plane

Run with KiCad's python:
    & "C:\Users\aswin\AppData\Local\Programs\KiCad\10.0\bin\python.exe" tools/build_v2.py
"""
import pcbnew, os, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, "ind_8ch_motor_ctrl.kicad_pcb")
DST = os.path.join(ROOT, "ind_8ch_motor_ctrl.kicad_pcb")
FPDIR = r"C:\Users\aswin\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints"
TB_LIB = "TerminalBlock_CUI.pretty"
TB_NAME = "TerminalBlock_CUI_TB007-508-20_1x20_P5.08mm_Horizontal"

MM = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))

# ---------------------------------------------------------------------------
# Terminal-block pin maps.  Pin 1 is at the TOP of each vertical block.
# ---------------------------------------------------------------------------
IN_PINS = {
    1: "12V_RAW", 2: "GND", 3: "12V_PROT",
    4: "SENS_IN1", 5: "SENS_IN2", 6: "SENS_IN3", 7: "SENS_IN4",
    8: "3V3_RAIL", 9: "I2C_SDA", 10: "I2C_SCL",
    11: "UART_TX", 12: "UART_RX",
}
OUT_PINS = {
    1: "MOT1", 2: "MOT2", 3: "MOT3", 4: "MOT4",
    5: "MOT5", 6: "MOT6", 7: "MOT7", 8: "MOT8",
    9: "12V_PROT",
}
USED = set(IN_PINS.values()) | set(OUT_PINS.values())

# ---------------------------------------------------------------------------
# Floor plan: (x, y, rotation).  Coordinates are footprint centres except for
# the two terminal blocks, whose position is pad 1.
# ---------------------------------------------------------------------------
PLACE = {
    # ---- power supply (top-left) -------------------------------------
    "D_TVS1":   (18.0, 12.0,   0),
    "D1":       (18.0, 18.0, 180),
    "C_BULK1":  (29.0, 10.0,   0),
    "C1":       (37.0,  8.0,   0),
    "U_BUCK1":  (29.0, 19.0,   0),
    "L1":       (41.0, 17.0,   0),
    "D2":       (46.0,  6.0,   0),
    "C2":       (49.0, 27.0,   0),
    "C_BULK2":  (41.0, 28.0,   0),
    "U_LDO1":   (29.0, 28.0,   0),
    "C3":       (25.0, 39.0,   0),
    "C4":       (20.0, 36.0,   0),
    "R19":      (22.0, 24.0,   0),
    # ---- MCU (top-centre, antenna toward top edge) -------------------
    "U_MCU1":   (64.0, 21.0,   0),
    # ---- I2C / UART pull-ups (left, beside TB) -----------------------
    "R13":      (17.0, 43.0,  90),
    "R14":      (17.0, 49.0,  90),
    # ---- motor-channel LED resistors ---------------------------------
    "R1":       (46.0, 39.0,   0),
    "R2":       (46.0, 44.5,   0),
    "R3":       (46.0, 50.0,   0),
    "R4":       (46.0, 55.5,   0),
    "R5":       (46.0, 61.0,   0),
    "R6":       (46.0, 66.5,   0),
    "R7":       (46.0, 72.0,   0),
    "R8":       (46.0, 77.5,   0),
    # ---- motor optocouplers ------------------------------------------
    "U1":       (34.0, 40.0,   0),
    "U2":       (34.0, 52.0,   0),
    "U3":       (34.0, 64.0,   0),
    "U4":       (34.0, 76.0,   0),
    # ---- ULN2803 driver (faces right TB) -----------------------------
    "U_DRV1":   (76.0, 47.0,   0),
    # ---- sensor interface (bottom) -----------------------------------
    "U5":       (30.0, 88.0, 180),
    "U6":       (52.0, 88.0, 180),
    "R15":      (21.0, 80.0,   0),
    "R16":      (21.0, 85.0,   0),
    "R17":      (21.0, 90.0,   0),
    "R18":      (21.0, 95.0,   0),
    "R9":       (62.0, 80.0,   0),
    "R10":      (62.0, 85.0,   0),
    "R11":      (62.0, 90.0,   0),
    "R12":      (62.0, 95.0,   0),
    # ---- zero-ohm links ----------------------------------------------
    "R_J1":     (70.0, 80.0,   0),
    "R_J2":     (70.0, 85.0,   0),
    "R_J3":     (70.0, 90.0,   0),
    "R_J4":     (84.0, 62.0,   0),
    "R_J5":     (70.0, 95.0,   0),
    # ---- mounting holes ----------------------------------------------
    "MH1":      (16.0,  5.0,   0),
    "MH2":      (84.5,  5.0,   0),
    "MH3":      (16.0, 95.0,   0),
    "MH4":      (84.5, 95.0,   0),
}

TB_POS = {"J_IN": (6.0, 1.75), "J_OUT": (94.0, 1.75)}


def log(*a):
    print(*a)


def main():
    b = pcbnew.LoadBoard(SRC)
    log("Loaded", len(list(b.GetFootprints())), "footprints")

    # ---- 1. wipe old routing -----------------------------------------
    for t in list(b.GetTracks()):
        b.RemoveNative(t)
    for z in list(b.Zones()):
        b.RemoveNative(z)
    log("Cleared tracks and zones")

    # ---- 2. delete the five old connectors ---------------------------
    for ref in ["J_PWR1", "J_MOT1", "J_SENS1", "J_I2C1", "J_PROG1"]:
        fp = b.FindFootprintByReference(ref)
        if fp:
            b.RemoveNative(fp)
            log("Removed", ref)

    # ---- 3. board outline 100 x 100 mm -------------------------------
    for d in list(b.GetDrawings()):
        if d.GetLayer() == pcbnew.Edge_Cuts:
            b.RemoveNative(d)
    corners = [(0, 0), (100, 0), (100, 100), (0, 100)]
    for i in range(4):
        seg = pcbnew.PCB_SHAPE(b)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(V(*corners[i]))
        seg.SetEnd(V(*corners[(i + 1) % 4]))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(MM(0.1))
        b.Add(seg)
    log("Board outline set to 100 x 100 mm")

    # ---- 4. add the two 20-pin terminal blocks -----------------------
    nets = {n: b.FindNet("/" + n) for n in USED}
    bad = [n for n, net in nets.items() if net is None]
    if bad:
        raise RuntimeError("Missing nets in board: " + ", ".join(bad))
    for ref, pinmap in (("J_IN", IN_PINS), ("J_OUT", OUT_PINS)):
        fp = pcbnew.FootprintLoad(os.path.join(FPDIR, TB_LIB), TB_NAME)
        if fp is None:
            raise RuntimeError("Terminal block footprint not found")
        fp.SetReference(ref)
        fp.SetValue("INPUT" if ref == "J_IN" else "OUTPUT")
        fp.SetPosition(V(*TB_POS[ref]))
        fp.SetOrientationDegrees(-90)
        b.Add(fp)
        for pad in fp.Pads():
            num = int(pad.GetNumber())
            netname = pinmap.get(num)
            if netname:
                pad.SetNet(nets[netname])
            else:
                pad.SetNetCode(0)
        log("Added", ref, "with", len(pinmap), "connected pins")

    # ---- 5. re-place everything else ----------------------------------
    missing = []
    for ref, (x, y, rot) in PLACE.items():
        fp = b.FindFootprintByReference(ref)
        if fp is None:
            missing.append(ref)
            continue
        fp.SetPosition(V(x, y))
        fp.SetOrientationDegrees(rot)
    if missing:
        log("WARNING missing:", missing)

    # ---- 6. mark unused TB pins with silkscreen "NC" ------------------
    for ref, pinmap in (("J_IN", IN_PINS), ("J_OUT", OUT_PINS)):
        fp = b.FindFootprintByReference(ref)
        for pad in fp.Pads():
            num = int(pad.GetNumber())
            if num in pinmap:
                continue
            p = pad.GetPosition()
            # place the NC text just inboard of the pad
            inward = MM(3.2) if ref == "J_IN" else MM(-3.2)
            txt = pcbnew.PCB_TEXT(b)
            txt.SetText("NC")
            txt.SetPosition(pcbnew.VECTOR2I(p.x + inward, p.y))
            txt.SetLayer(pcbnew.F_SilkS)
            txt.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8)))
            txt.SetTextThickness(MM(0.12))
            b.Add(txt)

    # ---- 7. pin-header style legends ----------------------------------
    legends = [
        (12.5, 4.0, "J_IN  INPUT  1:12V_RAW 2:GND 3:12VP 4-7:SENS1-4 8:3V3 9:SDA 10:SCL 11:TX 12:RX  13-20:NC"),
        (87.5, 4.0, "J_OUT OUTPUT  1-8:MOT1-8  9:12VP  10-20:NC"),
    ]
    for x, y, text in legends:
        # short legend only; long text handled in documentation
        pass

    # ---- 8. save -------------------------------------------------------
    pcbnew.SaveBoard(DST, b)
    log("Saved", DST)

    # ---- report --------------------------------------------------------
    b2 = pcbnew.LoadBoard(DST)
    bb = b2.GetBoardEdgesBoundingBox()
    log("Board %.2f x %.2f mm" % (pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())))
    log("Footprints:", len(list(b2.GetFootprints())))
    log("Nets:", len(list(b2.GetNetsByNetcode())))


if __name__ == "__main__":
    main()
