import pcbnew, os
LIBDIR=r"C:\Users\aswin\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints"
cands=[
 ("TerminalBlock.pretty","TerminalBlock_MaiXu_MX126-5.0-20P_1x20_P5.00mm"),
 ("TerminalBlock_Altech.pretty","Altech_AK100_1x20_P5.00mm"),
 ("TerminalBlock_Altech.pretty","Altech_AK300_1x20_P5.00mm_45-Degree"),
 ("TerminalBlock_CUI.pretty","TerminalBlock_CUI_TB007-508-20_1x20_P5.08mm_Horizontal"),
]
for lib,name in cands:
    f=pcbnew.FootprintLoad(os.path.join(LIBDIR,lib),name)
    if not f: print(name,"NOT FOUND"); continue
    bb=f.GetBoundingBox(False,False); cb=f.GetCourtyard(pcbnew.F_CrtYd)
    cbb=cb.BBox() if cb else None
    pads=sorted(f.Pads(),key=lambda p:int(p.GetNumber()))
    p1,pn=pads[0].GetPosition(),pads[-1].GetPosition()
    print(f"\n{name}")
    print(f"  bbox WxH = {pcbnew.ToMM(bb.GetWidth()):.2f} x {pcbnew.ToMM(bb.GetHeight()):.2f} mm")
    print(f"  pad1->pad20 span = {pcbnew.ToMM(pn.x-p1.x):.2f} mm ; pitch = {pcbnew.ToMM(pn.x-p1.x)/19:.3f} mm")
    if cbb: print(f"  courtyard x[{pcbnew.ToMM(cbb.GetLeft()):.2f},{pcbnew.ToMM(cbb.GetRight()):.2f}] y[{pcbnew.ToMM(cbb.GetTop()):.2f},{pcbnew.ToMM(cbb.GetBottom()):.2f}]")
    print(f"  pad size {pcbnew.ToMM(pads[0].GetSize().x):.2f} x {pcbnew.ToMM(pads[0].GetSize().y):.2f} ; drill {pcbnew.ToMM(pads[0].GetDrillSize().x):.2f}")
