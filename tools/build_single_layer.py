"""
Build the SINGLE-LAYER variant (working copy). The 2-layer design is preserved in
ind_8ch_motor_ctrl_2LAYER_backup.zip and backup_2layer/.

Changes vs 2-layer version:
  - B.Cu copper removed entirely (no tracks, no vias, no zones)
  - 5.08 mm CUI terminal blocks replaced with 5.00 mm Altech AK100 20-position
    blocks (101.05 mm body instead of 103.25 mm -> ~0.5 mm overhang per end)
  - terminal blocks repositioned to y=2.5 for symmetric end overhang
"""
import pcbnew, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,"ind_8ch_motor_ctrl.kicad_pcb")
LIB=r"C:\Users\aswin\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints"
TBLIB="TerminalBlock_Altech.pretty"
TBNAME="Altech_AK100_1x20_P5.00mm"
MM=pcbnew.FromMM
V=lambda x,y: pcbnew.VECTOR2I(MM(x),MM(y))

IN_PINS={1:"12V_RAW",2:"GND",3:"12V_PROT",4:"SENS_IN1",5:"SENS_IN2",6:"SENS_IN3",7:"SENS_IN4",
         8:"3V3_RAIL",9:"I2C_SDA",10:"I2C_SCL",11:"UART_TX",12:"UART_RX"}
OUT_PINS={1:"MOT1",2:"MOT2",3:"MOT3",4:"MOT4",5:"MOT5",6:"MOT6",7:"MOT7",8:"MOT8",9:"12V_PROT"}
USED=set(IN_PINS.values())|set(OUT_PINS.values())
TB_POS={"J_IN":(6.0,2.5),"J_OUT":(94.0,2.5)}

b=pcbnew.LoadBoard(PCB)
print("loaded footprints:",len(list(b.GetFootprints())))

# 1) wipe all routing and zones (both layers)
for t in list(b.GetTracks()): b.RemoveNative(t)
for z in list(b.Zones()): b.RemoveNative(z)
print("cleared tracks/zones")

# 2) remove old TBs and add 5.00 mm ones
for ref in ("J_IN","J_OUT"):
    fp=b.FindFootprintByReference(ref)
    if fp: b.RemoveNative(fp)
nets={n:b.FindNet("/"+n) for n in USED}
for ref,pinmap in (("J_IN",IN_PINS),("J_OUT",OUT_PINS)):
    fp=pcbnew.FootprintLoad(os.path.join(LIB,TBLIB),TBNAME)
    fp.SetReference(ref); fp.SetValue("INPUT" if ref=="J_IN" else "OUTPUT")
    fp.SetPosition(V(*TB_POS[ref])); fp.SetOrientationDegrees(-90)
    b.Add(fp)
    for p in fp.Pads():
        n=int(p.GetNumber()); nm=pinmap.get(n)
        if nm: p.SetNet(nets[nm])
        else: p.SetNetCode(0)
    cb=fp.GetBoundingBox(False,False)
    print(ref,"bbox x[%.2f,%.2f] y[%.2f,%.2f]"%(pcbnew.ToMM(cb.GetLeft()),pcbnew.ToMM(cb.GetRight()),pcbnew.ToMM(cb.GetTop()),pcbnew.ToMM(cb.GetBottom())))

# 3) remove any NC silkscreen text from the old board and re-add at correct positions
for d in list(b.GetDrawings()):
    if isinstance(d,pcbnew.PCB_TEXT) and d.GetText()=="NC": b.RemoveNative(d)
for ref,pinmap in (("J_IN",IN_PINS),("J_OUT",OUT_PINS)):
    fp=b.FindFootprintByReference(ref)
    for p in fp.Pads():
        if int(p.GetNumber()) in pinmap: continue
        q=p.GetPosition(); inward=MM(3.2) if ref=="J_IN" else MM(-3.2)
        t=pcbnew.PCB_TEXT(b); t.SetText("NC")
        t.SetPosition(pcbnew.VECTOR2I(q.x+inward,q.y))
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(MM(0.8),MM(0.8))); t.SetTextThickness(MM(0.12))
        b.Add(t)

# 4) ensure no B.Cu copper exists; F.Cu only
for t in list(b.GetTracks()):
    if t.GetLayer()==pcbnew.B_Cu: b.RemoveNative(t)

pcbnew.SaveBoard(PCB,b)
b2=pcbnew.LoadBoard(PCB)
print("tracks:",len(list(b2.GetTracks())),"vias:",len([t for t in b2.GetTracks() if isinstance(t,pcbnew.PCB_VIA)]),"zones:",len(list(b2.Zones())))
print("saved single-layer base:",PCB)
