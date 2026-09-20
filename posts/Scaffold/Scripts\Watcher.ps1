#Requires -Version 5.1

<#
.SYNOPSIS
    Lightweight Ready-folder watcher.

.DESCRIPTION
    Developer/operator helper that monitors Packages\Ready and calls Validator.ps1 for new MSI files. It never installs, moves, or modifies packages. Deployment remains the responsibility of the SYSTEM run engine.
#>

[CmdletBinding()]
param(
    [string]$BaseDir = "C:\Software",
    [int]$QuietSeconds = 3
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ReadyDir = Join-Path $BaseDir "Packages\Ready"
$WatcherLogDir = Join-Path $BaseDir "Logs\Watcher"
$ValidatorPath = Join-Path $BaseDir "Scripts\Validator.ps1"
$LogFile = $null
$Seen = @{}

function Initialize-WatcherLog {
    if (-not (Test-Path -LiteralPath $WatcherLogDir)) {
        New-Item -ItemType Directory -Path $WatcherLogDir -Force | Out-Null
    }
    $script:LogFile = Join-Path $WatcherLogDir ("Watcher_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
}

function Write-WatcherLog {
    param(
        [string]$Message,
        [ValidateSet("INFO","WARN","ERROR","SUCCESS")]
        [string]$Level = "INFO"
    )

    $entry = "[{0}] [{1}] [WATCHER] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"), $Level, $Message
    if ($script:LogFile) {
        Add-Content -LiteralPath $script:LogFile -Value $entry -Encoding UTF8
    }
    Write-Host $entry
}

function Wait-FileReady {
    param([string]$Path)

    Start-Sleep -Seconds $QuietSeconds
    try {
        $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)
        $stream.Close()
        return $true
    }
    catch {
        Write-WatcherLog "File is not ready yet: '$Path'. Reason: $($_.Exception.Message)" -Level WARN
        return $false
    }
}

function Invoke-Validator {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $ValidatorPath -PathType Leaf)) {
        Write-WatcherLog "Validator not found: '$ValidatorPath'." -Level ERROR
        return
    }

    Write-WatcherLog "Calling validator for '$Path'." -Level INFO
    $output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ValidatorPath -MsiPath $Path -BaseDir $BaseDir 2>&1
    $exitCode = $LASTEXITCODE
    $outputText = $output -join "`n"

    if ($exitCode -eq 0) {
        Write-WatcherLog "Validator passed for '$Path'. $outputText" -Level SUCCESS
    }
    else {
        Write-WatcherLog "Validator rejected '$Path'. $outputText" -Level WARN
    }
}

function Test-NewMsi {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) { return }
    if ([System.IO.Path]::GetExtension($Path) -ne ".msi") { return }
    if ($script:Seen.ContainsKey($Path)) { return }
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return }
    if (-not (Wait-FileReady -Path $Path)) { return }

    $script:Seen[$Path] = $true
    Invoke-Validator -Path $Path
}

try {
    Initialize-WatcherLog
    if (-not (Test-Path -LiteralPath $ReadyDir)) {
        New-Item -ItemType Directory -Path $ReadyDir -Force | Out-Null
    }

    Write-WatcherLog "Monitoring Ready directory: '$ReadyDir'." -Level INFO
    Write-WatcherLog "This helper validates only. It does not install or move packages." -Level INFO

    foreach ($existing in @(Get-ChildItem -LiteralPath $ReadyDir -Filter "*.msi" -File -ErrorAction SilentlyContinue)) {
        Test-NewMsi -Path $existing.FullName
    }

    $watcher = New-Object System.IO.FileSystemWatcher
    $watcher.Path = $ReadyDir
    $watcher.Filter = "*.msi"
    $watcher.IncludeSubdirectories = $false
    $watcher.EnableRaisingEvents = $true

    Register-ObjectEvent -InputObject $watcher -EventName Created -SourceIdentifier "ReadyMsiCreated" | Out-Null
    Register-ObjectEvent -InputObject $watcher -EventName Renamed -SourceIdentifier "ReadyMsiRenamed" | Out-Null

    while ($true) {
        $event = Wait-Event -Timeout 5
        if ($null -eq $event) { continue }

        try {
            $path = $event.SourceEventArgs.FullPath
            Write-WatcherLog "Detected MSI event: '$path'." -Level INFO
            Test-NewMsi -Path $path
        }
        finally {
            Remove-Event -EventIdentifier $event.EventIdentifier -ErrorAction SilentlyContinue
        }
    }
}
catch {
    Write-WatcherLog "Watcher error: $($_.Exception.Message)" -Level ERROR
    exit 1
}
finally {
    Unregister-Event -SourceIdentifier "ReadyMsiCreated" -ErrorAction SilentlyContinue
    Unregister-Event -SourceIdentifier "ReadyMsiRenamed" -ErrorAction SilentlyContinue
}
