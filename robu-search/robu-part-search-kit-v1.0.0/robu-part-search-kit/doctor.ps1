#Requires -Version 5.1
<#
    Robu Part Search - doctor
    Checks Python, packages, browser, installed skill folders and network.
    Read-only: nothing is modified.
#>
[CmdletBinding()]
param(
    [string[]]$Targets = @('opencode', 'qoder')
)

$ErrorActionPreference = 'Stop'
$problems = 0
$warnings = 0

function Write-Ok([string]$Text)  { Write-Host "  [ok]   $Text" -ForegroundColor Green }
function Write-Warn2([string]$Text) { Write-Host "  [warn] $Text" -ForegroundColor Yellow; $script:warnings++ }
function Write-Fail([string]$Text) { Write-Host "  [fail] $Text" -ForegroundColor Red; $script:problems++ }

function Get-PythonInfo {
    $candidates = @(
        @{ Exe = 'py';      Prefix = @('-3') },
        @{ Exe = 'py';      Prefix = @() },
        @{ Exe = 'python';  Prefix = @() },
        @{ Exe = 'python3'; Prefix = @() }
    )
    foreach ($c in $candidates) {
        if (-not (Get-Command $c.Exe -CommandType Application -ErrorAction SilentlyContinue)) { continue }
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
                    return [pscustomobject]@{ Exe = $c.Exe; Prefix = @($c.Prefix); Version = $ver.ToString() }
                }
            }
        } catch { }
    }
    return $null
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
    foreach ($p in $paths) { if (Test-Path -LiteralPath $p) { return $p } }
    return $null
}

function Test-SkillFolder {
    param([string]$Label, [string]$Path)
    Write-Host ''
    Write-Host "  $Label" -ForegroundColor White
    if (-not (Test-Path -LiteralPath $Path)) {
        Write-Warn2 "not installed: $Path"
        return
    }
    $skillFile = Join-Path $Path 'SKILL.md'
    $scriptFile = Join-Path (Join-Path $Path 'scripts') 'search_robu.py'

    if (Test-Path -LiteralPath $skillFile) {
        $head = (Get-Content -LiteralPath $skillFile -TotalCount 12) -join "`n"
        if ($head -match '(?m)^name:\s*robu-part-search\s*$') {
            Write-Ok 'SKILL.md frontmatter ok'
        } else {
            Write-Warn2 'SKILL.md found, but name: robu-part-search not in the first lines'
        }
    } else {
        Write-Fail 'missing SKILL.md'
    }

    if (Test-Path -LiteralPath $scriptFile) {
        $size = (Get-Item -LiteralPath $scriptFile).Length
        Write-Ok ("script ok ({0:n0} bytes)" -f $size)
    } else {
        Write-Fail 'missing scripts\search_robu.py'
    }
}

Write-Host ''
Write-Host '  Robu Part Search - doctor' -ForegroundColor White
Write-Host '  ---------------------------' -ForegroundColor DarkGray

# Python
Write-Host ''
Write-Host '  Python' -ForegroundColor White
$py = Get-PythonInfo
if ($py) {
    Write-Ok ("Python {0} ({1} {2})" -f $py.Version, $py.Exe, ($py.Prefix -join ' '))
} else {
    Write-Fail 'Python 3.8+ not found (or not on PATH)'
}

# Packages + script help
if ($py) {
    Write-Host ''
    Write-Host '  Python packages' -ForegroundColor White
    $probe = & $py.Exe @(@($py.Prefix) + @('-c', 'import DrissionPage, bs4; print(DrissionPage.__version__)')) 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Ok ("DrissionPage {0} + beautifulsoup4" -f (($probe | Out-String).Trim()))
    } else {
        Write-Fail 'DrissionPage/beautifulsoup4 not importable - run install.bat'
    }
}

# Browser
Write-Host ''
Write-Host '  Browser' -ForegroundColor White
$browser = Get-BrowserPath
if ($browser) { Write-Ok $browser } else { Write-Fail 'Chrome/Edge not found in standard locations' }

# Installed skills
foreach ($t in $Targets) {
    if ($t -eq 'opencode') {
        Test-SkillFolder -Label 'OpenCode (user)' -Path (Join-Path (Join-Path $HOME '.config\opencode\skills') 'robu-part-search')
    } elseif ($t -eq 'qoder') {
        Test-SkillFolder -Label 'Qoder (user)' -Path (Join-Path (Join-Path $HOME '.qoder\skills') 'robu-part-search')
    }
}

# Script help (syntax check)
if ($py) {
    $installed = Join-Path (Join-Path $HOME '.config\opencode\skills') 'robu-part-search'
    $candidate = Join-Path (Join-Path $installed 'scripts') 'search_robu.py'
    if (Test-Path -LiteralPath $candidate) {
        Write-Host ''
        Write-Host '  Script check' -ForegroundColor White
        $help = & $py.Exe @(@($py.Prefix) + @($candidate, '--help')) 2>&1
        if ($LASTEXITCODE -eq 0 -and (($help | Out-String) -match 'usage:')) {
            Write-Ok '--help runs'
        } else {
            Write-Fail 'script did not run cleanly'
        }
    }
}

# Network
Write-Host ''
Write-Host '  robu.in reachability' -ForegroundColor White
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch { }
try {
    $req = [System.Net.WebRequest]::Create('https://robu.in/')
    $req.Method = 'HEAD'
    $req.Timeout = 10000
    $resp = $req.GetResponse()
    Write-Ok ("HTTP {0}" -f [int]$resp.StatusCode)
    $resp.Close()
} catch [System.Net.WebException] {
    if ($_.Exception.Response) {
        Write-Ok 'reachable (Cloudflare or HTTP response received)'
    } else {
        Write-Warn2 ("could not connect: {0}" -f $_.Exception.Message)
    }
} catch {
    Write-Warn2 ("could not connect: {0}" -f $_.Exception.Message)
}

Write-Host ''
if ($problems -gt 0) {
    Write-Host "  Result: $problems problem(s), $warnings warning(s)" -ForegroundColor Red
    exit 1
}
Write-Host "  Result: healthy ($warnings warning(s))" -ForegroundColor Green
exit 0
