#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Collects logs and forensic evidence from a Windows host (intended for a
    Domain Controller) for threat hunting / incident response, following the
    Scaffold blue-team evidence-collection guide.

.DESCRIPTION
    - Exports key Windows Event Logs (evtx + readable CSV) with no log-clearing.
    - Captures live system state (processes, network connections, services,
      scheduled tasks, local/AD accounts, autoruns-style persistence points).
    - Pulls IIS logs, AD CS / Certification Authority logs, and (if present)
      MDT deployment share config files, without modifying source data.
    - Hashes every collected file (SHA256) into a manifest for chain of custody.
    - Packages everything into a single timestamped zip.

    Run this ELEVATED, ideally from a read-only/forensic mindset: it only reads
    and copies, it never deletes or clears anything.

.NOTES
    Run on the Domain Controller (or target host) itself, or point -RemoteComputer
    at a host you can reach via WinRM/PSRemoting with appropriate rights.
#>

[CmdletBinding()]
param(
    [string]$OutputRoot = "C:\Evidence",
    [string]$CaseName   = "Scaffold-IR-$(Get-Date -Format yyyyMMdd_HHmmss)",
    [string[]]$RemoteComputer,          # optional: run against remote host(s) via PSRemoting
    [int]$EventLogMaxEvents = 50000,    # cap per log to avoid runaway exports on huge logs
    [switch]$SkipZip
)

$ErrorActionPreference = 'Continue'
$caseDir = Join-Path $OutputRoot $CaseName
$dirs = @{
    EventLogs   = Join-Path $caseDir "EventLogs"
    SystemState = Join-Path $caseDir "SystemState"
    IIS         = Join-Path $caseDir "IIS_Logs"
    ADCS        = Join-Path $caseDir "ADCS"
    MDT         = Join-Path $caseDir "MDT_Deployment"
    AD          = Join-Path $caseDir "AD_Objects"
    Network     = Join-Path $caseDir "Network"
}
foreach ($d in $dirs.Values) { New-Item -ItemType Directory -Path $d -Force | Out-Null }

$manifestPath = Join-Path $caseDir "manifest_sha256.csv"
$manifest = New-Object System.Collections.Generic.List[object]
$transcriptPath = Join-Path $caseDir "collection_transcript.log"
Start-Transcript -Path $transcriptPath -Append | Out-Null

function Add-ToManifest {
    param([string]$Path)
    if (Test-Path $Path -PathType Leaf) {
        try {
            $hash = Get-FileHash -Path $Path -Algorithm SHA256 -ErrorAction Stop
            $manifest.Add([PSCustomObject]@{
                Path       = $Path
                SHA256     = $hash.Hash
                SizeBytes  = (Get-Item $Path).Length
                CollectedUtc = (Get-Date).ToUniversalTime().ToString("o")
            })
        } catch {
            Write-Warning "Could not hash $Path : $_"
        }
    }
}

function Write-Section($name) {
    Write-Host "`n===== $name =====" -ForegroundColor Cyan
}

# -------------------------------------------------------------------------
# 1. Windows Event Logs — the core sources from the hunting guide
# -------------------------------------------------------------------------
Write-Section "Exporting Windows Event Logs"

$logsToCollect = @(
    'Security',
    'System',
    'Application',
    'Directory Service',
    'DNS Server',
    'Microsoft-Windows-PowerShell/Operational',
    'Windows PowerShell',
    'Microsoft-Windows-Sysmon/Operational',
    'Microsoft-Windows-WMI-Activity/Operational',
    'Microsoft-Windows-TaskScheduler/Operational',
    'Microsoft-Windows-CertificateServicesClient-Lifecycle-System/Operational',
    'Microsoft-Windows-CAPI2/Operational',
    'Microsoft-Windows-SMBServer/Audit',
    'Microsoft-Windows-SMBServer/Security',
    'Microsoft-Windows-NTLM/Operational',
    'Microsoft-Windows-Kerberos/Operational'
)

foreach ($logName in $logsToCollect) {
    $safeName = ($logName -replace '[\\/]', '_')
    try {
        $exists = Get-WinEvent -ListLog $logName -ErrorAction Stop
        if ($exists.RecordCount -eq 0) {
            Write-Host "  [skip] $logName is empty"
            continue
        }

        # Native .evtx copy preserves full fidelity for forensic tooling
        $evtxOut = Join-Path $dirs.EventLogs "$safeName.evtx"
        wevtutil epl "$logName" "$evtxOut" 2>$null
        if (Test-Path $evtxOut) { Add-ToManifest $evtxOut }

        # Readable CSV for quick triage / SIEM ingestion, capped for size
        $csvOut = Join-Path $dirs.EventLogs "$safeName.csv"
        Get-WinEvent -LogName $logName -MaxEvents $EventLogMaxEvents -ErrorAction Stop |
            Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message |
            Export-Csv -Path $csvOut -NoTypeInformation -Encoding UTF8
        if (Test-Path $csvOut) { Add-ToManifest $csvOut }

        Write-Host "  [ok] $logName"
    } catch {
        Write-Host "  [unavailable] $logName ($($_.Exception.Message))" -ForegroundColor DarkYellow
    }
}

# Targeted high-value event ID pulls called out in the hunting guide
Write-Section "Pulling high-priority event IDs into focused CSVs"
$priorityPulls = @(
    @{ Log='Security'; Ids=4624,4625,4634,4648,4672,4768,4769,4771 ; Name='Logon_Kerberos_Events' }
    @{ Log='Security'; Ids=4728,4732,4756,5136,5137,5141             ; Name='DS_Change_And_GroupMembership' }
    @{ Log='Security'; Ids=4661,4662,4663                            ; Name='ObjectAccess' }
    @{ Log='Security'; Ids=4741,4742,4743                            ; Name='ComputerAccountChanges' }
    @{ Log='Security'; Ids=5140,5145                                 ; Name='FileShareAccess' }
    @{ Log='Security'; Ids=4886,4887,4888,4889                       ; Name='CertificateServices' }
)
foreach ($pull in $priorityPulls) {
    try {
        $filterXml = @"
<QueryList>
  <Query Id="0" Path="$($pull.Log)">
    <Select Path="$($pull.Log)">*[System[($(($pull.Ids | ForEach-Object {"EventID=$_"}) -join ' or '))]]</Select>
  </Query>
</QueryList>
"@
        $out = Join-Path $dirs.EventLogs "Priority_$($pull.Name).csv"
        Get-WinEvent -FilterXml $filterXml -ErrorAction Stop |
            Select-Object TimeCreated, Id, LevelDisplayName, Message |
            Export-Csv -Path $out -NoTypeInformation -Encoding UTF8
        if (Test-Path $out) { Add-ToManifest $out; Write-Host "  [ok] $($pull.Name)" }
    } catch {
        Write-Host "  [none/unavailable] $($pull.Name)" -ForegroundColor DarkYellow
    }
}

# -------------------------------------------------------------------------
# 2. Live system state
# -------------------------------------------------------------------------
Write-Section "Capturing live system state"

$stateJobs = @(
    @{ Name='Processes.csv';        Cmd = { Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,CommandLine,ExecutablePath,CreationDate } }
    @{ Name='Services.csv';         Cmd = { Get-CimInstance Win32_Service | Select-Object Name,DisplayName,State,StartMode,PathName,StartName } }
    @{ Name='ScheduledTasks.csv';   Cmd = { Get-ScheduledTask | ForEach-Object { $i = Get-ScheduledTaskInfo $_; [PSCustomObject]@{ TaskName=$_.TaskName; Path=$_.TaskPath; State=$_.State; Actions=($_.Actions.Execute -join ';'); Args=($_.Actions.Arguments -join ';'); LastRun=$i.LastRunTime; NextRun=$i.NextRunTime } } } }
    @{ Name='NetTCPConnections.csv';Cmd = { Get-NetTCPConnection | Select-Object LocalAddress,LocalPort,RemoteAddress,RemotePort,State,OwningProcess } }
    @{ Name='DnsClientCache.csv';   Cmd = { Get-DnsClientCache | Select-Object Entry,RecordName,RecordType,Data } }
    @{ Name='LocalUsers.csv';       Cmd = { Get-LocalUser | Select-Object Name,Enabled,LastLogon,PasswordLastSet } }
    @{ Name='LocalGroupMembers_Administrators.csv'; Cmd = { Get-LocalGroupMember -Group 'Administrators' } }
    @{ Name='InstalledSoftware.csv';Cmd = { Get-CimInstance Win32_Product | Select-Object Name,Version,InstallDate,Vendor } }
    @{ Name='AutorunsRegistry.csv'; Cmd = {
            $paths = @(
                'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
                'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce',
                'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
            )
            foreach ($p in $paths) {
                if (Test-Path $p) {
                    Get-Item $p | Select-Object -ExpandProperty Property | ForEach-Object {
                        [PSCustomObject]@{ Key=$p; Name=$_; Value=(Get-ItemProperty -Path $p -Name $_).$_ }
                    }
                }
            }
        }
    }
)

foreach ($job in $stateJobs) {
    try {
        $out = Join-Path $dirs.SystemState $job.Name
        & $job.Cmd | Export-Csv -Path $out -NoTypeInformation -Encoding UTF8
        Add-ToManifest $out
        Write-Host "  [ok] $($job.Name)"
    } catch {
        Write-Host "  [failed] $($job.Name): $($_.Exception.Message)" -ForegroundColor DarkYellow
    }
}

# netstat with process names, raw text as a redundant cross-check
$netstatOut = Join-Path $dirs.Network "netstat_ano.txt"
netstat -ano | Out-File -FilePath $netstatOut -Encoding utf8
Add-ToManifest $netstatOut

# -------------------------------------------------------------------------
# 3. Active Directory objects — recent/suspicious changes
# -------------------------------------------------------------------------
Write-Section "Collecting Active Directory object state"

if (Get-Module -ListAvailable -Name ActiveDirectory) {
    Import-Module ActiveDirectory -ErrorAction SilentlyContinue

    try {
        Get-ADUser -Filter * -Properties whenCreated,whenChanged,userAccountControl,LastLogonDate,Description |
            Select-Object SamAccountName,Enabled,whenCreated,whenChanged,userAccountControl,LastLogonDate,Description |
            Export-Csv (Join-Path $dirs.AD "AD_Users.csv") -NoTypeInformation -Encoding UTF8
        Add-ToManifest (Join-Path $dirs.AD "AD_Users.csv")

        Get-ADGroup -Filter * -Properties whenCreated,whenChanged,groupType,GroupCategory,GroupScope |
            Select-Object SamAccountName,whenCreated,whenChanged,groupType,GroupCategory,GroupScope |
            Export-Csv (Join-Path $dirs.AD "AD_Groups.csv") -NoTypeInformation -Encoding UTF8
        Add-ToManifest (Join-Path $dirs.AD "AD_Groups.csv")

        Get-ADComputer -Filter * -Properties whenCreated,whenChanged,LastLogonDate,DistinguishedName |
            Select-Object Name,whenCreated,whenChanged,LastLogonDate,DistinguishedName |
            Export-Csv (Join-Path $dirs.AD "AD_Computers.csv") -NoTypeInformation -Encoding UTF8
        Add-ToManifest (Join-Path $dirs.AD "AD_Computers.csv")

        # Flag computer/user objects created in the last 14 days — cheap tripwire for rogue accounts
        $cutoff = (Get-Date).AddDays(-14)
        Get-ADObject -Filter { whenCreated -ge $cutoff } -Properties whenCreated,ObjectClass |
            Select-Object Name,ObjectClass,whenCreated,DistinguishedName |
            Export-Csv (Join-Path $dirs.AD "AD_RecentlyCreatedObjects_14d.csv") -NoTypeInformation -Encoding UTF8
        Add-ToManifest (Join-Path $dirs.AD "AD_RecentlyCreatedObjects_14d.csv")

        Write-Host "  [ok] AD user/group/computer/recent-object exports"
    } catch {
        Write-Warning "AD module present but query failed: $_"
    }
} else {
    Write-Host "  [skip] ActiveDirectory PowerShell module not available on this host" -ForegroundColor DarkYellow
}

# -------------------------------------------------------------------------
# 4. AD CS / Certification Authority logs and issued-certificate list
# -------------------------------------------------------------------------
Write-Section "Collecting AD CS / Certification Authority data"

if (Get-Command certutil.exe -ErrorAction SilentlyContinue) {
    try {
        $caViewOut = Join-Path $dirs.ADCS "CA_IssuedCertificates.csv"
        # -view -out limits columns; adjust as needed for your CA's field set
        certutil.exe -view -out "RequestID,Request.RequesterName,CommonName,NotBefore,NotAfter,CertificateTemplate,SerialNumber" csv > $caViewOut 2>$null
        if (Test-Path $caViewOut) { Add-ToManifest $caViewOut; Write-Host "  [ok] CA issued-certificate export" }
    } catch {
        Write-Host "  [failed] certutil CA view (host may not be a CA): $($_.Exception.Message)" -ForegroundColor DarkYellow
    }

    try {
        $caCfgOut = Join-Path $dirs.ADCS "CA_Config.txt"
        certutil.exe -getreg CA > $caCfgOut 2>$null
        if (Test-Path $caCfgOut) { Add-ToManifest $caCfgOut }
    } catch { }
}

# -------------------------------------------------------------------------
# 5. IIS logs (default site + any custom site such as portal.<domain>)
# -------------------------------------------------------------------------
Write-Section "Collecting IIS logs"

$iisLogRoot = "$env:SystemDrive\inetpub\logs\LogFiles"
if (Test-Path $iisLogRoot) {
    try {
        Copy-Item -Path $iisLogRoot -Destination $dirs.IIS -Recurse -Force -ErrorAction Stop
        Get-ChildItem -Path $dirs.IIS -Recurse -File | ForEach-Object { Add-ToManifest $_.FullName }
        Write-Host "  [ok] Copied IIS logs from $iisLogRoot"
    } catch {
        Write-Warning "IIS log copy failed: $_"
    }
} else {
    Write-Host "  [skip] No IIS log directory found at $iisLogRoot" -ForegroundColor DarkYellow
}

# -------------------------------------------------------------------------
# 6. MDT deployment share configuration (read-only copy — do NOT modify source)
# -------------------------------------------------------------------------
Write-Section "Collecting MDT deployment configuration (if present)"

$mdtCandidates = @(
    "\\$env:COMPUTERNAME\DeploymentShare$\Control\CustomSettings.ini",
    "\\$env:COMPUTERNAME\DeploymentShare$\Control\Bootstrap.ini",
    "D:\DeploymentShare\Control\CustomSettings.ini",
    "D:\DeploymentShare\Control\Bootstrap.ini"
)
foreach ($path in $mdtCandidates) {
    if (Test-Path $path) {
        $dest = Join-Path $dirs.MDT (Split-Path $path -Leaf)
        try {
            Copy-Item -Path $path -Destination $dest -Force
            Add-ToManifest $dest
            Write-Host "  [ok] Copied $path"
        } catch {
            Write-Warning "Could not copy $path : $_"
        }
    }
}

# -------------------------------------------------------------------------
# 7. Finalize manifest and package
# -------------------------------------------------------------------------
Write-Section "Finalizing"

$manifest | Export-Csv -Path $manifestPath -NoTypeInformation -Encoding UTF8
Write-Host "Manifest written to $manifestPath ($($manifest.Count) files hashed)"

Stop-Transcript | Out-Null
Add-ToManifest $transcriptPath

if (-not $SkipZip) {
    $zipPath = "$caseDir.zip"
    try {
        Compress-Archive -Path $caseDir -DestinationPath $zipPath -Force
        $zipHash = Get-FileHash -Path $zipPath -Algorithm SHA256
        Write-Host "`nPackaged evidence: $zipPath" -ForegroundColor Green
        Write-Host "Archive SHA256: $($zipHash.Hash)" -ForegroundColor Green
    } catch {
        Write-Warning "Zip packaging failed, evidence remains at $caseDir : $_"
    }
}

Write-Host "`nDone. Evidence collected under: $caseDir" -ForegroundColor Green
