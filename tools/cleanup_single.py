"""Cosmetic cleanup for the single-layer board."""
import pcbnew, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,"ind_8ch_motor_ctrl.kicad_pcb")
MM=pcbnew.FromMM; V=lambda x,y: pcbnew.VECTOR2I(int(MM(x)),int(MM(y)))
b=pcbnew.LoadBoard(PCB)

# TB silk crossing board edge -> documentation layer
for ref in ("J_IN","J_OUT"):
    fp=b.FindFootprintByReference(ref)
    fields={"Reference":fp.Reference(),"Value":fp.Value()}
    for item in list(fp.GraphicalItems()):
        if item.GetLayer()!=pcbnew.F_SilkS: continue
        bb=item.GetBoundingBox()
        l,r,t,bo=MM(bb.GetLeft()),MM(bb.GetRight()),MM(bb.GetTop()),MM(bb.GetBottom())
        if l<0.6 or r>99.4 or t<0.6 or bo>99.4:
            item.SetLayer(pcbnew.Cmts_User)
    for name,txt in fields.items():
        txt.SetLayer(pcbnew.F_SilkS if name=="Reference" else pcbnew.F_Fab)
        txt.SetPosition(V(14,50) if ref=="J_IN" else V(86,50))
# NC labels inboard
for t in b.GetDrawings():
    if isinstance(t,pcbnew.PCB_TEXT) and t.GetText()=="NC":
        p=t.GetPosition(); x=pcbnew.ToMM(p.x)
        t.SetPosition(V(11.5 if x<50 else 88.5,pcbnew.ToMM(p.y)))
# move specific refs to F.Fab
for ref,x,y in [("D_TVS1",28,8),("C_BULK1",38,6),("C_BULK2",38,24),("C3",38,36),("D2",48,2)]:
    f=b.FindFootprintByReference(ref)
    if f:
        f.Reference().SetPosition(V(x,y)); f.Reference().SetLayer(pcbnew.F_Fab)
pcbnew.SaveBoard(PCB,b)
print("cleaned")
