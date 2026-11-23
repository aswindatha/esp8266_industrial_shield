# India Manufacturing Readiness — Deep Audit

**Date:** 2026-11-23
**Board:** `ind_8ch_motor_ctrl.kicad_pcb` (100×100 mm, 2-layer, ESP32-WROOM-32E)
**Automated evidence:** `python3 tools/production_audit.py` → 23/23 PASS
`python3 tools/india_manufacturing_audit.py` → findings below

---

## 1. Verdict

| Scope | Verdict | Rationale |
|---|---|---|
| **Bare PCB fabrication in India** | **READY** | 0 DRC / 0 ERC, complete Gerber+drill package, DFM within typical Indian fab capability (with one caveat below). |
| **PCBA assembly in India** | **CONDITIONAL** | Component procurement data (MPN/manufacturer/ratings/RoHS CoC) is absent from the design files. A recommended procurement BOM is now supplied (`fab/BOM_procurement.csv`) but must be frozen with real distributor part numbers before ordering. |
| **Regulatory sale/use in India** | **NOT YET CLEAR** | WPC ETA for the 2.4 GHz ESP32 module is required; no ETA for ESP32-WROOM-32E was found in Espressif's published list. BIS CRS does **not** appear applicable to this bare 12 V DC board. |
| **Electrical/thermal robustness** | **ACCEPTABLE with advisories** | 5 derating items identified; none are DRC errors; 2 are worth fixing in the next revision. |

**Overall: NOT FULLY PRODUCTION-READY for India until the WPC ETA and procurement/RoHS documentation are closed.** The PCB itself is electrically perfect and fabrication-ready.

---

## 2. Regulatory analysis (India)

### 2.1 BIS / CRS — not applicable to the bare board
The MeitY Compulsory Registration Scheme (2021 Order, as amended) covers **notified product categories only** — e.g. SMPS/adaptors, IT equipment, TVs, mobile phones, UPS, LED drivers. A 12 V DC industrial motor-control PCB is not in the notified list.
- If you sell the board **with an external mains SMPS/adaptor**, that adaptor must be BIS-CRS registered (IS/IEC 62368-1:2023).
- If you integrate this board into a product that itself falls in a notified category, BIS applies at the product level.
- **Action:** confirm the final product classification with a BIS consultant before sale.

### 2.2 WPC ETA — REQUIRED (open item)
- ESP32-WROOM-32E operates at 2402–2480 MHz (BT/BLE) and 2412–2484 MHz (Wi-Fi) under **G.S.R. 45(E) 28-01-2005** (licence-exempt, 2.4 GHz ISM, ≤100 mW EIRP).
- WPC DoT requires an **Equipment Type Approval (ETA)**. Self-declaration via **SARAL Sanchar** portal, fee ~₹10,000, supported by an accredited-lab RF test report.
- WPC FAQ #8: if a product made **in India** uses an RF module that already has ETA, **no separate ETA** is needed for the finished product. But Espressif's published certificate list shows WPC ETA for ESP32-WROOM-32D and ESP8684-WROOM-02C — **not for ESP32-WROOM-32E**.
- **Action (mandatory before sale/import):** obtain an ETA for the exact module (or finished product) via self-declaration, or source a module variant with an existing ETA. File an import undertaking with customs for incoming modules.

### 2.3 RoHS / E-Waste
- India has **no EU-style mandatory RoHS**, but the **E-Waste Management Rules 2016** (amended 2018/2022) progressively restrict hazardous substances, and most institutional/export customers require RoHS.
- Espressif documents the ESP32-WROOM-32E as RoHS/REACH compliant.
- **Action:** collect RoHS Certificates of Conformance for all 17 line items; prioritize XL1509, AMS1117, ULN2803, LTV-827S, SS34, terminal blocks and electrolytics (marked `CONFIRM Pb-free` in `fab/BOM_procurement.csv`).

### 2.4 Other
- **MTCTE/TEC:** not applicable (no public telecom network interface).
- **IWT Act 1933:** radio use must remain within the 2.4 GHz gazette conditions (non-interference, non-protection, shared) — the module's PCB antenna and output power meet this.

---

## 3. Component / BOM findings

The design files contain **no MPN, manufacturer, voltage, power, tolerance, lifecycle, HTS or RoHS fields**. `fab/BOM_procurement.csv` now supplies recommended parts and specs (verify with distributor before ordering).

| Finding | Severity | Action |
|---|---|---|
| Opto CTR: IF=6.36 mA, required CTR ≈61.3 %, LTV-827S min ≈50 % @5 mA | **Major** | Change R1–R8 330 Ω → 220 Ω (IF≈9.55 mA, required CTR ≈41 %) or use ≥100 % CTR rank |
| 10 µF 1206 MLCC at 5 V bias | Major | Specify X7R, ≥10 V (16 V preferred); avoid 6.3 V X5R |
| XL1509 inductor Isat | Major | Confirm SRR1260-330 Isat ≥2.5 A |
| TVS SMBJ15A vs 14.4 V rail | Minor | Acceptable; SMBJ18A adds margin (note 25 V input caps) |
| AMS1117 @ 500 mA | Minor | 0.85 W in SOT-223; Tj ≈ Ta+77 °C — check enclosure/ambient |
| Sensor 2.2 k @ 24 V | Minor | 236 mW in 1206 (250 mW) — use 0.5 W part or 1 W rated |
| 0.20 mm drills ×12 (ESP32 thermal pad) | Manufacturing | Confirm fab supports ≤0.20 mm laser/mechanical drill; else 0.25 mm |
| 4 references on F.Fab only | Assembly | C3, C_BULK1/2, D_TVS1 lack silkscreen |

---

## 4. PCB / DFM status (verified)

- 100 × 100 mm, 2 Cu layers, 716 segments, 83 vias, 50 footprints all on F.Cu.
- Min track 0.2624 mm, clearance 0.2516 mm, copper-to-edge 0.30 mm — within standard Indian fab capability.
- Drills 0.20 / 0.30 / 1.60 / 3.20 mm; PTH/NPTH separated; Gerber X2 with net attributes.
- 9 Gerbers, drill maps, BOM, POS, IPC-D-356, assembly PDF/SVG — all present and consistent.
- **0 DRC violations, 0 unconnected, 0 ERC violations, 0 DRC exclusions** — nothing hidden.

---

## 5. Action checklist before Indian production

- [ ] Obtain **WPC ETA** for ESP32-WROOM-32E / finished product (SARAL Sanchar, ~₹10k).
- [ ] Freeze MPNs/manufacturers in `fab/BOM_procurement.csv` with a distributor.
- [ ] Collect **RoHS CoCs** for all 17 line items.
- [ ] Decide BIS CRS applicability for the final product/adaptor.
- [ ] Change R1–R8 to 220 Ω (recommended) and confirm opto CTR rank.
- [ ] Specify 10 µF X7R ≥10 V and inductor Isat ≥2.5 A.
- [ ] Confirm fab 0.20 mm drill capability (or relax to 0.25 mm).
- [ ] Decide on pre-flashing firmware (IO0/EN are not broken out — see `PRODUCTION_READINESS_AUDIT.md` C-01).
- [ ] Validate RF (antenna keepout residual trace — M-02) if Wi-Fi range matters.

---

## 6. Bottom line

The **PCB design itself is perfect** (clean DRC/ERC, complete fab package) and can be fabricated in India today. It is **not yet fully manufacturing-ready as a sellable Indian product** because of one regulatory item (WPC ETA) and procurement/RoHS documentation gaps. Close the checklist in §5 and it is ready.
