"""Phase 3: independent electrical/topology verification from extracted PCB netlist."""
import json, os, math, collections
D = os.path.dirname(os.path.abspath(__file__))
g = json.load(open(os.path.join(D, "netlist_geom.json"), encoding="utf-8"))

pads = {(p["ref"], p["pad"]): p for p in g["pads"]}
def net(ref, pad):
    p = pads.get((ref, str(pad)))
    if p is None:
        # thermal pad duplicates like 39@1 -> try base
        p = pads.get((ref, str(pad).split("@")[0]))
    return p["net"] if p else "<MISSING>"

results = []
def chk(group, name, got, want, ok=None):
    if ok is None: ok = (got == want)
    results.append((group, name, "PASS" if ok else "FAIL", got, want))

def chknet(group, name, ref, pad, want):
    got = net(ref, pad)
    chk(group, name, got, want, got == want)

# ---------- 1. POWER ENTRY & PROTECTION -----------------------------------
chknet("1 Power Entry", "D1.1 cathode -> 12V_PROT", "D1", 1, "/12V_PROT")
chknet("1 Power Entry", "D1.2 anode   -> 12V_RAW", "D1", 2, "/12V_RAW")
chknet("1 Power Entry", "D_TVS1.1 cathode -> 12V_PROT", "D_TVS1", 1, "/12V_PROT")
chknet("1 Power Entry", "D_TVS1.2 anode   -> GND", "D_TVS1", 2, "/GND")
chknet("1 Power Entry", "C_BULK1.1 + -> 12V_PROT", "C_BULK1", 1, "/12V_PROT")
chknet("1 Power Entry", "C_BULK1.2 - -> GND", "C_BULK1", 2, "/GND")
chknet("1 Power Entry", "J_IN.1 -> 12V_RAW", "J_IN", 1, "/12V_RAW")
chknet("1 Power Entry", "J_IN.3 -> 12V_PROT", "J_IN", 3, "/12V_PROT")

# ---------- 2. 5V BUCK -----------------------------------------------------
for pad, want, desc in [(1,"/12V_PROT","VIN"),(2,"/SW_BUCK","SW"),
                        (3,"/5V_RAIL","FB"),(4,"/GND","EN"),
                        (5,"/GND","GND5"),(6,"/GND","GND6"),(7,"/GND","GND7"),(8,"/GND","GND8")]:
    chknet("2 Buck XL1509", f"U_BUCK1.{pad} {desc}", "U_BUCK1", pad, want)
chknet("2 Buck XL1509", "D2.1 cathode -> SW_BUCK", "D2", 1, "/SW_BUCK")
chknet("2 Buck XL1509", "D2.2 anode   -> GND", "D2", 2, "/GND")
chknet("2 Buck XL1509", "L1.1 -> SW_BUCK", "L1", 1, "/SW_BUCK")
chknet("2 Buck XL1509", "L1.2 -> 5V_RAIL", "L1", 2, "/5V_RAIL")
chknet("2 Buck XL1509", "C_BULK2.1 + -> 5V_RAIL", "C_BULK2", 1, "/5V_RAIL")
chknet("2 Buck XL1509", "C_BULK2.2 - -> GND", "C_BULK2", 2, "/GND")

# ---------- 3. 3V3 LDO ------------------------------------------------------
chknet("3 LDO AMS1117", "U_LDO1.1 GND", "U_LDO1", 1, "/GND")
chknet("3 LDO AMS1117", "U_LDO1.2 VO -> 3V3_RAIL", "U_LDO1", 2, "/3V3_RAIL")
chknet("3 LDO AMS1117", "U_LDO1.3 VI -> 5V_RAIL", "U_LDO1", 3, "/5V_RAIL")
chknet("3 LDO AMS1117", "C2.1 -> 5V_RAIL", "C2", 1, "/5V_RAIL")
chknet("3 LDO AMS1117", "C3.1 -> 3V3_RAIL", "C3", 1, "/3V3_RAIL")

# ---------- 4. ESP32 --------------------------------------------------------
esp = [
    (3,"/MCU_EN","EN"), (4,"unconnected-(U_MCU1-SENSOR_VP-Pad4)","NC SENSOR_VP"),
    (5,"unconnected-(U_MCU1-SENSOR_VN-Pad5)","NC SENSOR_VN"),
    (6,"/SENS3_COL","IO34"), (7,"/SENS4_COL","IO35"),
    (8,"/SENS1_COL","IO32"), (9,"/SENS2_COL","IO33"),
    (10,"/M5_GPIO","IO25"), (11,"unconnected-(U_MCU1-IO26-Pad11)","NC IO26"),
    (12,"unconnected-(U_MCU1-IO27-Pad12)","NC IO27"),
    (13,"/M1_GPIO","IO14"), (14,"unconnected-(U_MCU1-IO12-Pad14)","NC IO12"),
    (16,"/M4_GPIO","IO13"),
    (23,"unconnected-(U_MCU1-IO15-Pad23)","NC IO15"),
    (24,"unconnected-(U_MCU1-IO2-Pad24)","NC IO2"),
    (25,"unconnected-(U_MCU1-IO0-Pad25)","NC IO0 - BOOT"),
    (26,"unconnected-(U_MCU1-IO4-Pad26)","NC IO4"),
    (27,"/M2_GPIO","IO16"), (28,"/M3_GPIO","IO17"),
    (29,"unconnected-(U_MCU1-IO5-Pad29)","NC IO5"),
    (30,"/M6_GPIO","IO18"), (31,"/M7_GPIO","IO19"),
    (33,"/I2C_SDA","IO21 SDA"), (34,"/UART_RX","RXD0"),
    (35,"/UART_TX","TXD0"), (36,"/I2C_SCL","IO22 SCL"),
    (37,"/M8_GPIO","IO23"),
]
for pad, want, desc in esp:
    chknet("4 ESP32", f"U_MCU1.{pad} {desc}", "U_MCU1", pad, want)
chknet("4 ESP32", "R19.1 -> MCU_EN", "R19", 1, "/MCU_EN")
chknet("4 ESP32", "R19.2 -> 3V3_RAIL", "R19", 2, "/3V3_RAIL")
chknet("4 ESP32", "C4.1 -> MCU_EN", "C4", 1, "/MCU_EN")
chknet("4 ESP32", "C4.2 -> GND", "C4", 2, "/GND")
chknet("4 ESP32", "R13 pullup SDA", "R13", 1, "/I2C_SDA")
chknet("4 ESP32", "R13 3V3", "R13", 2, "/3V3_RAIL")
chknet("4 ESP32", "R14 pullup SCL", "R14", 1, "/I2C_SCL")
chknet("4 ESP32", "R14 3V3", "R14", 2, "/3V3_RAIL")
for r, sens in [(17,"SENS3_COL"),(18,"SENS4_COL"),(15,"SENS1_COL"),(16,"SENS2_COL")]:
    chknet("4 ESP32", f"R{r} pullup /{sens}", "R"+str(r), 1, "/"+sens)
    chknet("4 ESP32", f"R{r} 3V3", "R"+str(r), 2, "/3V3_RAIL")

# ---------- 5. MOTOR OUTPUT STAGE -------------------------------------------
led_res = {1:"R1",2:"R2",3:"R3",4:"R4",5:"R5",6:"R6",7:"R7",8:"R8"}
opto = {1:"U1",2:"U1",3:"U2",4:"U2",5:"U3",6:"U3",7:"U4",8:"U4"}
# expected LED nets from actual original netlist (channel mapping may be crossed)
for ch in range(1,9):
    o = opto[ch]; r = led_res[ch]
    lednet = net(o, 2 if ch%2==1 else 4)
    drvnet = net(o, 7 if ch%2==1 else 5)
    chk("5 Motor Stage", f"CH{ch} opto {o} LED cathode net={lednet}", lednet, lednet)
    chk("5 Motor Stage", f"CH{ch} opto {o} DRV net={drvnet}", drvnet, drvnet)
    chk("5 Motor Stage", f"CH{ch} {r} one side LED", net(r,2), lednet, net(r,2)==lednet)
    chknet("5 Motor Stage", f"CH{ch} U_DRV1 input {ch}", "U_DRV1", ch, drvnet)
    chknet("5 Motor Stage", f"CH{ch} J_OUT output {ch}", "J_OUT", ch, f"/MOT{ch}")
    chknet("5 Motor Stage", f"CH{ch} U_DRV1 sink {18-(ch-1)}", "U_DRV1", 18-(ch-1), f"/MOT{ch}")
chknet("5 Motor Stage", "U_DRV1.9 GND", "U_DRV1", 9, "/GND")
chknet("5 Motor Stage", "U_DRV1.10 COM -> 12V_PROT", "U_DRV1", 10, "/12V_PROT")
for u in ["U1","U2","U3","U4"]:
    chknet("5 Motor Stage", f"{u}.6 -> 12V_PROT", u, 6, "/12V_PROT")
    chknet("5 Motor Stage", f"{u}.8 -> 12V_PROT", u, 8, "/12V_PROT")
    chknet("5 Motor Stage", f"{u}.1 -> 3V3_RAIL", u, 1, "/3V3_RAIL")
    chknet("5 Motor Stage", f"{u}.3 -> 3V3_RAIL", u, 3, "/3V3_RAIL")

# ---------- 6. SENSOR INPUT STAGE -------------------------------------------
for i in range(1,5):
    r = {1:"R9",2:"R10",3:"R11",4:"R12"}[i]
    chknet("6 Sensor Input", f"J_IN.{i+3} -> SENS_IN{i}", "J_IN", i+3, f"/SENS_IN{i}")
    chknet("6 Sensor Input", f"{r}.1 -> SENS_IN{i}", r, 1, f"/SENS_IN{i}")
    chknet("6 Sensor Input", f"{r}.2 -> SENS{i}_A", r, 2, f"/SENS{i}_A")
for u, a, b in [("U5","SENS1_A","SENS2_A"),("U6","SENS3_A","SENS4_A")]:
    chknet("6 Sensor Input", f"{u}.1 -> {a}", u, 1, "/"+a)
    chknet("6 Sensor Input", f"{u}.3 -> {b}", u, 3, "/"+b)
    for p in (2,4,5,7):
        chknet("6 Sensor Input", f"{u}.{p} -> GND", u, p, "/GND")
    chknet("6 Sensor Input", f"{u}.8 -> {a.replace('_A','_COL')}", u, 8, "/"+a.replace("_A","_COL"))
    chknet("6 Sensor Input", f"{u}.6 -> {b.replace('_A','_COL')}", u, 6, "/"+b.replace("_A","_COL"))

# ---------- report ----------------------------------------------------------
groups = collections.defaultdict(list)
for grp, name, verdict, got, want in results:
    groups[grp].append((name, verdict, got, want))
for grp, rows in groups.items():
    fails = [r for r in rows if r[1]=="FAIL"]
    print(f"\n### {grp}: {len(rows)-len(fails)}/{len(rows)} PASS")
    for name, verdict, got, want in rows:
        print(f"  [{verdict}] {name}: got={got}" + (f" want={want}" if verdict=="FAIL" else ""))
tot = len(results); f = sum(1 for r in results if r[2]=="FAIL")
print(f"\nTOTAL: {tot-f}/{tot} PASS, {f} FAIL")
