"""
Single-layer floor plan v4: left corridor x12-25 kept CLEAR for J_IN sensor /
UART / I2C fan-out; power section moved into x26-55, y4-35.
"""
import pcbnew, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB=os.path.join(ROOT,"ind_8ch_motor_ctrl.kicad_pcb")
MM=pcbnew.FromMM; V=lambda x,y: pcbnew.VECTOR2I(MM(x),MM(y))
b=pcbnew.LoadBoard(PCB)
for t in list(b.GetTracks()): b.RemoveNative(t)
for z in list(b.Zones()): b.RemoveNative(z)
for f in list(b.GetFootprints()):
    if f.GetReference().startswith("JMP"): b.RemoveNative(f)

PLACE={
 # power section (right of the clear left corridor)
 "D_TVS1":(28,8,0), "C_BULK1":(38,8,0), "C1":(58,8,0),
 "D1":(28,16,180), "U_BUCK1":(38,16,0), "L1":(49,16,0),
 "U_LDO1":(28,26,0), "C_BULK2":(38,26,0), "D2":(48,4,0),
 "C3":(38,34,0), "C2":(44,34,0), "C4":(28,34,0), "R19":(28,40,0),
 # MCU
 "U_MCU1":(46,52,0),
 # I2C pull-ups moved near MCU (out of left corridor)
 "R13":(34,40,90), "R14":(34,46,90),
 # motor channel strip
 "R1":(60,42,0), "R2":(60,47.5,0), "R3":(60,53,0), "R4":(60,58.5,0),
 "R5":(60,64,0), "R6":(60,69.5,0), "R7":(60,75,0), "R8":(60,80.5,0),
 "U1":(70,42,0), "U2":(70,54,0), "U3":(70,66,0), "U4":(70,78,0),
 "U_DRV1":(82,58,0),
 # sensor stage: series resistors in the clear left corridor near J_IN pins
 "R9":(16,62,0), "R10":(16,67,0), "R11":(16,72,0), "R12":(16,77,0),
 "U5":(30,88,180), "U6":(50,88,180),
 "R15":(19,82,0), "R16":(19,86,0), "R17":(19,90,0), "R18":(28,98,0),
 # jumpers
 "R_J1":(40,84,0), "R_J2":(40,88,0), "R_J3":(40,92,0), "R_J4":(82,70,0), "R_J5":(40,96,0),
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
