$cli = "C:\Users\aswin\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe"
$dir = "tools\audit"
New-Item -ItemType Directory -Force -Path $dir | Out-Null

Write-Output "=== 1. SCHEMATIC ERC ==="
& $cli sch erc --severity-all --format json -o "$dir\erc_audit.json" ind_8ch_motor_ctrl.kicad_sch 2>&1 | Select-Object -Last 4
Write-Output ("ERC exit code: {0}" -f $LASTEXITCODE)

Write-Output "=== 2. PCB DRC (severity-all) ==="
& $cli pcb drc --severity-all --format json -o "$dir\drc_audit.json" ind_8ch_motor_ctrl.kicad_pcb 2>&1 | Select-Object -Last 4
Write-Output ("DRC exit code: {0}" -f $LASTEXITCODE)

Write-Output "=== 3. PCB DRC + SCHEMATIC PARITY ==="
& $cli pcb drc --schematic-parity --severity-all --format json -o "$dir\drc_parity_audit.json" ind_8ch_motor_ctrl.kicad_pcb 2>&1 | Select-Object -Last 4
Write-Output ("Parity DRC exit code: {0}" -f $LASTEXITCODE)
