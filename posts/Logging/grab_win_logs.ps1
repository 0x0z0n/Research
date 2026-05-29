<#
.SYNOPSIS
    Windows & Domain Controller Forensic Triage Collector (v1.1 - WMI Fallback)
#>

$Port = 8080
$Hostname = $env:COMPUTERNAME
$Timestamp = Get-Date -Format "yyyyMMdd_HHmm"
$ExportDir = "C:\Windows\Temp\ForensicTriage_$Timestamp"
$ArchiveName = "Triage_$Hostname_$Timestamp.zip"
$FinalPath = Join-Path -Path "C:\Windows\Temp" -ChildPath $ArchiveName

function Remove-Staging {
    if (Test-Path $ExportDir) {
        Remove-Item -Path $ExportDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "   WINDOWS & DC FORENSIC TRIAGE COLLECTOR    " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. Admin Check
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $IsAdmin) { Write-Error "Admin required."; exit }

Try {
    $DomainRole = (Get-CimInstance Win32_ComputerSystem).DomainRole
    $IsDC = ($DomainRole -ge 4)

    # 3. Prepare Staging
    New-Item -ItemType Directory -Force -Path $ExportDir | Out-Null
    $SysInfoDir = New-Item -ItemType Directory -Force -Path "$ExportDir\System_Info"
    $LogsDir = New-Item -ItemType Directory -Force -Path "$ExportDir\Logs"
    $RegDir = New-Item -ItemType Directory -Force -Path "$ExportDir\Registry"
    $ArtifactsDir = New-Item -ItemType Directory -Force -Path "$ExportDir\Artifacts"

    # 4. Volatile Data (Using WMI for maximum compatibility)
    Write-Host "[+] Collecting Volatile System State..." -ForegroundColor Green
    
    Get-NetTCPConnection | Select-Object LocalAddress,LocalPort,RemoteAddress,RemotePort,State,OwningProcess | Export-Csv "$SysInfoDir\Network.csv" -NoTypeInformation
    Get-Process | Select-Object Id,ProcessName,Path,StartTime,User | Export-Csv "$SysInfoDir\Processes.csv" -NoTypeInformation
    
    # FIX: Using Get-CimInstance instead of Get-LocalUser for compatibility
    Get-CimInstance -ClassName Win32_UserAccount | Select-Object Name,Caption,Disabled,PasswordRequired,SID | Export-Csv "$SysInfoDir\Users_WMI.csv" -NoTypeInformation
    
    Get-Service | Select-Object Name,DisplayName,Status,StartType | Export-Csv "$SysInfoDir\Services.csv" -NoTypeInformation
    
    ipconfig /displaydns > "$SysInfoDir\DNS_Cache.txt"
    arp -a > "$SysInfoDir\ARP_Cache.txt"
    route print > "$SysInfoDir\Routing_Table.txt"

    # 5. Registry Hives
    Write-Host "[+] Saving Registry Hives..." -ForegroundColor Green
    reg save HKLM\SYSTEM "$RegDir\SYSTEM.hive" /y | Out-Null
    reg save HKLM\SAM "$RegDir\SAM.hive" /y | Out-Null
    reg save HKLM\SECURITY "$RegDir\SECURITY.hive" /y | Out-Null

    # 6. Forensic Artifacts
    Write-Host "[+] Collecting Execution & User Artifacts..." -ForegroundColor Green
    if (Test-Path "C:\Windows\Prefetch") {
        $PfDir = New-Item -ItemType Directory -Force -Path "$ArtifactsDir\Prefetch"
        Copy-Item -Path "C:\Windows\Prefetch\*.pf" -Destination $PfDir -ErrorAction SilentlyContinue
    }

    $UsersDir = "C:\Users"
    $PSHistDir = New-Item -ItemType Directory -Force -Path "$ArtifactsDir\PS_History"
    Get-ChildItem -Path $UsersDir -Directory | ForEach-Object {
        $HistoryPath = "$($_.FullName)\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt"
        if (Test-Path $HistoryPath) {
            Copy-Item -Path $HistoryPath -Destination "$PSHistDir\$($_.Name)_ConsoleHost_history.txt" -ErrorAction SilentlyContinue
        }
    }

    # 7. Domain Controller Specific
    if ($IsDC) {
        Write-Host "[+] Collecting DC-Specific Artifacts..." -ForegroundColor Magenta
        $DCDir = New-Item -ItemType Directory -Force -Path "$ExportDir\DC_Artifacts"
        cmd /c "repadmin /showrepl" > "$DCDir\repadmin_showrepl.txt" 2>&1
        cmd /c "dcdiag /q" > "$DCDir\dcdiag_quiet.txt" 2>&1
        cmd /c "netdom query fsmo" > "$DCDir\fsmo_roles.txt" 2>&1
    }

    # 8. Event Logs
    Write-Host "[+] Sweeping Event Logs..." -ForegroundColor Green
    $TargetLogs = @("System", "Security", "Application", "Microsoft-Windows-PowerShell/Operational")
    foreach ($LogName in $TargetLogs) {
        $Dest = "$LogsDir\$($LogName -replace '[/ ]','_').evtx"
        wevtutil epl "$LogName" "$Dest" /ow:true
    }

    # 10. Compression
    Write-Host "[+] Compressing forensic artifacts..." -ForegroundColor Green
    Compress-Archive -Path "$ExportDir\*" -DestinationPath $FinalPath -Force
    Write-Host "[+] Archive created at: $FinalPath" -ForegroundColor Cyan

    # 11. Serving
    $IP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.InterfaceAlias -notlike "*vEthernet*" } | Select-Object -First 1).IPAddress
    Write-Host "`nDOWNLOAD LINK: http://$($IP):$Port/$ArchiveName" -ForegroundColor Yellow
    
    Set-Location "C:\Windows\Temp"
    python -m http.server $Port

} Catch {
    Write-Error "Critical Error: $($_.Exception.Message)"
} Finally {
    Remove-Staging
}