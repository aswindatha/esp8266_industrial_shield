"""Compile verified Robu.in quotes + cuCircuits MCP findings into a cost report."""
import os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (line, robu sku, title, unit_inr, qty_per_board, stock, conf, url)
ITEMS=[
 ('0R 1206 resistor (R_J1-5)','R137882','Uniohm 0R 1206 250mW',0.17,5,'in stock','MED','https://robu.in/product/1206w4f0000t5e-uniohm-royal-ohm-250mw-thick-film-resistors-200v--c2-b1800ppm--e2-84-83-c2-b11-0-cf-89-1206-chip-resistor-surface-mount-rohs/'),
 ('10k 1206 resistor (R19)','R179282','Walsin 10k 1206 250mW',0.15,1,'in stock','MED','https://robu.in/product/wr12x103-jtl-walsin-250mw-thick-film-resistors-200v--c2-b1100ppm--e2-84-83--c2-b15-10k-cf-89-1206-chip-resistor-surface-mount-rohs/'),
 ('330R 1206 resistor (R1-8)','R189319','Yageo 330R 1206 1%',0.29,8,'in stock','MED','https://robu.in/product/rc1206fr-07330rl-yageo-smd-chip-resistor-330-ohm--c2-b1-1-250-mw-1206-3216-metric-thick-film-general-purpose/'),
 ('2.2k 1206 resistor (R9-12)','R179336','Walsin 2.2k 1206 250mW',0.11,4,'in stock','MED','https://robu.in/product/wr12x222-jtl-walsin-250mw-thick-film-resistors-200v--c2-b1100ppm--e2-84-83--c2-b15-2-2k-cf-89-1206-chip-resistor-surface-mount-rohs/'),
 ('4.7k 1206 resistor (R13-18)','R138163','Uniohm 4.7k 1206 250mW',0.15,6,'in stock','MED','https://robu.in/product/1206w4j0472t5e-uniohm-royal-ohm-250mw-thick-film-resistors-200v--c2-b1100ppm--e2-84-83--c2-b15-4-7k-cf-89-1206-chip-resistor-surface-mount-rohs/'),
 ('10uF 1206 25V X7R (C1-4)','R111769','Samsung 10uF 25V X7R 1206',3.05,4,'1758 pcs','HIGH','https://robu.in/product/cl31b106kahzw6e-samsung-electro-mechanics-multilayer-ceramic-capacitors-mlcc-smd-smt-10uf-10-25v-x7r-3-1206/'),
 ('220uF 25V electrolytic','R183176','Follon 220uF 25V SMD D8x10.5',2.00,2,'in stock','HIGH','https://robu.in/product/efvz025ada221m08b0-follon-220uf-25v--c2-b120-smdd8xl10-5mm-aluminum-electrolytic-capacitors-smd-rohs/'),
 ('33uH shielded inductor','R158560','Bourns SRR1260-330M 33uH 2.8A',74.00,1,'in stock','HIGH','https://robu.in/product/srr1260-330m-bourns-srr1260-330m-inductor-shielded-33uh-2-8a-smd/'),
 ('ESP32-WROOM-32E-N4','R186288','Espressif ESP32-WROOM-32E-N4',349.00,1,'665 pcs','MED','https://robu.in/product/espressif-esp32-wroom-32e-n4-modules/'),
 ('XL1509-5.0 buck','R241995','UMW XL1509-5.0 5V 2A SOIC-8',42.00,1,'in stock','MED','https://robu.in/product/xl1509-5-0-umw-step-down-type-fixed-5v-2a-4-5v40v-soic-8-dc-dc-converters-rohs/'),
 ('AMS1117-3.3 fixed','R193008','Slkor AMS1117-3.3 SOT-223',4.81,1,'1821 pcs','HIGH','https://robu.in/product/ams1117-3-3-slkor-800ma-70db120hz-fixed-3-3v-positive-electrode-18v-sot-223-voltage-regulators-linear-low-drop-out-ldo-regulators-rohs/'),
 ('ULN2803A','R194519','XBLW ULN2803A SOP-18',40.00,1,'in stock','MED','https://robu.in/product/uln2803adtr-xblw-eight-channels-50v-500ma-sop-18-darlington-transistor-arrays-rohs/'),
 ('LTV-827S optocoupler','1087779','Lite-On LTV-827S-TA1 SOP-8',36.00,6,'18 pcs (SHORT)','MED','https://robu.in/product/ltv-827s-ta1-photocoupler-5kv-2ch-transistor-8-smd/'),
 ('SMBJ15A TVS','R190689','Diodes Inc SMBJ15A-13-F',22.00,1,'in stock','HIGH','https://robu.in/product/smbj15a-13-f-diodes-inc-smbj15a-13-f-tvs-diode-smbj-unidirectional-15-v-24-4-v-do-214aa-smb-2-pins/'),
 ('SS34 Schottky (FOOTPRINT WARNING)','649691','SS34 DO214AC (SMA) - board is SMB',1.72,2,'9776 pcs','MED','https://robu.in/product/ss34-diode-do214ac/'),
]

NB=5  # prototype qty = PCB MOQ
lines=[]
total=0
for name,sku,title,unit,qpb,stock,conf,url in ITEMS:
    qty=qpb*NB; ext=round(unit*qty,2); total+=ext
    lines.append((name,sku,title,unit,qpb,qty,ext,stock,conf,url))

md=[]
md.append("# Manufacturing Cost Estimate — ind_8ch_motor_ctrl")
md.append("")
md.append("**Date:** 2026-11-23  |  **Prototype qty:** 5 PCBs (PCB MOQ)  |  **Currency:** INR incl. GST")
md.append("")
md.append("## 1. PCB fabrication — cuCircuits (https://cucircuits.com/mcp)")
md.append("")
md.append("MCP endpoint is live and responded to `initialize` / `tools/list` / `get_options`.")
md.append("**A quotation could not be generated: `start_upload` and `quote` return code -32001")
md.append("\"Sign in to CU Circuits to use this tool\".** Sign-in to the connected account is required.")
md.append("")
md.append("Options retrieved for a 2-layer board (board size/layers are read from the Gerbers):")
md.append("")
md.append("| Category | Choices |")
md.append("|---|---|")
md.append("| Layers | 2 (from file) |")
md.append("| Base Material | FR4 TG135 / FR4 TG140 / Flex |")
md.append("| Thickness | 0.8 / 1.0 / 1.2 / 1.6 / 2.0 mm |")
md.append("| Surface Finish | HASL / HASL-RoHs / ENIG-RoHS / OSP |")
md.append("| Copper Weight | 1 / 2 / 3 oz |")
md.append("| Color | Green, Purple, Red, Yellow, Blue, White, Black |")
md.append("| Silkscreen | White / Black |")
md.append("| Via | tented / through |")
md.append("| Testing | Yes / No |")
md.append("")
md.append("Recommended selection: FR4 TG135, 1.6 mm, 1 oz, HASL-RoHs (or ENIG-RoHS), Green, White silk, tented vias, Testing Yes.")
md.append("Quantity rule: min 5, step 5, max 500. Standard lead time 8 working days from payment to dispatch.")
md.append("Capability check: min trace/space 0.15/0.15 mm, min hole 0.15 mm, 1-14 layers — our 0.2624 mm track and 0.20 mm drill are within capability.")
md.append("")
md.append("**PCB price: NOT OBTAINED — sign-in required.** To complete: sign in at cucircuits.com,")
md.append("reconnect the MCP, then call `start_upload` → `get_upload` → `get_options` → `quote`")
md.append("with the Gerber ZIP `ind_8ch_motor_ctrl_FAB_PACKAGE.zip`.")
md.append("")
md.append("## 2. Components — Robu.in (verified live 2026-11-23, prices incl. GST)")
md.append("")
md.append("| Line | Robu SKU | Qty (5 pcs) | Unit ₹ | Ext ₹ | Stock | Conf |")
md.append("|---|---|---:|---:|---:|---|---|")
for l in lines:
    md.append(f"| {l[0]} | {l[1]} | {l[5]} | {l[3]:.2f} | {l[6]:.2f} | {l[7]} | {l[8]} |")
md.append(f"| **Component subtotal (5 boards)** | | | | **{total:.2f}** | | |")
md.append(f"| **Per board** | | | | **{total/NB:.2f}** | | |")
md.append("")
md.append("### Sourcing gaps / warnings")
md.append("- **2 × 20-position 5.08 mm terminal blocks (J_IN, J_OUT):** no robu.in match. Searches for")
md.append("  `TB007-508-20`, `20 pin 5.08mm screw terminal block`, `KF301V-20P`, `DG128-20` returned only")
md.append("  2-pin/7.5 mm or unrelated parts. Per skill rules, no link is invented — source these separately.")
md.append("- **LTV-827S:** only 18 in stock vs 30 needed for 5 boards — short 12 (buy 3 boards' worth now).")
md.append("- **SS34:** robu.in stocks DO214AC (SMA); board footprint is `D_SMB_Handsoldering` (SMB/DO214AA).")
md.append("  Verify pad compatibility or use an equivalent in SMB before ordering.")
md.append("")
md.append("## 3. Overall prototype cost (5 boards)")
md.append("")
md.append("| Item | Amount ₹ |")
md.append("|---|---:|")
md.append(f"| Components (verified Robu.in, 5 boards) | {total:.2f} |")
md.append("| Terminal blocks ×10 (not on Robu — TBD) | TBD |")
md.append("| PCB fabrication ×5 (cuCircuits — sign-in required) | TBD |")
md.append("| PCB shipping (Chennai → your location) | TBD |")
md.append("| **Known component total** | **%.2f** |"%total)
md.append("")
md.append("Once the cuCircuits quote is obtained, add PCB + shipping to the ₹%.2f component total."%total)
md.append("")
md.append("## 4. Sources / reproducibility")
md.append("- Robu skill: `python3 ~/.config/opencode/skills/robu-part-search/scripts/search_robu.py \"<part>\" --table`")
md.append("- cuCircuits MCP: `POST https://cucircuits.com/mcp` (JSON-RPC 2.0)")
md.append("- Gerber ZIP prepared: `/tmp/ind_8ch_motor_ctrl_GERBERS.zip` (114 KB)")

out=os.path.join(ROOT,'COST_REPORT.md')
open(out,'w').write("\n".join(md)+"\n")
print("wrote",out,"component total",total,"per board",total/NB)
