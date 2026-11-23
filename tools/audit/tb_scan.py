import pcbnew, os, glob
LIBDIR=r"C:\Users\aswin\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints"
rows=[]
for pretty in glob.glob(os.path.join(LIBDIR,"TerminalBlock*.pretty")):
    for fp in glob.glob(os.path.join(pretty,"*.kicad_mod")):
        name=os.path.basename(fp)[:-10]
        if "1x20" not in name and "20P" not in name: continue
        f=pcbnew.FootprintLoad(pretty,name)
        if not f: continue
        pads=sorted(f.Pads(),key=lambda p:int(p.GetNumber()))
        if len(pads)!=20: continue
        bb=f.GetBoundingBox(False,False)
        w=pcbnew.ToMM(bb.GetWidth()); h=pcbnew.ToMM(bb.GetHeight())
        pitch=pcbnew.ToMM(pads[-1].GetPosition().x-pads[0].GetPosition().x)/19
        rows.append((w,h,pitch,os.path.basename(pretty),name))
rows.sort()
print(f"{'W':>7} {'H':>7} {'pitch':>6}  library / name")
for w,h,p,lib,name in rows[:40]:
    print(f"{w:7.2f} {h:7.2f} {p:6.2f}  {lib.replace('.pretty','')}: {name}")
print("total candidates:",len(rows))
