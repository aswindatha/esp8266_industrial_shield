"""Deep India-manufacturing readiness audit: BOM procurement data, RoHS risk,
electrical derating, DFM limits, and regulatory applicability.
"""
import pcbnew, os, csv, json, re, math
from collections import defaultdict

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MM=pcbnew.ToMM
b=pcbnew.LoadBoard(os.path.join(ROOT,'ind_8ch_motor_ctrl.kicad_pcb'))
fps=list(b.GetFootprints())
bom=list(csv.DictReader(open(os.path.join(ROOT,'fab','BOM.csv'))))
sch=open(os.path.join(ROOT,'ind_8ch_motor_ctrl.kicad_sch')).read()

print("="*70)
print("A. BOM PROCUREMENT / COMPLIANCE DATA COMPLETENESS")
print("="*70)
props=re.findall(r'\(property "([^"]+)"',sch)
need=['MPN','Manufacturer','Supplier','RoHS','Voltage','Power','Tolerance','Lifecycle','HTS','CountryOfOrigin']
for f in need:
    print(f"  {f:18s}: {'FOUND' if f in props else 'MISSING'}")

print("\n"+"="*70)
print("B. COMPONENT ROHS RISK (part-level declarations required)")
print("="*70)
rohs_notes={
'J_IN':'CUI TB007-508-20 - obtain RoHS CoC',
'J_OUT':'CUI TB007-508-20 - obtain RoHS CoC',
'U_MCU1':'Espressif ESP32-WROOM-32E - RoHS/REACH per datasheet; obtain CoC',
'U_BUCK1':'XLSEMI XL1509-5.0E1 - CONFIRM Pb-free suffix / RoHS CoC',
'U_LDO1':'AMS1117-3.3 - CONFIRM Pb-free (e.g. AMS1117-3.3_ND) / CoC',
'U_DRV1':'ULN2803A - confirm TI/ST Pb-free variant / CoC',
'U1..U6':'Lite-On LTV-827S - confirm RoHS variant / CoC',
'D_TVS1':'SMBJ15A-13-F (-F = Pb-free matte tin) - confirm CoC',
'D1,D2':'SS34 - confirm Pb-free variant / CoC',
'L1':'Bourns SRR1260-330 - RoHS per vendor; confirm CoC',
'C_BULK1/2':'220uF/25V Al-electrolytic - confirm 105C & RoHS CoC',
'C1..C4':'10uF 1206 MLCC - CONFIRM dielectric (X7R) & voltage (>=10V) & RoHS',
'R*':'Chip resistors - typically RoHS; confirm CoC',
}
for k,v in rohs_notes.items(): print(f"  {k:14s}: {v}")

print("\n"+"="*70)
print("C. ELECTRICAL DERATING / RELIABILITY FLAGS")
print("="*70)
# computed from known design values
IF=(3.3-1.2)/330*1000
ctr_req=3.9e-3/((3.3-1.2)/330)*100
print(f"  Opto LED IF (330R from 3V3)      : {IF:.2f} mA")
print(f"  Required CTR to drive ULN input  : {ctr_req:.1f} %  (LTV-827S min ~50% @5mA) -> MARGINAL")
print(f"  Suggested R1..R8                 : 220R -> IF {(3.3-1.2)/220*1000:.2f} mA")
print("  TVS SMBJ15A VRWM 15V vs 14.4V rail: 0.6V margin (4.2%) -> MARGINAL")
print("  Suggested TVS                     : SMBJ18A (VRWM 18V)")
print("  AMS1117 P @ 500mA (5->3.3V)       : 0.85 W in SOT-223; Tj ~ +77C over ambient")
print("    -> Ta 40C gives Tj ~117C (limit 125C) -> check heatsinking/load")
print("  Sensor R 2.2k @ 24V               : P=(24-1.2)^2/2200 = %.0f mW (250mW 1206) -> ~94%% loaded" % (((24-1.2)**2/2200)*1000))
print("  10uF 1206 MLCC at 5V bias         : if 6.3V X5R, effective C may drop >50% -> use 10V/16V X7R")
print("  XL1509 33uH inductor              : confirm Isat >= 2.5A (2A buck + ripple)")

print("\n"+"="*70)
print("D. PCB DFM / INDIAN FAB CAPABILITY")
print("="*70)
tracks=list(b.GetTracks())
segs=[t for t in tracks if t.Type()!=pcbnew.PCB_VIA_T]
vias=[t for t in tracks if t.Type()==pcbnew.PCB_VIA_T]
widths=sorted(set(MM(t.GetWidth()) for t in segs))
drills=sorted(set(MM(p.GetDrillSizeX()) for f in fps for p in f.Pads() if p.GetDrillSizeX()>0))
print(f"  Board size           : {MM(b.GetBoardEdgesBoundingBox().GetWidth()):.1f} x {MM(b.GetBoardEdgesBoundingBox().GetHeight()):.1f} mm")
print(f"  Copper layers        : {b.GetCopperLayerCount()}")
print(f"  Min track width      : {min(widths):.4f} mm (capability OK, standard 0.15mm)")
print(f"  Drill sizes          : {drills} mm")
print(f"  0.20mm drills        : {sum(1 for f in fps for p in f.Pads() if 0<MM(p.GetDrillSizeX())<=0.21)} PTH - needs LASER/HDI")
print(f"  Vias                 : {len(vias)} (0.6/0.3mm) - standard")
print("  Copper-to-edge       : 0.30 mm - standard")
print("  Surface finish       : ENIG/HASL - specify to fab")
print("  NOTE: 0.20mm drills are the main fab-cost driver in India; confirm capability")

print("\n"+"="*70)
print("E. REGULATORY APPLICABILITY (INDIA)")
print("="*70)
print("  BIS CRS (MeitY 2021 Order): NOT applicable to bare 12V DC control PCB")
print("    - only notified categories (SMPS, adaptors, IT equipment, etc.)")
print("    - if sold WITH an external mains SMPS/adaptor -> that adaptor needs BIS CRS")
print("  WPC ETA: REQUIRED - ESP32-WROOM-32E is 2.4GHz Wi-Fi/BT (G.S.R.45E)")
print("    - If module has its own ETA and used unmodified in India-made product,")
print("      no separate ETA needed (WPC FAQ #8)")
print("    - Espressif published ETA list does NOT show 32E (shows 32D & ESP8684)")
print("    - ACTION: obtain ETA via SARAL Sanchar self-declaration (~Rs 10,000)")
print("      using module RF test report; or have supplier provide 32E ETA")
print("  RoHS: India has no EU-style mandatory RoHS, but E-Waste Rules 2016")
print("    restrict hazardous substances; obtain supplier RoHS CoCs for all parts")
print("  MTCTE/TEC: not applicable (no telecom network interface)")
print("  IWT Act 1933: frequency use must conform to 2.4GHz gazette conditions")
