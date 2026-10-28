#!/usr/bin/env python3
"""
Netlist generator + connectivity validator.

Project : ESP8266 8x 12V motor / 16x opto-isolated input controller
Board   : 170 x 100 mm, 2-layer, 1.6 mm FR-4, 1 oz Cu

Emits
  NETLIST.csv      one row per component pin -> net (machine readable)
  NET_SUMMARY.md   one row per net -> every pin on it (human readable)
  CONNECTIVITY.md  validation report (floating pins, single-pin nets)

Pin numbering notes
  U3  ESP-12F follows the KiCad RF_Module:ESP-12E symbol: pads 1-8 down the
      left edge, 9-14 the six bottom thermal pads (GND), 15-22 up the right
      edge. The physical pad order is documented in the PinName column so the
      net entry stays unambiguous even if a different symbol is used.
  U8-U11 PS2501-4: ch1 = A1/K2/C16/E15, ch2 = 3/4/14/13,
                   ch3 = 5/6/12/11, ch4 = 7/8/10/9
"""

import csv
import collections
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
PARTS = {}


def add(ref, value, fp, pins, note=""):
    PARTS[ref] = {"value": value, "fp": fp, "pins": pins, "note": note}


# ---------------------------------------------------------------- power chain
add("J1", "12V IN 5.00mm", "TerminalBlock:TerminalBlock_bornier-2_P5.00mm",
    {"1": ("VIN_RAW", "P"), "2": ("GND", "P")}, "screw terminal")

add("F1", "PTC 4A", "Fuse:Fuse_1812_4532Metric",
    {"1": ("VIN_RAW", "in"), "2": ("VIN_A", "out")}, "Bourns MF-R400")

add("D1", "SMAJ28A", "Diode_SMD:D_SMA",
    {"1": ("VIN_A", "K"), "2": ("GND", "A")}, "TVS, cathode to rail")

add("D2", "SS34", "Diode_SMD:D_SMA",
    {"1": ("+12V", "K"), "2": ("VIN_A", "A")}, "reverse polarity")

add("C1", "100uF/50V", "Capacitor_SMD:CP_Elec_6.3x7.7",
    {"1": ("+12V", "+"), "2": ("GND", "-")})
add("C2", "100nF/100V", "Capacitor_SMD:C_0805_2012Metric",
    {"1": ("+12V", "1"), "2": ("GND", "2")})
add("C3", "100nF/50V", "Capacitor_SMD:C_0805_2012Metric",
    {"1": ("+12V", "1"), "2": ("GND", "2")}, "at U1 VIN")

add("U1", "XL1509-5.0E1", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    {"1": ("+12V", "VIN"), "2": ("SW_NODE", "SW"), "3": ("+5V", "FB"),
     "4": ("+12V", "EN"), "5": ("GND", "GND"), "6": ("GND", "GND"),
     "7": ("GND", "GND"), "8": ("GND", "GND")}, "pins 5-8 = GND")

add("L1", "33uH 2A", "Inductor_SMD:L_8x8mm",
    {"1": ("SW_NODE", "1"), "2": ("+5V", "2")}, "8D43 / SRN8040")
add("D3", "SS34", "Diode_SMD:D_SMA",
    {"1": ("SW_NODE", "K"), "2": ("GND", "A")}, "freewheel")
add("C4", "220uF/25V", "Capacitor_SMD:CP_Elec_8x10.2",
    {"1": ("+5V", "+"), "2": ("GND", "-")})
add("C5", "100nF/50V", "Capacitor_SMD:C_0805_2012Metric",
    {"1": ("+5V", "1"), "2": ("GND", "2")})

add("U2", "AMS1117-3.3", "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    {"1": ("GND", "GND"), "2": ("+3V3", "VOUT"), "3": ("+5V", "VIN")},
    "tab = pin 2 = VOUT = 3.3V")
add("C6", "10uF/16V", "Capacitor_SMD:C_0805_2012Metric",
    {"1": ("+5V", "1"), "2": ("GND", "2")})
add("C7", "22uF/16V", "Capacitor_SMD:C_1210_3225Metric",
    {"1": ("+3V3", "1"), "2": ("GND", "2")}, "LDO stability")
add("C8", "100nF/50V", "Capacitor_SMD:C_0805_2012Metric",
    {"1": ("+3V3", "1"), "2": ("GND", "2")})
add("C9", "100uF/10V", "Capacitor_SMD:CP_Elec_6.3x5.4",
    {"1": ("+3V3", "+"), "2": ("GND", "-")})
add("C19", "470uF/25V", "Capacitor_SMD:CP_Elec_10x10.5",
    {"1": ("+12V", "+"), "2": ("GND", "-")}, "motor bulk, recommended")

# ------------------------------------------------------------------------ MCU
add("U3", "ESP-12F", "RF_Module:ESP-12E",
    {"1": ("RST", "RST"), "2": ("ADC", "ADC/TOUT"), "3": ("EN", "EN/CH_PD"),
     "4": ("GPIO16", "GPIO16"), "5": ("ECHO", "GPIO14"), "6": ("TRIG", "GPIO12"),
     "7": ("GPIO13", "GPIO13"), "8": ("+3V3", "VCC"),
     "9": ("GND", "GND bottom1"), "10": ("GND", "GND bottom2"),
     "11": ("GND", "GND bottom3"), "12": ("GND", "GND bottom4"),
     "13": ("GND", "GND bottom5"), "14": ("GND", "GND bottom6"),
     "15": ("GND", "GND right"), "16": ("GPIO15", "GPIO15"),
     "17": ("GPIO2", "GPIO2"), "18": ("GPIO0", "GPIO0"),
     "19": ("SCL", "GPIO5"), "20": ("SDA", "GPIO4"),
     "21": ("RXD0", "RXD0/GPIO3"), "22": ("TXD0", "TXD0/GPIO1")},
    "antenna overhangs board edge")

add("R1", "10k", "Resistor_SMD:R_0805_2012Metric",
    {"1": ("EN", "1"), "2": ("+3V3", "2")}, "EN pull-up")
add("C12", "100nF", "Capacitor_SMD:C_0805_2012Metric",
    {"1": ("EN", "1"), "2": ("GND", "2")}, "EN RC delay 1 ms")

add("R2", "10k", "Resistor_SMD:R_0805_2012Metric",
    {"1": ("RST", "1"), "2": ("+3V3", "2")}, "RST pull-up")
add("SW2", "RESET", "Button_Switch_SMD:SW_SPST_TL3342",
    {"1": ("RST", "1"), "2": ("GND", "2")})
add("C18", "100nF", "Capacitor_SMD:C_0805_2012Metric",
    {"1": ("RST", "1"), "2": ("GND", "2")}, "max 100nF")

add("R3", "10k", "Resistor_SMD:R_0805_2012Metric",
    {"1": ("GPIO0", "1"), "2": ("+3V3", "2")}, "boot strap")
add("SW1", "FLASH", "Button_Switch_SMD:SW_SPST_TL3342",
    {"1": ("GPIO0", "1"), "2": ("GND", "2")}, "no capacitor across")

add("R4", "10k", "Resistor_SMD:R_0805_2012Metric",
    {"1": ("GPIO15", "1"), "2": ("GND", "2")}, "boot strap LOW")
add("R5", "10k", "Resistor_SMD:R_0805_2012Metric",
    {"1": ("GPIO2", "1"), "2": ("+3V3", "2")}, "boot strap HIGH")
add("R6", "10k", "Resistor_SMD:R_0805_2012Metric",
    {"1": ("TRIG", "1"), "2": ("GND", "2")}, "GPIO12/MTDI strap guard")

add("C10", "100nF", "Capacitor_SMD:C_0805_2012Metric",
    {"1": ("+3V3", "1"), "2": ("GND", "2")})
add("C11", "10uF", "Capacitor_SMD:C_0805_2012Metric",
    {"1": ("+3V3", "1"), "2": ("GND", "2")})

add("J2", "UART 4P 5.00mm", "TerminalBlock:TerminalBlock_bornier-4_P5.00mm",
    {"1": ("+3V3", "1"), "2": ("TXD0", "2"), "3": ("RXD0", "3"), "4": ("GND", "4")},
    "3V3 is OUTPUT only - do not back-power")

add("H2", "PROG 1x6", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
    {"1": ("GND", "1"), "2": ("+3V3", "2"), "3": ("TXD0", "3"),
     "4": ("RXD0", "4"), "5": ("GPIO0", "5"), "6": ("RST", "6")},
    "recommended for USB-TTL")

add("H1", "SPARE 2x5", "Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical",
    {"1": ("+3V3", "1"), "2": ("GND", "2"),
     "3": ("EXP_B0", "GPB0"), "4": ("EXP_B1", "GPB1"),
     "5": ("EXP_B2", "GPB2"), "6": ("EXP_B3", "GPB3"),
     "7": ("EXP_B4", "GPB4"), "8": ("EXP_B5", "GPB5"),
     "9": ("EXP_B6", "GPB6"), "10": ("EXP_B7", "GPB7")})

add("TP1", "+5V", "Connector:TestPoint", {"1": ("+5V", "1")})
add("TP2", "+3V3", "Connector:TestPoint", {"1": ("+3V3", "1")})
add("TP3", "GND", "Connector:TestPoint", {"1": ("GND", "1")})
add("TP4", "ADC", "Connector:TestPoint", {"1": ("ADC", "1")}, "0-1.0 V only")
add("TP5", "GPIO16", "Connector:TestPoint", {"1": ("GPIO16", "1")})
add("TP6", "GPIO13", "Connector:TestPoint", {"1": ("GPIO13", "1")})

# ------------------------------------------------------------- I2C expanders
add("U4", "MCP23017-E/SO", "Package_SO:SOIC-28W_7.5x17.9mm_P1.27mm",
    {"1": ("EXP_B0", "GPB0"), "2": ("EXP_B1", "GPB1"), "3": ("EXP_B2", "GPB2"),
     "4": ("EXP_B3", "GPB3"), "5": ("EXP_B4", "GPB4"), "6": ("EXP_B5", "GPB5"),
     "7": ("EXP_B6", "GPB6"), "8": ("EXP_B7", "GPB7"),
     "9": ("+3V3", "VDD"), "10": ("GND", "VSS"),
     "11": (None, "NC"), "12": ("SCL", "SCL"), "13": ("SDA", "SDA"),
     "14": (None, "NC"), "15": ("GND", "A0"), "16": ("GND", "A1"),
     "17": ("GND", "A2"), "18": ("EXP1_RST", "RESET"),
     "19": (None, "INTB"), "20": (None, "INTA"),
     "21": ("M1_DRV", "GPA0"), "22": ("M2_DRV", "GPA1"),
     "23": ("M3_DRV", "GPA2"), "24": ("M4_DRV", "GPA3"),
     "25": ("M5_DRV", "GPA4"), "26": ("M6_DRV", "GPA5"),
     "27": ("M7_DRV", "GPA6"), "28": ("M8_DRV", "GPA7")},
    "address 0x20 (A2..A0 = 000)")

add("U5", "MCP23017-E/SO", "Package_SO:SOIC-28W_7.5x17.9mm_P1.27mm",
    {"1": ("OPT9_COL", "GPB0"), "2": ("OPT10_COL", "GPB1"),
     "3": ("OPT11_COL", "GPB2"), "4": ("OPT12_COL", "GPB3"),
     "5": ("OPT13_COL", "GPB4"), "6": ("OPT14_COL", "GPB5"),
     "7": ("OPT15_COL", "GPB6"), "8": ("OPT16_COL", "GPB7"),
     "9": ("+3V3", "VDD"), "10": ("GND", "VSS"),
     "11": (None, "NC"), "12": ("SCL", "SCL"), "13": ("SDA", "SDA"),
     "14": (None, "NC"), "15": ("+3V3", "A0"), "16": ("GND", "A1"),
     "17": ("GND", "A2"), "18": ("EXP2_RST", "RESET"),
     "19": (None, "INTB"), "20": (None, "INTA"),
     "21": ("OPT1_COL", "GPA0"), "22": ("OPT2_COL", "GPA1"),
     "23": ("OPT3_COL", "GPA2"), "24": ("OPT4_COL", "GPA3"),
     "25": ("OPT5_COL", "GPA4"), "26": ("OPT6_COL", "GPA5"),
     "27": ("OPT7_COL", "GPA6"), "28": ("OPT8_COL", "GPA7")},
    "address 0x21 (A2..A0 = 001)")

add("R7", "4.7k", "Resistor_SMD:R_0805_2012Metric",
    {"1": ("SDA", "1"), "2": ("+3V3", "2")}, "I2C pull-up")
add("R8", "4.7k", "Resistor_SMD:R_0805_2012Metric",
    {"1": ("SCL", "1"), "2": ("+3V3", "2")}, "I2C pull-up")
add("R9", "10k", "Resistor_SMD:R_0805_2012Metric",
    {"1": ("EXP1_RST", "1"), "2": ("+3V3", "2")})
add("R10", "10k", "Resistor_SMD:R_0805_2012Metric",
    {"1": ("EXP2_RST", "1"), "2": ("+3V3", "2")})
add("C13", "100nF", "Capacitor_SMD:C_0805_2012Metric",
    {"1": ("+3V3", "1"), "2": ("GND", "2")}, "at U4")
add("C14", "100nF", "Capacitor_SMD:C_0805_2012Metric",
    {"1": ("+3V3", "1"), "2": ("GND", "2")}, "at U5")

# -------------------------------------------------------------- motor drivers
add("U6", "ULN2803ADWR", "Package_SO:SOIC-18W_7.5x11.6mm_P1.27mm",
    {"1": ("M1_DRV", "IN1"), "2": ("M1_DRV", "IN2"),
     "3": ("M2_DRV", "IN3"), "4": ("M2_DRV", "IN4"),
     "5": ("M3_DRV", "IN5"), "6": ("M3_DRV", "IN6"),
     "7": ("M4_DRV", "IN7"), "8": ("M4_DRV", "IN8"),
     "9": ("GND", "GND"), "10": ("+12V", "COM"),
     "11": ("MOT4_N", "O8"), "12": ("MOT4_N", "O7"),
     "13": ("MOT3_N", "O6"), "14": ("MOT3_N", "O5"),
     "15": ("MOT2_N", "O4"), "16": ("MOT2_N", "O3"),
     "17": ("MOT1_N", "O2"), "18": ("MOT1_N", "O1")},
    "motors 1-4, 2 channels paralleled per motor")

add("U7", "ULN2803ADWR", "Package_SO:SOIC-18W_7.5x11.6mm_P1.27mm",
    {"1": ("M5_DRV", "IN1"), "2": ("M5_DRV", "IN2"),
     "3": ("M6_DRV", "IN3"), "4": ("M6_DRV", "IN4"),
     "5": ("M7_DRV", "IN5"), "6": ("M7_DRV", "IN6"),
     "7": ("M8_DRV", "IN7"), "8": ("M8_DRV", "IN8"),
     "9": ("GND", "GND"), "10": ("+12V", "COM"),
     "11": ("MOT8_N", "O8"), "12": ("MOT8_N", "O7"),
     "13": ("MOT7_N", "O6"), "14": ("MOT7_N", "O5"),
     "15": ("MOT6_N", "O4"), "16": ("MOT6_N", "O3"),
     "17": ("MOT5_N", "O2"), "18": ("MOT5_N", "O1")},
    "motors 5-8")

add("RN5", "10k x4", "Resistor_SMD:R_Array_Concave_4x0612",
    {"1": ("M1_DRV", "1"), "2": ("M2_DRV", "2"), "3": ("M3_DRV", "3"),
     "4": ("M4_DRV", "4"), "5": ("GND", "5"), "6": ("GND", "6"),
     "7": ("GND", "7"), "8": ("GND", "8")}, "power-up pull-down")
add("RN6", "10k x4", "Resistor_SMD:R_Array_Concave_4x0612",
    {"1": ("M5_DRV", "1"), "2": ("M6_DRV", "2"), "3": ("M7_DRV", "3"),
     "4": ("M8_DRV", "4"), "5": ("GND", "5"), "6": ("GND", "6"),
     "7": ("GND", "7"), "8": ("GND", "8")}, "power-up pull-down")

add("C15", "100nF", "Capacitor_SMD:C_0805_2012Metric",
    {"1": ("+12V", "1"), "2": ("GND", "2")}, "at U6 COM")
add("C16", "100nF", "Capacitor_SMD:C_0805_2012Metric",
    {"1": ("+12V", "1"), "2": ("GND", "2")}, "at U7 COM")

# motor terminals J3..J10 -> motors 1..8
for n in range(1, 9):
    add("J%d" % (n + 2), "MOTOR %d 5.00mm" % n,
        "TerminalBlock:TerminalBlock_bornier-2_P5.00mm",
        {"1": ("+12V", "M+"), "2": ("MOT%d_N" % n, "M-")})

# --------------------------------------------------- opto-isolated field input
add("R29", "0R", "Resistor_SMD:R_0805_2012Metric",
    {"1": ("+12V", "1"), "2": ("FLD_12V", "2")},
    "isolation link: remove for true galvanic isolation")


def opto(ref, ch0, note):
    pins = {}
    for i in range(4):
        ch = ch0 + i
        a = 1 + 2 * i
        k = a + 1
        c = 16 - 2 * i
        e = c - 1
        pins[str(a)] = ("FLD_12V", "A%d" % (i + 1))
        pins[str(k)] = ("OPT%d_K" % ch, "K%d" % (i + 1))
        pins[str(c)] = ("OPT%d_COL" % ch, "C%d" % (i + 1))
        pins[str(e)] = ("GND", "E%d" % (i + 1))
        note2 = note
    add(ref, "PS2501-4", "Package_DIP:DIP-16_W7.62mm", pins, note2)


opto("U8", 1, "channels 1-4")
opto("U9", 5, "channels 5-8")
opto("U10", 9, "channels 9-12")
opto("U11", 13, "channels 13-16")

# per-channel field parts: R11..R26, D4..D19, J11..J26
for ch in range(1, 17):
    add("R%d" % (10 + ch), "1.2k 0.25W", "Resistor_SMD:R_1206_3216Metric",
        {"1": ("OPT%d_K" % ch, "1"), "2": ("FL%d_N" % ch, "2")},
        "If = 9 mA at 12 V, 145 mW at 14.4 V")
    add("D%d" % (3 + ch), "1N4148W", "Diode_SMD:D_SOD-123",
        {"1": ("FLD_12V", "K"), "2": ("OPT%d_K" % ch, "A")},
        "antiparallel LED reverse clamp")
    add("J%d" % (10 + ch), "FIELD %d 5.00mm" % ch,
        "TerminalBlock:TerminalBlock_bornier-2_P5.00mm",
        {"1": ("FLD_12V", "+12V"), "2": ("FL%d_N" % ch, "SIG")})

# opto collector pull-up arrays RN1..RN4
for blk in range(4):
    pins = {}
    for i in range(4):
        ch = blk * 4 + i + 1
        pins[str(i + 1)] = ("+3V3", "%d" % (i + 1))
        pins[str(8 - i)] = ("OPT%d_COL" % ch, "%d" % (8 - i))
    add("RN%d" % (blk + 1), "10k x4", "Resistor_SMD:R_Array_Concave_4x0612",
        pins, "channels %d-%d" % (blk * 4 + 1, blk * 4 + 4))

# ------------------------------------------------------------- ultrasonic port
add("J27", "HC-SR04 4P 2.5mm", "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical",
    {"1": ("+5V", "VCC"), "2": ("TRIG", "TRIG"),
     "3": ("ECHO_RAW", "ECHO"), "4": ("GND", "GND")})
add("R27", "1k", "Resistor_SMD:R_0805_2012Metric",
    {"1": ("ECHO_RAW", "1"), "2": ("ECHO", "2")}, "divider top")
add("R28", "2k", "Resistor_SMD:R_0805_2012Metric",
    {"1": ("ECHO", "1"), "2": ("GND", "2")}, "divider bottom, 5V -> 3.33V")
add("C17", "100nF", "Capacitor_SMD:C_0805_2012Metric",
    {"1": ("+5V", "1"), "2": ("GND", "2")})

# ------------------------------------------------------------------- validate
nets = collections.defaultdict(list)
nc_pins = []
unassigned = []
for ref, p in PARTS.items():
    for pin, (net, name) in p["pins"].items():
        if net is None:
            nc_pins.append((ref, pin, name))
        else:
            nets[net].append((ref, pin, name))

# every part must have at least one pin and no None pin keys
for ref, p in PARTS.items():
    if not p["pins"]:
        unassigned.append(ref)

single = {n: v for n, v in nets.items() if len(v) == 1}

# ----------------------------------------------------------------- emit files
with open(os.path.join(OUT_DIR, "NETLIST.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Net", "Component", "Pin", "PinFunction", "Value", "Footprint"])
    for net in sorted(nets, key=lambda s: (not s.startswith(("+", "GND", "FLD")), s)):
        for ref, pin, name in sorted(nets[net], key=lambda t: (t[0][0], t[0], int(t[1]))):
            w.writerow([net, ref, pin, name, PARTS[ref]["value"], PARTS[ref]["fp"]])

with open(os.path.join(OUT_DIR, "NET_SUMMARY.md"), "w", encoding="utf-8") as f:
    f.write("# Net summary\n\n")
    f.write("Generated by `gen_netlist.py` - %d nets, %d component pins, %d parts.\n\n"
            % (len(nets), sum(len(v) for v in nets.values()), len(PARTS)))
    f.write("| Net | Pins | Connections (ref.pin) |\n|---|---|---|\n")
    for net in sorted(nets, key=lambda s: (not s.startswith(("+", "GND", "FLD")), s)):
        conns = ", ".join("%s.%s" % (r, p) for r, p, _ in
                          sorted(nets[net], key=lambda t: (t[0][0], t[0], int(t[1]))))
        f.write("| `%s` | %d | %s |\n" % (net, len(nets[net]), conns))

with open(os.path.join(OUT_DIR, "CONNECTIVITY.md"), "w", encoding="utf-8") as f:
    f.write("# Connectivity check\n\n")
    f.write("- Parts: %d\n- Nets: %d\n- Component pins on nets: %d\n"
            "- Explicit no-connect pins: %d\n- Single-pin nets: %d\n\n"
            % (len(PARTS), len(nets), sum(len(v) for v in nets.values()),
               len(nc_pins), len(single)))
    f.write("## Single-pin nets (must be intentional test points)\n\n")
    for n, v in single.items():
        f.write("- `%s` -> %s\n" % (n, ", ".join("%s.%s" % (r, p) for r, p, _ in v)))
    f.write("\n## No-connect pins\n\n")
    for r, p, name in nc_pins:
        f.write("- %s.%s (%s)\n" % (r, p, name))
    f.write("\n## Parts with no pins\n\n")
    f.write("None\n" if not unassigned else "\n".join("- " + r for r in unassigned) + "\n")

print("parts: %d  nets: %d  pins: %d  NC: %d  single-pin nets: %d"
      % (len(PARTS), len(nets), sum(len(v) for v in nets.values()), len(nc_pins), len(single)))
for n, v in sorted(single.items()):
    print("  single-pin net:", n, v)
