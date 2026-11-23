"""
Single-layer floor plan v3 (corrected spacing):
  - power rows top-left, MCU centre-left near J_IN I2C/UART pins
  - motor channel strip left-to-right across the middle-right
  - sensor resistors near J_IN sensor pins (left), sensor optos bottom
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
 # power supply rows (top-left)
 "D_TVS1":(17,8,0), "C_BULK1":(27,8,0), "C1":(35,8,0),
 "D1":(17,16,180), "U_BUCK1":(27,16,0), "L1":(39,16,0),
 "U_LDO1":(17,26,0), "C_BULK2":(27,26,0), "D2":(39,26,0),
 "C3":(27,34,0), "C2":(35,33,0), "C4":(17,34,0), "R19":(20,38,0),
 # MCU centre-left
 "U_MCU1":(46,50,0),
 # I2C pull-ups
 "R13":(17,43,90), "R14":(17,49,90),
 # motor channel strip
 "R1":(60,40,0), "R2":(60,45.5,0), "R3":(60,51,0), "R4":(60,56.5,0),
 "R5":(60,62,0), "R6":(60,67.5,0), "R7":(60,73,0), "R8":(60,78.5,0),
 "U1":(70,40,0), "U2":(70,52,0), "U3":(70,64,0), "U4":(70,76,0),
 "U_DRV1":(82,58,0),
 # sensor stage
 "R9":(19,62,0), "R10":(19,67,0), "R11":(19,72,0), "R12":(19,77,0),
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
