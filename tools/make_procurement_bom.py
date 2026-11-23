"""Generate a procurement-grade BOM with manufacturer, ratings, RoHS and India notes.

MPNs are RECOMMENDED equivalents based on the schematic values/footprints;
they must be confirmed with the distributor before placing an order.
"""
import os, csv
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'fab','BOM_procurement.csv')

# refgroup, value, recommended MPN, manufacturer, critical spec, qty, RoHS, note
R=[
 ('R_J1..R_J5','0R','RC1206FR-070RL','Yageo','1206 1% 1/4W',5,'RoHS','0-ohm links; DNP optional'),
 ('R19','10k','RC1206FR-0710KL','Yageo','1206 1% 1/4W',1,'RoHS','ESP32 EN pull-up'),
 ('R1..R8','330R','RC1206FR-07330RL','Yageo','1206 1% 1/4W',8,'RoHS','LED drive; 220R recommended for CTR margin'),
 ('R9..R12','2.2k','RC1206FR-072K2L','Yageo','1206 1% 1/4W',4,'RoHS','Field sensor; use 0.5W rated part for 24V'),
 ('R13..R18','4.7k','RC1206FR-074K7L','Yageo','1206 1% 1/4W',6,'RoHS','I2C + sensor pull-ups'),
 ('C1..C4','10uF','CC1206KKX7R9BB106','Yageo','1206 X7R 10V (or 16V)',4,'RoHS','CONFIRM X7R/10V min - avoid 6.3V X5R'),
 ('C_BULK1/2','220uF/25V','UPW1E221MPD','Nichicon','Radial 6.3x7.7 25V 105C',2,'RoHS','105C rated required for industrial'),
 ('L1','33uH','SRR1260-330M','Bourns','33uH Isat>=2.5A',1,'RoHS','Verify saturation current'),
 ('U_MCU1','ESP32-WROOM-32E','ESP32-WROOM-32E','Espressif','4MB flash 2.4GHz Wi-Fi+BT',1,'RoHS/REACH','WPC ETA required in India - see report'),
 ('U_BUCK1','XL1509-5.0','XL1509-5.0E1','XLSEMI','5V 2A buck SOIC-8',1,'CONFIRM Pb-free','Check RoHS suffix with distributor'),
 ('U_LDO1','AMS1117-3.3','AMS1117-3.3','Diodes Inc / AMS','3.3V 1A SOT-223',1,'CONFIRM Pb-free','Thermal: check load vs 0.85W @500mA'),
 ('U_DRV1','ULN2803','ULN2803A','TI / ST','8-channel sink SOIC-18W',1,'RoHS',"Use 'A' revision"),
 ('U1..U6','LTV-827S','LTV-827S','Lite-On','Dual opto SOP-8',6,'CONFIRM RoHS rank','Prefer CTR rank >=100% if available'),
 ('D_TVS1','SMBJ15A-13-F','SMBJ15A-13-F','Diodes Inc','15V TVS SMB',1,'RoHS (-F)','Consider SMBJ18A for margin'),
 ('D1,D2','SS34','SS34','Diodes Inc / ON','3A 40V Schottky SMB',2,'CONFIRM Pb-free','Reverse polarity + buck freewheel'),
 ('J_IN','INPUT','TB007-508-20','CUI','20-pos 5.08mm horizontal TB',1,'RoHS','Obtain CoC'),
 ('J_OUT','OUTPUT','TB007-508-20','CUI','20-pos 5.08mm horizontal TB',1,'RoHS','Obtain CoC'),
]
with open(OUT,'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    w.writerow(['RefGroup','Value','Recommended_MPN','Manufacturer','Critical_Spec','Qty','RoHS_Status','Notes'])
    w.writerows(R)
print('wrote',OUT,'rows',len(R))
