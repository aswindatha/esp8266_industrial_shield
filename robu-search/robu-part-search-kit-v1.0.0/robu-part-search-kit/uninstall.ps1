#Requires -Version 5.1
<#
    Robu Part Search - uninstaller
    Removes the installed skill folders. Python packages are left alone.
    Use -WhatIf to preview.
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [ValidateSet('User', 'Project')]
    [string]$Scope = 'User',

    [string]$ProjectDir = '',

    [string[]]$Targets = @('opencode', 'qoder')
)

$ErrorActionPreference = 'Stop'

$allTargets = @('opencode', 'qoder')
$Targets = @($Targets | ForEach-Object { $_.ToLowerInvariant() } | Select-Object -Unique)
if ($Targets -contains 'all') { $Targets = $allTargets }

if ($Scope -eq 'Project') {
    $dir = $ProjectDir
    if ([string]::IsNullOrWhiteSpace($dir)) { $dir = (Get-Location).Path }
    if (-not (Test-Path -LiteralPath $dir)) { throw "Project directory not found: $dir" }
    $dir = (Resolve-Path -LiteralPath $dir).Path
    $roots = @{
        opencode = (Join-Path (Join-Path $dir '.opencode') 'skills')
        qoder    = (Join-Path (Join-Path $dir '.qoder') 'skills')
    }
} else {
    $roots = @{
        opencode = (Join-Path (Join-Path $HOME '.config\opencode') 'skills')
        qoder    = (Join-Path (Join-Path $HOME '.qoder') 'skills')
    }
}

Write-Host ''
Write-Host '  Robu Part Search - uninstaller' -ForegroundColor White
Write-Host ''

$removed = 0
foreach ($t in $Targets) {
    if ($allTargets -notcontains $t) { throw "Unknown target '$t'. Use: opencode, qoder, all." }
    $dest = Join-Path $roots.$t 'robu-part-search'
    if (-not (Test-Path -LiteralPath $dest)) {
        Write-Host "  [skip] $t - not installed" -ForegroundColor Gray
        continue
    }
    if ($PSCmdlet.ShouldProcess($dest, 'Remove skill folder')) {
        Remove-Item -LiteralPath $dest -Recurse -Force
        Write-Host "  [ok]   removed $dest" -ForegroundColor Green
        $removed++
    }
}

Write-Host ''
if ($removed -gt 0) {
    Write-Host "  Removed $removed skill folder(s)." -ForegroundColor Green
    Write-Host '  Python packages (DrissionPage, beautifulsoup4) were left in place.' -ForegroundColor Gray
    Write-Host '  To remove them: python -m pip uninstall DrissionPage beautifulsoup4' -ForegroundColor Gray
} else {
    Write-Host '  Nothing to remove.' -ForegroundColor Gray
}
Write-Host ''
