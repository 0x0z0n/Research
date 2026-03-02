<#
.SYNOPSIS
    Windows & Domain Controller Log Collector (Optimized)
.DESCRIPTION
    General purpose collector. Detects if host is a DC and expands scope 
    to include AD Logs, Sysvol scripts, and Replication status.
    Features native .NET compression and a standalone PowerShell HTTP listener.
.NOTES
    Run as Administrator.
#>

# --- Configuration ---
$Port = 8080
$Hostname = $env:COMPUTERNAME
$Timestamp = Get-Date -Format "yyyyMMdd_HHmm"
$BaseDir = $env:TEMP
$ExportDir = Join-Path -Path $BaseDir -ChildPath "LogExport_$Timestamp"
$ArchiveName = "Loot_$Hostname_$Timestamp.zip"
$FinalPath = Join-Path -Path $BaseDir -ChildPath $ArchiveName

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
Write-Host "   WINDOWS & DC LOG COLLECTOR (OPTIMIZED)   " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. Admin Check
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $IsAdmin) {
    Write-Error "This script requires Administrator privileges. Exiting."
    exit
}

Try {
    # Load .NET Assembly for faster compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem

    # 2. DC Detection
    $DomainRole = (Get-CimInstance Win32_ComputerSystem -ErrorAction Stop).DomainRole
    $IsDC = ($DomainRole -ge 4)

    if ($IsDC) {
        Write-Host "[*] DOMAIN CONTROLLER DETECTED! (Role: $DomainRole)" -ForegroundColor Magenta
        Write-Host "    -> Engaging Extended Collection Scope." -ForegroundColor Magenta
    } else {
        Write-Host "[*] Standard Workstation/Server detected." -ForegroundColor Cyan
    }

    # 3. Prepare Staging
    $null = New-Item -ItemType Directory -Force -Path $ExportDir -ErrorAction Stop
    $SysInfoDir = New-Item -ItemType Directory -Force -Path "$ExportDir\System_Info"
    $LogsDir = New-Item -ItemType Directory -Force -Path "$ExportDir\Logs"

    # 4. Volatile Data (General)
    Write-Host "[+] Collecting System State..." -ForegroundColor Green
    
    Get-NetTCPConnection -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,RemoteAddress,RemotePort,State,OwningProcess | Export-Csv "$SysInfoDir\Network.csv" -NoTypeInformation
    Get-Process -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,Path,StartTime | Export-Csv "$SysInfoDir\Processes.csv" -NoTypeInformation
    Get-LocalUser -ErrorAction SilentlyContinue | Export-Csv "$SysInfoDir\LocalUsers.csv" -NoTypeInformation
    
    Copy-Item "$env:windir\System32\drivers\etc\hosts" -Destination "$SysInfoDir\hosts.txt" -ErrorAction SilentlyContinue

    # 5. Domain Controller Specific Scope
    if ($IsDC) {
        Write-Host "[+] Collecting DC-Specific Artifacts..." -ForegroundColor Magenta
        $DCDir = New-Item -ItemType Directory -Force -Path "$ExportDir\DC_Artifacts"

        Write-Host "    [*] Running DC Diagnostic commands..." -ForegroundColor Yellow
        cmd /c "repadmin /showrepl" > "$DCDir\repadmin_showrepl.txt" 2>&1
        cmd /c "dcdiag /q" > "$DCDir\dcdiag_quiet.txt" 2>&1
        cmd /c "netdom query fsmo" > "$DCDir\fsmo_roles.txt" 2>&1
        cmd /c "nltest /dclist:$env:USERDOMAIN" > "$DCDir\dc_list.txt" 2>&1
        
        if (Test-Path "$env:windir\SYSVOL\domain\scripts") {
            Write-Host "    [*] Copying SYSVOL Scripts..." -ForegroundColor Yellow
            Copy-Item "$env:windir\SYSVOL\domain\scripts" -Destination "$DCDir\Sysvol_Scripts" -Recurse -ErrorAction SilentlyContinue
        }

        Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" -ErrorAction SilentlyContinue | Out-File "$DCDir\NTDS_Registry_Settings.txt"
    }

    # 6. Event Logs (Dynamic Scope)
    Write-Host "[+] Sweeping Event Logs..." -ForegroundColor Green
    
    $TargetLogs = @("System", "Security", "Application", "Microsoft-Windows-PowerShell/Operational")
    if ($IsDC) {
        $TargetLogs += @("Directory Service", "DNS Server", "DFS Replication", "Key Management Service")
    }

    foreach ($LogName in $TargetLogs) {
        $Dest = Join-Path $LogsDir "$($LogName -replace '[/ ]','_').evtx"
        Try {
            wevtutil epl "$LogName" "$Dest" /ow:true
            Write-Host "    [OK] Exported: $LogName" -ForegroundColor Gray
        } Catch {
            Write-Host "    [SKIP] Log not found or locked: $LogName" -ForegroundColor DarkGray
        }
    }

    # 7. Compression (Using Fast .NET Class)
    Write-Host "[+] Compressing artifacts (Fast Mode)..." -ForegroundColor Green
    if (Test-Path $FinalPath) { Remove-Item $FinalPath -Force }
    [System.IO.Compression.ZipFile]::CreateFromDirectory($ExportDir, $FinalPath)
    Write-Host "[+] Archive created at: $FinalPath" -ForegroundColor Cyan

    # 8. Serving (Native PowerShell HTTP Server)
    $IP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.InterfaceAlias -notlike "*vEthernet*" } | Select-Object -First 1).IPAddress
    if (-not $IP) { $IP = "127.0.0.1" }

    Write-Host "`n====================================================" -ForegroundColor Yellow
    Write-Host " DOWNLOAD LINK: http://$($IP):$($Port)/$ArchiveName" -ForegroundColor Yellow
    Write-Host " Waiting for 1 download connection. Press CTRL+C to abort." -ForegroundColor Yellow
    Write-Host "====================================================" -ForegroundColor Yellow

    # Standalone PowerShell Web Listener (No Python required)
    $Listener = New-Object System.Net.HttpListener
    $Listener.Prefixes.Add("http://+:$Port/")
    $Listener.Start()

    Try {
        $Context = $Listener.GetContext()
        $Response = $Context.Response
        
        Write-Host "[*] Connection received from $($Context.Request.RemoteEndPoint.Address)..." -ForegroundColor Cyan
        
        $FileBytes = [System.IO.File]::ReadAllBytes($FinalPath)
        $Response.ContentType = "application/zip"
        $Response.ContentLength64 = $FileBytes.Length
        $Response.AddHeader("Content-Disposition", "attachment; filename=$ArchiveName")
        
        $OutputStream = $Response.OutputStream
        $OutputStream.Write($FileBytes, 0, $FileBytes.Length)
        $OutputStream.Close()
        
        Write-Host "[+] File successfully transferred!" -ForegroundColor Green
    } Finally {
        $Listener.Stop()
    }

} Catch {
    Write-Error "Critical Error: $($_.Exception.Message)"
} Finally {
    Remove-Staging
}