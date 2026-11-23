"""
Re-plan the single-layer floor plan for planar left-to-right signal flow:
  J_IN(left) -> power + MCU -> resistor column -> optos -> ULN2803 -> J_OUT(right)
  Sensor interface along the bottom.
"""
import pcbnew, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,"ind_8ch_motor_ctrl.kicad_pcb")
MM=pcbnew.FromMM
V=lambda x,y: pcbnew.VECTOR2I(MM(x),MM(y))
b=pcbnew.LoadBoard(PCB)

for t in list(b.GetTracks()): b.RemoveNative(t)
for z in list(b.Zones()): b.RemoveNative(z)

PLACE={
 # power (top-left, clear of MCU antenna)
 "D_TVS1":(17,12,0), "D1":(18,18,180), "C_BULK1":(27,10,0), "C1":(34,7,0),
 "U_BUCK1":(27,19,0), "L1":(39,17,0), "D2":(42,4,0), "C2":(42,34,0),
 "C_BULK2":(35,28,0), "U_LDO1":(25,28,0), "C3":(22,38,0), "C4":(18,35,0),
 "R19":(17,27,0),
 # MCU
 "U_MCU1":(56,21,0),
 # pull-ups (left, near J_IN)
 "R13":(17,43,90), "R14":(17,49,90),
 # resistor column RIGHT of MCU
 "R1":(60,40,0), "R2":(60,45.5,0), "R3":(60,51,0), "R4":(60,56.5,0),
 "R5":(60,62,0), "R6":(60,67.5,0), "R7":(60,73,0), "R8":(60,78.5,0),
 # optocouplers right of resistors
 "U1":(70,40,0), "U2":(70,52,0), "U3":(70,64,0), "U4":(70,76,0),
 # driver near right TB
 "U_DRV1":(83,58,0),
 # sensor interface (bottom)
 "U5":(30,88,180), "U6":(50,88,180),
 "R15":(19,78,0), "R16":(19,83,0), "R17":(19,88,0), "R18":(28,98,0),
 "R9":(62,88,0), "R10":(62,92,0), "R11":(62,96,0), "R12":(68,96,0),
 # zero-ohm links
 "R_J1":(40,84,0), "R_J2":(40,88,0), "R_J3":(40,92,0), "R_J4":(84,70,0), "R_J5":(40,96,0),
 # mounting holes
 "MH1":(15.5,4,0), "MH2":(86,4,0), "MH3":(15.5,96,0), "MH4":(86,96,0),
}
missing=[]
for ref,(x,y,r) in PLACE.items():
    f=b.FindFootprintByReference(ref)
    if not f: missing.append(ref); continue
    f.SetPosition(V(x,y)); f.SetOrientationDegrees(r)
print("missing:",missing)
pcbnew.SaveBoard(PCB,b)
print("placement updated, tracks cleared")
