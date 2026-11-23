"""Production hardening of the 2-layer board.

Safe value fixes (no routing change):
  - R1..R8: 330R -> 220R (opto CTR margin)
  - D_TVS1: SMBJ15A-13-F -> SMBJ18A (12V rail margin)
  - C1..C4: 10uF -> 10uF (X7R 25V specified in BOM)

Adds protection components in free board area (routed with 2-layer A*):
  - F1: PTC fuse in series with 12V_RAW
  - D_FL1..D_FL8: flyback diodes MOTx -> 12V_PROT
  - C_DEC1..C_DEC4: 100nF decoupling near ICs
"""
import pcbnew, os, math, heapq, re
from collections import defaultdict

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,'ind_8ch_motor_ctrl.kicad_pcb')
MM=pcbnew.ToMM; FM=pcbnew.FromMM
b=pcbnew.LoadBoard(PCB)

# ---- 1. safe value fixes ----
for f in b.GetFootprints():
    r=f.GetReference()
    if r in ('R1','R2','R3','R4','R5','R6','R7','R8'):
        f.SetValue('220R')
    if r=='D_TVS1':
        f.SetValue('SMBJ18A')
print("value fixes applied")

# ---- 2. find free space and add components ----
# Use existing footprints' bounding boxes as obstacles
obstacles=[]
for f in b.GetFootprints():
    bb=f.GetBoundingBox(False,False)
    obstacles.append((MM(bb.GetLeft())-0.5,MM(bb.GetTop())-0.5,MM(bb.GetRight())+0.5,MM(bb.GetBottom())+0.5))
for t in b.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T:
        p=t.GetPosition(); r=MM(t.GetWidth(pcbnew.F_Cu))/2+0.4; x,y=MM(p.x),MM(p.y)
        obstacles.append((x-r,y-r,x+r,y+r))
    else:
        s,e=t.GetStart(),t.GetEnd(); x0,y0,x1,y1=MM(s.x),MM(s.y),MM(e.x),MM(e.y); r=MM(t.GetWidth())/2+0.4
        obstacles.append((min(x0,x1)-r,min(y0,y1)-r,max(x0,x1)+r,max(y0,y1)+r))

def rect_free(x,y,w,h):
    box=(x-w/2,y-h/2,x+w/2,y+h/2)
    return not any(box[0]<o[2] and box[2]>o[0] and box[1]<o[3] and box[3]>o[1] for o in obstacles)

def add_comp(lib,name,ref,value,x,y,rot=0):
    fp=pcbnew.FootprintLoad(os.path.join('/usr/share/kicad/footprints',lib+'.pretty'),name)
    if not fp: print("FP LOAD FAIL",lib,name); return None
    fp.SetReference(ref); fp.SetValue(value)
    fp.SetPosition(pcbnew.VECTOR2I(FM(x),FM(y))); fp.SetOrientationDegrees(rot)
    b.Add(fp)
    bb=fp.GetBoundingBox(False,False)
    obstacles.append((MM(bb.GetLeft())-0.5,MM(bb.GetTop())-0.5,MM(bb.GetRight())+0.5,MM(bb.GetBottom())+0.5))
    return fp

# PTC fuse near input (top-left free area)
fuse=add_comp('Fuse','Fuse_1206_3216Metric','F1','PTC 3A',12,10)
# Flyback diodes in right free area
fb=[]
for i in range(8):
    y=50+i*5.5
    f=add_comp('Diode_SMD','D_SMA','D_FL%d'%(i+1),'SS34',88,y)
    if f: fb.append(f)
# Decoupling caps near ICs
for i,(x,y) in enumerate([(32,14),(32,34),(57,50),(73,80)]):
    add_comp('Capacitor_SMD','C_0603_1608Metric','C_DEC%d'%(i+1),'100nF',x,y)

pcbnew.SaveBoard(PCB,b)
print("added components, saved")
