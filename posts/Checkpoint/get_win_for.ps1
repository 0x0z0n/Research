<#
.SYNOPSIS
    FULL AD / DOMAIN COMPROMISE FORENSIC COLLECTOR
.DESCRIPTION
    Collects endpoint + AD + share + credential + persistence + execution evidence.
    Designed for post-exploitation / CTF forensic reconstruction.
.NOTES
    Run as Administrator on DC or compromised domain host.
#>

# =========================
# CONFIG
# =========================
$Port = 8080
$Hostname = $env:COMPUTERNAME
$Timestamp = Get-Date -Format "yyyyMMdd_HHmm"

$BaseDir = "C:\Windows\Temp\Forensics_$Timestamp"
$EvidenceDir = "$BaseDir\Evidence"
$FinalZip = "Forensics_$Hostname_$Timestamp.zip"
$FinalPath = "C:\Windows\Temp\$FinalZip"

# Evidence folders
$ADDir = "$EvidenceDir\AD"
$ShareDir = "$EvidenceDir\Shares"
$ExecDir = "$EvidenceDir\Execution"
$CredDir = "$EvidenceDir\Credentials"
$PersDir = "$EvidenceDir\Persistence"
$LogDir = "$EvidenceDir\Logs"
$MemDir = "$EvidenceDir\Memory"

# =========================
# CLEANUP
# =========================
function Cleanup {
    Write-Host "[*] Cleaning staging..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $BaseDir
}

# =========================
# INIT
# =========================
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " FULL DOMAIN FORENSICS COLLECTOR " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Run as Administrator"
    exit
}

New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
New-Item -ItemType Directory -Force -Path $ADDir,$ShareDir,$ExecDir,$CredDir,$PersDir,$LogDir,$MemDir | Out-Null

# =========================
# SYSTEM STATE
# =========================
Write-Host "[+] System state collection..." -ForegroundColor Green

Get-Process | Select Id,ProcessName,Path,StartTime | Out-File "$ExecDir\processes.txt"
Get-NetTCPConnection | Out-File "$ExecDir\network.txt"
Get-LocalUser | Out-File "$ExecDir\local_users.txt"

# Command history (important CTF artifact)
$history = "$env:APPDATA\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt"
if (Test-Path $history) {
    Copy-Item $history "$ExecDir\ps_history.txt" -Force
}

# =========================
# AD / DOMAIN EVIDENCE (CRITICAL)
# =========================
Write-Host "[+] AD forensic collection..." -ForegroundColor Magenta

try {
    Import-Module ActiveDirectory -ErrorAction SilentlyContinue

    Get-ADUser -Filter * -Properties * | Out-File "$ADDir\ad_users.txt"
    Get-ADComputer -Filter * -Properties * | Out-File "$ADDir\ad_computers.txt"
    Get-ADGroup -Filter * | Out-File "$ADDir\ad_groups.txt"
} catch {}

# Deleted objects / recycle bin (Step 1–2)
try {
    Get-ADObject -IncludeDeletedObjects -Filter * | Out-File "$ADDir\deleted_objects.txt"
} catch {}

# Domain role check
$role = (Get-CimInstance Win32_ComputerSystem).DomainRole
"DomainRole: $role" | Out-File "$ADDir\domain_role.txt"

# =========================
# DC CRITICAL ARTIFACTS
# =========================
if ($role -ge 4) {

    Write-Host "[+] Domain Controller artifacts..." -ForegroundColor Magenta

    cmd /c "repadmin /showrepl" > "$ADDir\replication.txt" 2>&1
    cmd /c "dcdiag /q" > "$ADDir\dcdiag.txt" 2>&1
    cmd /c "netdom query fsmo" > "$ADDir\fsmo.txt" 2>&1

    # SYSVOL (scripts / creds)
    if (Test-Path "C:\Windows\SYSVOL\domain\scripts") {
        Copy-Item "C:\Windows\SYSVOL\domain\scripts" "$ADDir\SYSVOL_Scripts" -Recurse -Force
    }

    # NTDS / SAM / SYSTEM (CRITICAL for hashes)
    $ntds = "C:\Windows\NTDS\ntds.dit"
    $system = "C:\Windows\System32\config\SYSTEM"
    $sam = "C:\Windows\System32\config\SAM"
    $security = "C:\Windows\System32\config\SECURITY"

    foreach ($f in @($ntds,$system,$sam,$security)) {
        if (Test-Path $f) {
            Copy-Item $f $ADDir -Force
        }
    }
}

# =========================
# SHARE ABUSE / LATERAL MOVEMENT
# =========================
Write-Host "[+] Share & lateral movement evidence..." -ForegroundColor Green

cmd /c "net share" > "$ShareDir\net_share.txt" 2>&1
cmd /c "net use" > "$ShareDir\net_use.txt" 2>&1

try {
    Get-SmbShare | Out-File "$ShareDir\smb_shares.txt"
    Get-SmbSession | Out-File "$ShareDir\smb_sessions.txt"
    Get-SmbOpenFile | Out-File "$ShareDir\smb_open_files.txt"
} catch {}

# =========================
# EXECUTION TRACE (STEP 6 / 8 / 10)
# =========================
Write-Host "[+] Execution artifacts..." -ForegroundColor Green

Get-WmiObject Win32_Process |
Select Name,ProcessId,ParentProcessId,CommandLine |
Out-File "$ExecDir\process_cmdline.txt"

# Event logs (attack timeline)
$logs = @(
"Security",
"System",
"Application",
"Microsoft-Windows-PowerShell/Operational",
"Microsoft-Windows-TerminalServices-LocalSessionManager/Operational",
"Microsoft-Windows-WinRM/Operational"
)

foreach ($log in $logs) {
    wevtutil epl "$log" "$LogDir\$($log -replace '/','_').evtx" /ow:true 2>$null
}

# =========================
# CREDENTIAL & KERBEROS ARTIFACTS
# =========================
Write-Host "[+] Credential artifacts..." -ForegroundColor Yellow

cmd /c "klist" > "$CredDir\kerberos_cache.txt" 2>&1

# LSASS dump indicator (no dumping, just metadata)
tasklist /svc | Out-File "$CredDir\tasklist.txt"

# =========================
# PERSISTENCE
# =========================
Write-Host "[+] Persistence artifacts..." -ForegroundColor Yellow

Get-ScheduledTask | Out-File "$PersDir\schtasks.txt"
Get-CimInstance Win32_StartupCommand | Out-File "$PersDir\startup.txt"

# =========================
# MEMORY / FORENSICS ARTIFACTS
# =========================
Write-Host "[+] Memory artifacts..." -ForegroundColor Yellow

$memPaths = @(
"C:\Windows\MEMORY.DMP",
"C:\Windows\Minidump",
"C:\pagefile.sys",
"C:\hiberfil.sys"
)

foreach ($m in $memPaths) {
    if (Test-Path $m) {
        Copy-Item $m $MemDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# =========================
# SUPPLY CHAIN / DEVDROP STYLE ABUSE
# =========================
Write-Host "[+] Searching for payload artifacts..." -ForegroundColor Green

Get-ChildItem C:\ -Recurse -ErrorAction SilentlyContinue |
Where-Object { $_.Name -match "vsix|dll|ps1|zip|exe" } |
Select FullName |
Out-File "$ShareDir\suspicious_files.txt"

# =========================
# COMPRESS
# =========================
Write-Host "[+] Compressing evidence..." -ForegroundColor Cyan

Compress-Archive -Path "$EvidenceDir\*" -DestinationPath $FinalPath -Force

# =========================
# SERVE
# =========================
$IP = (Get-NetIPAddress -AddressFamily IPv4 |
Where-Object { $_.InterfaceAlias -notlike "*Loopback*" } |
Select-Object -First 1).IPAddress

if (-not $IP) { $IP = "127.0.0.1" }

Write-Host "=============================================" -ForegroundColor Yellow
Write-Host " DOWNLOAD: http://$IP:$Port/$FinalZip " -ForegroundColor Yellow
Write-Host "=============================================" -ForegroundColor Yellow

Set-Location "C:\Windows\Temp"

if (Get-Command python -ErrorAction SilentlyContinue) {
    python -m http.server $Port
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    python3 -m http.server $Port
}

# =========================
# CLEANUP
# =========================
Cleanup
