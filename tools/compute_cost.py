"""Compute verified per-board costs from Robu.in SKUs and fab quotes."""
import os, json
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# verified Robu.in SKUs / unit prices incl GST (checked 2026-11-24; 2026-11-23 for LTB-827S)
items=[
 ("0R 1206 resistor","R137882",0.17,5),
 ("10k 1206 resistor","R179282",0.15,1),
 ("330R 1206 resistor (now 220R in 2L)","R189319",0.31,8),
 ("2.2k 1206 resistor","R179336",0.12,4),
 ("4.7k 1206 resistor","R138163",0.15,6),
 ("10uF 1206 25V X7R","R111769",3.33,4),
 ("220uF 25V SMD electrolytic","R183176",2.01,2),
 ("33uH SRR1260-330M","R158560",74.00,1),
 ("ESP32-WROOM-32E-N4","R186288",349.00,1),
 ("XL1509-5.0","R241995",42.00,1),
 ("AMS1117-3.3 fixed","R193008",4.81,1),
 ("ULN2803A","R194519",40.00,1),
 ("LTV-827S","1087779",36.00,6),
 ("SMBJ15A-13-F","R190689",22.00,1),
 ("SS34","649691",1.72,2),
]
comp=sum(p*q for _,_,p,q in items)
jumpers=16*0.17   # 1-layer only: 16 x 0R links

lines=[]
lines.append("# Per-Board Manufacturing Cost — ind_8ch_motor_ctrl")
lines.append("")
lines.append("**Date:** 2026-11-24 · **Currency:** INR incl. GST · **Qty basis:** 5 boards")
lines.append("")
lines.append("## 1. Components (Robu.in, verified live, per board)")
lines.append("")
lines.append("| Item | Robu SKU | Qty/board | Unit ₹ | Ext ₹ |")
lines.append("|---|---|---:|---:|---:|")
for n,sku,p,q in items:
    lines.append(f"| {n} | {sku} | {q} | {p:.2f} | {p*q:.2f} |")
lines.append(f"| **Components per board** | | | | **{comp:.2f}** |")
lines.append(f"| Components for 5 boards | | | | {comp*5:.2f} |")
lines.append("")
lines.append("Not on Robu.in: 2 × 20-pos 5.08 mm terminal blocks (J_IN, J_OUT) — source separately.")
lines.append("LTV-827S stock: only 18 pcs (30 needed for 5 boards) — order early.")
lines.append("")
lines.append("## 2. PCB fabrication per board")
lines.append("")
lines.append("| Board | Fab | ₹/board (5 pcs) | Source |")
lines.append("|---|---|---:|---|")
lines.append("| 2-layer | cuCircuits | 338.55 | live Gerber quote |")
lines.append("| 2-layer | Lion Circuits | 375.40 | live instant quote (₹1,877/5) |")
lines.append("| 1-layer | cuCircuits | not obtained | capabilities API supports layers=1; quote websocket blocked in this environment |")
lines.append("| 1-layer | Lion Circuits | not offered | instant quote lists 2/4/6/8 only; manual quote needed |")
lines.append("")
lines.append("## 3. Total per board (excluding terminal blocks, shipping, assembly)")
lines.append("")
lines.append("| Configuration | Components | PCB (cuCircuits) | Jumpers | Total ₹/board |")
lines.append("|---|---:|---:|---:|---:|")
lines.append(f"| 2-layer production | {comp:.2f} | 338.55 | — | **{comp+338.55:.2f}** |")
lines.append(f"| 2-layer (Lion PCB) | {comp:.2f} | 375.40 | — | **{comp+375.40:.2f}** |")
lines.append(f"| 1-layer prototype | {comp:.2f} | TBD | {jumpers:.2f} | **{comp+jumpers:.2f} + PCB** |")
lines.append("")
lines.append("## 4. Notes")
lines.append("- Component prices include GST; Robu.in prices/stock change — verify before ordering.")
lines.append("- 1-layer PCB needs a manual quote from either fab; both can make single-sided boards.")
lines.append("- Add terminal blocks (~₹150–250 each), shipping and assembly to get landed cost.")

out=os.path.join(ROOT,'COST_PER_BOARD.md')
open(out,'w').write("\n".join(lines)+"\n")
print("wrote",out,"components/board",comp)
