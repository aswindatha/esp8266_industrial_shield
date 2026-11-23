#Requires -Version 5.1
<#
    Robu Part Search - installer
    ----------------------------
    Installs the robu-part-search skill for OpenCode and Qoder, makes sure
    the Python dependencies are present, and runs a live smoke test.

    Usage:
        powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
        .\install.ps1 -Targets opencode
        .\install.ps1 -Scope Project -ProjectDir C:\path\to\repo
        .\install.ps1 -DryRun

    No administrator rights are required.
#>
[CmdletBinding()]
param(
    [ValidateSet('User', 'Project')]
    [string]$Scope = 'User',

    # Only used with -Scope Project. Defaults to the current directory.
    [string]$ProjectDir = '',

    # opencode, qoder, or all
    [string[]]$Targets = @('opencode', 'qoder'),

    [switch]$SkipDeps,
    [switch]$SkipTest,
    [switch]$DryRun,
    [switch]$InstallPython
)

$ErrorActionPreference = 'Stop'
$script:Failures = 0

function Write-Step([string]$Text) {
    Write-Host ''
    Write-Host "==> $Text" -ForegroundColor Cyan
}

function Write-Ok([string]$Text) {
    Write-Host "    [ok]   $Text" -ForegroundColor Green
}

function Write-Note([string]$Text) {
    Write-Host "    $Text" -ForegroundColor Gray
}

function Write-Warn2([string]$Text) {
    Write-Host "    [warn] $Text" -ForegroundColor Yellow
}

function Write-Fail([string]$Text) {
    Write-Host "    [fail] $Text" -ForegroundColor Red
    $script:Failures++
}

function Get-PythonInfo {
    $candidates = @(
        @{ Exe = 'py';      Prefix = @('-3') },
        @{ Exe = 'py';      Prefix = @() },
        @{ Exe = 'python';  Prefix = @() },
        @{ Exe = 'python3'; Prefix = @() }
    )
    foreach ($c in $candidates) {
        if (-not (Get-Command $c.Exe -CommandType Application -ErrorAction SilentlyContinue)) {
            continue
        }
        $a = @($c.Prefix) + @('-c', 'import sys; print(sys.version_info[0], sys.version_info[1])')
        try {
            $out = & $c.Exe @a 2>$null
            if ($LASTEXITCODE -ne 0) { continue }
            $text = ($out | Out-String).Trim()
            if (-not $text) { continue }
            $line = ($text -split "`r?`n")[0].Trim()
            if ($line -match '^(\d+)\s+(\d+)$') {
                $ver = [version]($Matches[1] + '.' + $Matches[2])
                if ($ver -ge [version]'3.8') {
                    return [pscustomobject]@{
                        Exe = $c.Exe
                        Prefix = @($c.Prefix)
                        Version = $ver.ToString()
                    }
                }
            }
        } catch { }
    }
    return $null
}

function Invoke-Py {
    param($Py, [string[]]$Arguments)
    $a = @($Py.Prefix) + $Arguments
    & $Py.Exe @a
}

function Get-BrowserPath {
    $paths = @()
    if ($env:ProgramFiles) {
        $paths += (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe')
        $paths += (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe')
    }
    $pf86 = ${env:ProgramFiles(x86)}
    if ($pf86) {
        $paths += (Join-Path $pf86 'Google\Chrome\Application\chrome.exe')
        $paths += (Join-Path $pf86 'Microsoft\Edge\Application\msedge.exe')
    }
    if ($env:LOCALAPPDATA) {
        $paths += (Join-Path $env:LOCALAPPDATA 'Google\Chrome\Application\chrome.exe')
        $paths += (Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\Application\msedge.exe')
    }
    foreach ($p in $paths) {
        if (Test-Path -LiteralPath $p) { return $p }
    }
    return $null
}

function Get-SkillRoots {
    param([string]$Mode, [string]$ProjectPath)
    if ($Mode -eq 'Project') {
        $dir = $ProjectPath
        if ([string]::IsNullOrWhiteSpace($dir)) { $dir = (Get-Location).Path }
        if (-not (Test-Path -LiteralPath $dir)) { throw "Project directory not found: $dir" }
        $dir = (Resolve-Path -LiteralPath $dir).Path
        return [pscustomobject]@{
            opencode = (Join-Path (Join-Path $dir '.opencode') 'skills')
            qoder    = (Join-Path (Join-Path $dir '.qoder') 'skills')
            base     = $dir
        }
    }
    return [pscustomobject]@{
        opencode = (Join-Path (Join-Path $HOME '.config\opencode') 'skills')
        qoder    = (Join-Path (Join-Path $HOME '.qoder') 'skills')
        base     = $HOME
    }
}

function Get-Sha256 {
    param([string]$Path)
    # .NET hash instead of Get-FileHash: works even when a PowerShell 7
    # module path is inherited by Windows PowerShell 5.1
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $stream = [System.IO.File]::OpenRead($Path)
    try {
        return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-', '')
    } finally {
        $stream.Dispose()
        $sha.Dispose()
    }
}

function Get-PayloadSignature {
    param([string]$SkillPath, [string]$ScriptPath)
    return ((Get-Sha256 -Path $SkillPath) + (Get-Sha256 -Path $ScriptPath))
}

# ------------------------------------------------------------------ start

Write-Host ''
Write-Host '  Robu Part Search - installer' -ForegroundColor White
Write-Host '  OpenCode + Qoder skill for robu.in component search' -ForegroundColor DarkGray
Write-Host ''

$Payload   = Join-Path $PSScriptRoot 'skill'
$SrcSkill  = Join-Path $Payload 'SKILL.md'
$SrcScript = Join-Path (Join-Path $Payload 'scripts') 'search_robu.py'
$SrcReq    = Join-Path $Payload 'requirements.txt'

foreach ($p in @($SrcSkill, $SrcScript, $SrcReq)) {
    if (-not (Test-Path -LiteralPath $p)) {
        throw "Package is incomplete - missing: $p"
    }
}

$allTargets = @('opencode', 'qoder')
$Targets = @($Targets | ForEach-Object { $_.ToLowerInvariant() } | Select-Object -Unique)
if ($Targets -contains 'all') { $Targets = $allTargets }
if ($Targets.Count -eq 0) { throw 'No targets selected. Use -Targets opencode,qoder' }
foreach ($t in $Targets) {
    if ($allTargets -notcontains $t) {
        throw "Unknown target '$t'. Use: opencode, qoder, all."
    }
}

$roots = Get-SkillRoots -Mode $Scope -ProjectPath $ProjectDir
$installed = @()

if ($DryRun) {
    Write-Note 'DRY RUN - no files will be changed and pip will not run.'
}

# ------------------------------------------------------------------ python

Write-Step 'Python'
$py = Get-PythonInfo

if (-not $py -and $InstallPython) {
    $winget = Get-Command winget -CommandType Application -ErrorAction SilentlyContinue
    if (-not $winget) {
        Write-Fail 'Python 3.8+ not found and winget is unavailable.'
        Write-Note 'Install Python from https://www.python.org/downloads/windows/ (tick "Add python.exe to PATH"), then re-run.'
    } else {
        Write-Note 'Python not found - installing Python 3.12 with winget...'
        if ($DryRun) {
            Write-Note '[dry-run] winget install -e --id Python.Python.3.12 --scope user'
        } else {
            & winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
            $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
            $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
            $env:Path = "$machinePath;$userPath"
            $py = Get-PythonInfo
        }
    }
}

if (-not $py) {
    if (-not $DryRun) {
        Write-Fail 'Python 3.8+ was not found.'
        Write-Note 'Install it, then re-run install.bat:'
        Write-Note '  winget install -e --id Python.Python.3.12 --scope user'
        Write-Note '  https://www.python.org/downloads/windows/'
    }
} else {
    $prefixText = ($py.Prefix -join ' ')
    Write-Ok ("Python {0}  ({1} {2})" -f $py.Version, $py.Exe, $prefixText)
}

# ------------------------------------------------------------------ packages

if ($py -and -not $SkipDeps) {
    Write-Step 'Python packages'
    $probeOut = Invoke-Py -Py $py -Arguments @('-c', 'import DrissionPage, bs4; print(DrissionPage.__version__)') 2>&1
    $probeOk = ($LASTEXITCODE -eq 0)

    if ($probeOk) {
        $ver = ($probeOut | Out-String).Trim()
        Write-Ok "DrissionPage $ver and beautifulsoup4 are installed"
    } elseif ($DryRun) {
        Write-Note '[dry-run] pip install --user -r skill\requirements.txt'
    } else {
        Write-Note 'Installing DrissionPage and beautifulsoup4 (user site)...'

        $pipArgs = @('-m', 'pip', 'install', '--user', '--upgrade', '-r', $SrcReq)
        Invoke-Py -Py $py -Arguments $pipArgs
        $pipOk = ($LASTEXITCODE -eq 0)

        if (-not $pipOk) {
            Write-Note 'pip failed - trying ensurepip...'
            Invoke-Py -Py $py -Arguments @('-m', 'ensurepip', '--upgrade') | Out-Null
            Invoke-Py -Py $py -Arguments $pipArgs
            $pipOk = ($LASTEXITCODE -eq 0)
        }

        if (-not $pipOk) {
            Write-Note 'Retrying without --user...'
            Invoke-Py -Py $py -Arguments @('-m', 'pip', 'install', '--upgrade', '-r', $SrcReq)
            $pipOk = ($LASTEXITCODE -eq 0)
        }

        $checkOut = Invoke-Py -Py $py -Arguments @('-c', 'import DrissionPage, bs4; print(1)') 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Ok 'Dependencies installed'
        } else {
            Write-Fail 'Dependencies are still not importable.'
            Write-Note ($checkOut | Out-String).Trim()
            Write-Note 'See README.md (Troubleshooting).'
        }
    }
} elseif ($SkipDeps) {
    Write-Note 'Skipping dependency install (-SkipDeps)'
}

# ------------------------------------------------------------------ browser

Write-Step 'Browser'
$browser = Get-BrowserPath
if ($browser) {
    Write-Ok "Found $browser"
} else {
    Write-Warn2 'Chrome/Edge not found in standard locations.'
    Write-Note 'Install Chrome or Edge before running searches.'
}

# ------------------------------------------------------------------ install

Write-Step 'Skill files'
$srcSig = Get-PayloadSignature -SkillPath $SrcSkill -ScriptPath $SrcScript

foreach ($t in $Targets) {
    $root = $roots.$t
    $dest = Join-Path $root 'robu-part-search'

    if ($DryRun) {
        Write-Note ("[dry-run] {0} -> {1}" -f $t, $dest)
        continue
    }

    if (-not (Test-Path -LiteralPath $root)) {
        New-Item -ItemType Directory -Path $root -Force | Out-Null
    }

    $same = $false
    if (Test-Path -LiteralPath $dest) {
        $dSkill  = Join-Path $dest 'SKILL.md'
        $dScript = Join-Path (Join-Path $dest 'scripts') 'search_robu.py'
        if ((Test-Path -LiteralPath $dSkill) -and (Test-Path -LiteralPath $dScript)) {
            $destSig = Get-PayloadSignature -SkillPath $dSkill -ScriptPath $dScript
            $same = ($destSig -eq $srcSig)
        }
    }

    if ($same) {
        Write-Ok "$t - already up to date"
        Write-Note $dest
        $installed += $dest
        continue
    }

    if (Test-Path -LiteralPath $dest) {
        $backup = $dest + '.bak-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
        try {
            Move-Item -LiteralPath $dest -Destination $backup -Force
            Write-Note "Previous version backed up to $backup"
        } catch {
            Write-Warn2 "Could not move the old folder ($($_.Exception.Message)); overwriting in place."
        }
    }

    New-Item -ItemType Directory -Path $dest -Force | Out-Null
    Copy-Item -Path (Join-Path $Payload '*') -Destination $dest -Recurse -Force
    Write-Ok "$t - installed"
    Write-Note $dest
    $installed += $dest
}

# ------------------------------------------------------------------ test

if ($py -and -not $SkipTest -and -not $DryRun -and $installed.Count -gt 0) {
    Write-Step 'Smoke test'
    $testScript = Join-Path (Join-Path $installed[0] 'scripts') 'search_robu.py'
    Write-Note 'Searching robu.in for LTV-356T - a Chrome window may open briefly...'
    $testOut = Invoke-Py -Py $py -Arguments @($testScript, 'LTV-356T', '--fast', '--top', '1') 2>&1
    $text = ($testOut | Out-String)
    if ($text -match 'robu\.in/product/') {
        Write-Ok 'Live search returned a product link'
    } else {
        Write-Warn2 'Smoke test did not return a product link.'
        Write-Note 'The install is fine; check network/Cloudflare with doctor.ps1.'
        $first = ($text.Trim() -split "`r?`n")[0]
        if ($first) { Write-Note $first }
    }
}

# ------------------------------------------------------------------ summary

Write-Step 'Summary'

if ($DryRun) {
    Write-Note 'Dry run complete. Re-run without -DryRun to install.'
    exit 0
}

if ($script:Failures -gt 0) {
    Write-Host "  Finished with $($script:Failures) problem(s)." -ForegroundColor Red
    exit 1
}

Write-Host '  Installed:' -ForegroundColor Green
foreach ($d in $installed) { Write-Host "    $d" }
Write-Host ''
Write-Host '  OpenCode: skills reload automatically; start a session and ask' -ForegroundColor Gray
Write-Host '            "Search robu.in for LTV-356T" (or @robu-part-search).' -ForegroundColor Gray
Write-Host '  Qoder:    open a new session, or run /skills reload, then ask' -ForegroundColor Gray
Write-Host '            the same question (or /robu-part-search).' -ForegroundColor Gray
Write-Host ''
Write-Host '  CLI:      python "<installed>\scripts\search_robu.py" "LTV-356T" --table' -ForegroundColor Gray
Write-Host ''
exit 0
