# Run three sample queries with BOM quantities.
# Usage: right-click > Run with PowerShell, or: .\demo.ps1

$ErrorActionPreference = 'Stop'

$kitRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$script = Join-Path (Join-Path (Join-Path $kitRoot 'skill') 'scripts') 'search_robu.py'
if (-not (Test-Path -LiteralPath $script)) {
    throw "Cannot find skill\scripts\search_robu.py - run this from the kit's examples folder."
}

$exe = $null
$prefix = @()
if (Get-Command py -CommandType Application -ErrorAction SilentlyContinue) {
    & py -3 -c "import sys" 2>$null
    if ($LASTEXITCODE -eq 0) { $exe = 'py'; $prefix = @('-3') }
}
if (-not $exe -and (Get-Command python -CommandType Application -ErrorAction SilentlyContinue)) {
    $exe = 'python'
}
if (-not $exe) {
    throw 'Python not found. Run install.bat first.'
}

Write-Host ''
Write-Host 'Running 3 sample robu.in queries...' -ForegroundColor Cyan
Write-Host 'A Chrome window may open briefly (expected).' -ForegroundColor DarkGray
Write-Host ''

$runArgs = @($prefix) + @(
    $script,
    'LTV-356T',
    'NE555 timer',
    '4 pin 5mm pluggable screw terminal',
    '--qty', '4,2,10',
    '--table',
    '--top', '1'
)

& $exe @runArgs
exit $LASTEXITCODE
