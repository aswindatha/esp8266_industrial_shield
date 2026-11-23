# ind_8ch_motor_ctrl — Industrial 8-channel motor controller

**100 × 100 mm, 2-layer, fabrication-ready.** ESP32-WROOM-32E, eight opto-isolated
motor channels, four opto-coupled field inputs, I²C + UART, 12 V input with
buck + LDO regulation.

## Status: FABRICATION READY

| Gate | Result |
|---|---|
| Unconnected items (DRC) | **0** |
| Clearance / short / courtyard / hole DRC | **0** |
| Routing | **100 %** (Freerouting 2.5.0, score 1000/1000, 0 violations) |
| Copper layers | F.Cu + B.Cu, B.Cu solid GND return plane, F.Cu 12V_PROT power plane |
| Tracks / vias | ~800 tracks, 83 vias (0.6/0.3 mm) |
| Remaining DRC | 5 **non-fab** library-link warnings only (see "Known warnings") |

## Board architecture

- **Outline:** 100.0 × 100.0 mm, four 3.2 mm mounting holes.
- **Left edge — `J_IN` (INPUT, 20-position, 5.08 mm pitch):**
  the *only* input connector on the board.
- **Right edge — `J_OUT` (OUTPUT, 20-position, 5.08 mm pitch):**
  the *only* output connector on the board.
- Both are standard CUI TB007-508-20 horizontal terminal blocks.
- All other former connectors (power, motor, sensor, I²C header, PROG header)
  were removed; their signals were rerouted to the two terminal blocks.

### `J_IN` pinout (left / INPUT)

| Pin | Net | Function |
|-----|-----|----------|
| 1 | `12V_RAW` | 12 V supply input (before protection) |
| 2 | `GND` | Supply / logic ground |
| 3 | `12V_PROT` | Protected 12 V — sensor field supply |
| 4 | `SENS_IN1` | Field sensor input 1 |
| 5 | `SENS_IN2` | Field sensor input 2 |
| 6 | `SENS_IN3` | Field sensor input 3 |
| 7 | `SENS_IN4` | Field sensor input 4 |
| 8 | `3V3_RAIL` | 3.3 V logic rail (also on J_OUT area) |
| 9 | `I2C_SDA` | I²C data |
| 10 | `I2C_SCL` | I²C clock |
| 11 | `UART_TX` | UART transmit |
| 12 | `UART_RX` | UART receive |
| 13–20 | — | **NC — not connected** (labelled on silkscreen) |

### `J_OUT` pinout (right / OUTPUT)

| Pin | Net | Function |
|-----|-----|----------|
| 1 | `MOT1` | Motor output 1 (ULN2803 open-drain sink) |
| 2 | `MOT2` | Motor output 2 |
| 3 | `MOT3` | Motor output 3 |
| 4 | `MOT4` | Motor output 4 |
| 5 | `MOT5` | Motor output 5 |
| 6 | `MOT6` | Motor output 6 |
| 7 | `MOT7` | Motor output 7 |
| 8 | `MOT8` | Motor output 8 |
| 9 | `12V_PROT` | Protected 12 V — motor supply common |
| 10–20 | — | **NC — not connected** (labelled on silkscreen) |

> Motors connect between `12V_PROT` (J_OUT.9) and the relevant `MOTx` sink.
> Field sensors are powered from `12V_PROT` (J_IN.3) and return via `SENS_INx`
> against `GND` (J_IN.2).

## Design rules / stackup

- 1.6 mm FR-4, 1 oz copper, 2 layers.
- Min track 0.2 mm; routed signal track 0.35 mm (0.262 mm necks at fine-pitch pins).
- Clearance 0.25 mm; copper-to-edge 0.3 mm.
- Vias 0.6 mm outer / 0.3 mm drill, tented.
- B.Cu: continuous GND plane with thermal-relief connections.
- F.Cu: 12V_PROT power plane for high motor current, auto-cleared around signals.
- TVS + reverse-polarity diode on the 12 V input; buck (XL1509-5.0) → 5 V,
  LDO (AMS1117-3.3) → 3.3 V.

## Fabrication package (`fab/`)

| File | Contents |
|---|---|
| `*.gtl`, `*.gbl` | F.Cu / B.Cu copper (Gerber X2) |
| `*.gts`, `*.gbs` | F.Cu / B.Cu solder mask |
| `*.gto`, `*.gbo` | F.Cu / B.Cu silkscreen |
| `*.gtp`, `*.gbp` | F.Cu / B.Cu paste |
| `*.gm1` | Board outline / Edge.Cuts |
| `*.gbrjob` | Gerber job file |
| `*.drl`, `drill_report.txt`, `*-drl_map.pdf` | Excellon drills + map |
| `pos.csv` | Pick-and-place (mm, both sides) |
| `BOM.csv`, `BOM_grouped.csv` | Board-accurate BOM (46 parts + 4 mounting holes) |
| `netlist.ipc356` | IPC-D-356 test netlist |
| `assembly_top.pdf`, `top.svg` | Assembly / layout plots |

Gerbers and drills were exported with KiCad 10.0.8.

## Known warnings (non-fab)

Five DRC library-link warnings remain and **do not affect Gerbers or assembly**:

- `U_MCU1` footprint differs slightly from the current `RF_Module` library copy
  (the board copy omits the library's large antenna-courtyard outline graphic).
- `MH1–MH4` FPID names use the legacy `MountingHole_3.2mm` item name; the
  installed library calls it `MountingHole_3.2mm_M3`. Hole geometry is identical.

## Schematic note

The PCB netlist is complete and internally consistent (DRC reports 0
unconnected items and, with `--schematic-parity`, only the 5 expected connector
reference differences). The schematic file still shows the **five original
connectors** — it documents the underlying circuit, while the PCB implements
the two-terminal-block I/O requested for this revision. If schematic/PCB parity
is required in your flow, replace those five connector symbols with two
20-position terminal-block symbols using the pin tables above.

## Rebuild flow (tools/)

```powershell
$PY  = "C:\Users\aswin\AppData\Local\Programs\KiCad\10.0\bin\python.exe"
$JAVA = "tools\jre25\jdk-25.0.5.1+2-jre\bin\java.exe"

Copy-Item ind_8ch_motor_ctrl.kicad_pcb.pre_v2.bak ind_8ch_motor_ctrl.kicad_pcb -Force
& $PY tools/build_v2.py                 # 100x100 board, TBs, placement, nets
& $PY tools/export_dsn.py               # Specctra DSN
& $JAVA -jar tools/freerouting-2.5.0.jar --gui.enabled=false `
    -de tools/board.dsn -do tools/board_route.ses --router.autorouter.max_passes=30
& $PY tools/finalize.py                 # import SES, add GND/PWR planes
& $PY tools/cleanup.py                  # silkscreen / mounting-hole cleanup
& $PY tools/cleanup3.py                 # final mounting-hole positioning
& $PY tools/cleanup4.py                 # NC label spacing
& $PY tools/make_bom.py                 # BOM from final board
```

Electrical note: single ground, no galvanic isolation. The 12 V motor rail and
3.3 V logic share a return; the optocouplers provide level shifting and noise
separation only. Do not use where isolation is a safety requirement.
