<#
.SYNOPSIS
    DarkZeroReturns / HTB Windows forensic evidence collector.

.DESCRIPTION
    Collects volatile and non-volatile Windows forensic evidence relevant to:
      - Active Directory authentication
      - Kerberos activity
      - LDAP/account/group changes
      - WinRM
      - PowerShell execution
      - Process creation
      - Service/task persistence
      - Network configuration/connections
      - Windows Security/System/Application logs
      - Sysmon logs
      - Registry-based forensic artifacts
      - Prefetch / Amcache / SRUM where accessible
      - Recent PowerShell history
      - Scheduled tasks
      - Services
      - Local users/groups
      - AD-related Windows event logs

    The script is intended to be READ-ONLY with respect to the host.
    It does not clear logs, delete artifacts, or modify configuration.

.NOTES
    Run from an elevated PowerShell console.

    Example:
        .\Collect-DarkZeroEvidence.ps1

    Optional:
        .\Collect-DarkZeroEvidence.ps1 -OutputRoot D:\Evidence

#>

[CmdletBinding()]
param(
    [string]$OutputRoot = "C:\Forensics"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "SilentlyContinue"

# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

$StartTime = Get-Date
$HostName  = $env:COMPUTERNAME
$Timestamp = $StartTime.ToUniversalTime().ToString("yyyyMMdd_HHmmssZ")

$EvidenceRoot = Join-Path $OutputRoot "${HostName}_${Timestamp}"

$Directories = @(
    "00_Metadata",
    "01_Volatile",
    "02_EventLogs",
    "03_Security",
    "04_Sysmon",
    "05_PowerShell",
    "06_Processes",
    "07_Network",
    "08_Users_Groups",
    "09_Services",
    "10_ScheduledTasks",
    "11_Registry",
    "12_FileSystem",
    "13_AD",
    "14_WinRM",
    "15_Persistence",
    "16_Hashes"
)

New-Item -ItemType Directory -Path $EvidenceRoot -Force | Out-Null

foreach ($Dir in $Directories) {
    New-Item -ItemType Directory `
        -Path (Join-Path $EvidenceRoot $Dir) `
        -Force | Out-Null
}

$LogFile = Join-Path $EvidenceRoot "00_Metadata\Collection.log"

function Write-CollectionLog {
    param(
        [string]$Message
    )

    $Line = "[{0}] {1}" -f `
        (Get-Date).ToUniversalTime().ToString("yyyy-MM-dd HH:mm:ss.fffZ"),
        $Message

    $Line | Tee-Object -FilePath $LogFile -Append
}

function Export-Text {
    param(
        [Parameter(Mandatory)]
        [string]$Name,

        [Parameter(Mandatory)]
        [scriptblock]$Command
    )

    try {
        Write-CollectionLog "Collecting $Name"

        & $Command |
            Out-File -FilePath $Name `
                     -Encoding UTF8 `
                     -Width 4096

    }
    catch {
        "ERROR: $($_.Exception.Message)" |
            Out-File -FilePath $Name `
                     -Encoding UTF8
    }
}

function Export-CsvSafe {
    param(
        [Parameter(Mandatory)]
        [string]$Name,

        [Parameter(Mandatory)]
        [scriptblock]$Command
    )

    try {
        Write-CollectionLog "Collecting $Name"

        & $Command |
            Export-Csv -Path $Name `
                       -NoTypeInformation `
                       -Encoding UTF8

    }
    catch {
        "ERROR: $($_.Exception.Message)" |
            Out-File -FilePath $Name `
                     -Encoding UTF8
    }
}

function Copy-IfExists {
    param(
        [string]$Source,
        [string]$Destination
    )

    if (Test-Path $Source) {
        try {
            Copy-Item $Source $Destination -Force -ErrorAction Stop
            Write-CollectionLog "Copied $Source"
        }
        catch {
            Write-CollectionLog "FAILED copying $Source : $($_.Exception.Message)"
        }
    }
}

# ---------------------------------------------------------------------------
# 00 - Collection metadata
# ---------------------------------------------------------------------------

Write-CollectionLog "========== COLLECTION START =========="
Write-CollectionLog "Host: $HostName"
Write-CollectionLog "Start UTC: $($StartTime.ToUniversalTime().ToString("o"))"

Export-Text `
    (Join-Path $EvidenceRoot "00_Metadata\systeminfo.txt") `
    { systeminfo.exe }

Export-Text `
    (Join-Path $EvidenceRoot "00_Metadata\hostname.txt") `
    { hostname.exe }

Export-Text `
    (Join-Path $EvidenceRoot "00_Metadata\whoami.txt") `
    { whoami.exe /all }

Export-Text `
    (Join-Path $EvidenceRoot "00_Metadata\windows_version.txt") `
    {
        Get-ComputerInfo |
            Select-Object `
                WindowsProductName,
                WindowsVersion,
                OsBuildNumber,
                OsArchitecture,
                CsName,
                CsDomain,
                CsDomainRole,
                CsManufacturer,
                CsModel,
                BiosVersion,
                TimeZone |
            Format-List
    }

Export-Text `
    (Join-Path $EvidenceRoot "00_Metadata\time.txt") `
    {
        Get-Date
        Get-Date -AsUTC
        w32tm.exe /query /status
        w32tm.exe /query /configuration
    }

# ---------------------------------------------------------------------------
# 01 - Volatile evidence
# ---------------------------------------------------------------------------

Write-CollectionLog "========== VOLATILE EVIDENCE =========="

Export-CsvSafe `
    (Join-Path $EvidenceRoot "01_Volatile\processes.csv") `
    {
        Get-CimInstance Win32_Process |
            Select-Object `
                ProcessId,
                ParentProcessId,
                Name,
                ExecutablePath,
                CommandLine,
                CreationDate,
                SessionId
    }

Export-CsvSafe `
    (Join-Path $EvidenceRoot "01_Volatile\services.csv") `
    {
        Get-CimInstance Win32_Service |
            Select-Object `
                Name,
                DisplayName,
                State,
                StartMode,
                StartName,
                PathName,
                ProcessId
    }

Export-Text `
    (Join-Path $EvidenceRoot "01_Volatile\netstat.txt") `
    {
        netstat.exe -ano
    }

Export-Text `
    (Join-Path $EvidenceRoot "01_Volatile\arp.txt") `
    {
        arp.exe -a
    }

Export-Text `
    (Join-Path $EvidenceRoot "01_Volatile\routing.txt") `
    {
        route.exe print
    }

Export-Text `
    (Join-Path $EvidenceRoot "01_Volatile\ipconfig.txt") `
    {
        ipconfig.exe /all
    }

Export-Text `
    (Join-Path $EvidenceRoot "01_Volatile\dns.txt") `
    {
        ipconfig.exe /displaydns
    }

Export-CsvSafe `
    (Join-Path $EvidenceRoot "01_Volatile\tcp_connections.csv") `
    {
        Get-NetTCPConnection |
            Select-Object `
                LocalAddress,
                LocalPort,
                RemoteAddress,
                RemotePort,
                State,
                OwningProcess,
                CreationTime
    }

Export-CsvSafe `
    (Join-Path $EvidenceRoot "01_Volatile\udp_endpoints.csv") `
    {
        Get-NetUDPEndpoint |
            Select-Object `
                LocalAddress,
                LocalPort,
                OwningProcess
    }

# ---------------------------------------------------------------------------
# 02 - Windows Event Logs
# ---------------------------------------------------------------------------

Write-CollectionLog "========== EVENT LOG COLLECTION =========="

$EventLogs = @(
    "System",
    "Application",
    "Security",
    "Windows PowerShell"
)

foreach ($Log in $EventLogs) {

    $SafeName = $Log -replace '[\\/:*?"<>| ]','_'

    Export-Text `
        (Join-Path $EvidenceRoot "02_EventLogs\${SafeName}_metadata.txt") `
        {
            Get-WinEvent -ListLog $Log |
                Format-List *
        }

    try {
        wevtutil.exe epl `
            "$Log" `
            (Join-Path $EvidenceRoot "02_EventLogs\${SafeName}.evtx")

        Write-CollectionLog "Exported $Log"
    }
    catch {
        Write-CollectionLog "FAILED exporting $Log"
    }
}

# ---------------------------------------------------------------------------
# 03 - Security-specific event extraction
# ---------------------------------------------------------------------------

Write-CollectionLog "========== SECURITY EVENTS =========="

$SecurityEvents = @(
    4624, # Successful logon
    4625, # Failed logon
    4634, # Logoff
    4647, # User initiated logoff
    4648, # Explicit credential use
    4672, # Special privileges assigned
    4673, # Privileged service called
    4674, # Privileged operation
    4688, # Process creation
    4697, # Service installed
    4698, # Scheduled task created
    4699, # Scheduled task deleted
    4700, # Scheduled task enabled
    4701, # Scheduled task disabled
    4702, # Scheduled task updated
    4720, # User created
    4722, # User enabled
    4723, # Password change attempt
    4724, # Password reset
    4725, # User disabled
    4726, # User deleted
    4728, # Member added to security-enabled global group
    4732, # Member added to local group
    4735, # Security-enabled local group changed
    4738, # User account changed
    4740, # Account locked out
    4756, # Member added to universal group
    4768, # Kerberos TGT request
    4769, # Kerberos service ticket
    4770, # Kerberos service ticket renewed
    4771, # Kerberos pre-authentication failed
    4776, # NTLM authentication
    5140, # SMB share accessed
    5145, # Detailed SMB share access
    5156, # Windows Filtering Platform connection
    5157, # Windows Filtering Platform blocked
    7045  # Service installation
)

$SecurityCsv = Join-Path `
    $EvidenceRoot `
    "03_Security\Security_SelectedEvents.csv"

try {

    Get-WinEvent -FilterHashtable @{
        LogName = "Security"
        Id      = $SecurityEvents
    } -ErrorAction Stop |
    ForEach-Object {

        [PSCustomObject]@{
            TimeCreated = $_.TimeCreated
            Id          = $_.Id
            Provider    = $_.ProviderName
            RecordId    = $_.RecordId
            MachineName = $_.MachineName
            Level       = $_.LevelDisplayName
            Message     = $_.Message
        }

    } |
    Export-Csv $SecurityCsv `
        -NoTypeInformation `
        -Encoding UTF8

}
catch {
    Write-CollectionLog "Security event extraction failed: $($_.Exception.Message)"
}

# ---------------------------------------------------------------------------
# 04 - Sysmon
# ---------------------------------------------------------------------------

Write-CollectionLog "========== SYSMON =========="

$SysmonLog = "Microsoft-Windows-Sysmon/Operational"

if (Get-WinEvent -ListLog $SysmonLog) {

    wevtutil.exe epl `
        $SysmonLog `
        (Join-Path $EvidenceRoot "04_Sysmon\Sysmon-Operational.evtx")

    Export-Text `
        (Join-Path $EvidenceRoot "04_Sysmon\Sysmon_metadata.txt") `
        {
            Get-WinEvent -ListLog $SysmonLog |
                Format-List *
        }

    $SysmonEvents = @(
        1,   # Process Create
        2,   # File creation time changed
        3,   # Network connection
        5,   # Process terminated
        6,   # Driver loaded
        7,   # Image loaded
        8,   # CreateRemoteThread
        10,  # Process access
        11,  # FileCreate
        12,  # Registry create/delete
        13,  # Registry value set
        14,  # Registry rename
        15,  # FileCreateStreamHash
        17,  # Named pipe created
        18,  # Named pipe connected
        22,  # DNS query
        23,  # File deletion
        25,  # Process tampering
        26,  # File deletion detected
        27,  # File block executable
        28,  # File block shimming
        29,  # File executable detected
        32,  # Windows Defender detection
        33,  # DNS query
        34,  # Clipboard
        35,  # Clipboard
        36,  # DNS query
        37   # Pipe event
    )

    try {

        Get-WinEvent -FilterHashtable @{
            LogName = $SysmonLog
            Id      = $SysmonEvents
        } |
        ForEach-Object {

            [PSCustomObject]@{
                TimeCreated = $_.TimeCreated
                EventID     = $_.Id
                RecordId    = $_.RecordId
                Computer    = $_.MachineName
                Provider    = $_.ProviderName
                Message     = $_.Message
            }

        } |
        Export-Csv `
            (Join-Path $EvidenceRoot "04_Sysmon\Sysmon_SelectedEvents.csv") `
            -NoTypeInformation `
            -Encoding UTF8
    }
    catch {
        Write-CollectionLog "Sysmon extraction failed"
    }
}
else {
    Write-CollectionLog "Sysmon Operational log not present"
}

# ---------------------------------------------------------------------------
# 05 - PowerShell
# ---------------------------------------------------------------------------

Write-CollectionLog "========== POWERSHELL =========="

$PSLogs = @(
    "Microsoft-Windows-PowerShell/Operational",
    "Microsoft-Windows-PowerShell-ISE/Operational"
)

foreach ($Log in $PSLogs) {

    if (Get-WinEvent -ListLog $Log) {

        $SafeName = $Log -replace '[\\/:*?"<>| ]','_'

        wevtutil.exe epl `
            $Log `
            (Join-Path $EvidenceRoot "05_PowerShell\${SafeName}.evtx")
    }
}

# PowerShell history for all local profiles
$ProfileDirs = Get-ChildItem `
    "C:\Users" `
    -Directory `
    -Force `
    -ErrorAction SilentlyContinue

foreach ($Profile in $ProfileDirs) {

    $History = Join-Path `
        $Profile.FullName `
        "AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt"

    if (Test-Path $History) {

        $Destination = Join-Path `
            $EvidenceRoot `
            "05_PowerShell\$($Profile.Name)_ConsoleHost_history.txt"

        Copy-IfExists $History $Destination
    }
}

# ---------------------------------------------------------------------------
# 06 - Process evidence
# ---------------------------------------------------------------------------

Write-CollectionLog "========== PROCESS EVIDENCE =========="

Export-CsvSafe `
    (Join-Path $EvidenceRoot "06_Processes\Win32_Process.csv") `
    {
        Get-CimInstance Win32_Process |
            Select-Object `
                Name,
                ProcessId,
                ParentProcessId,
                ExecutablePath,
                CommandLine,
                CreationDate,
                SessionId
    }

Export-Text `
    (Join-Path $EvidenceRoot "06_Processes\process_tree.txt") `
    {
        Get-CimInstance Win32_Process |
            Sort-Object ParentProcessId |
            Format-Table `
                ProcessId,
                ParentProcessId,
                Name,
                CommandLine `
                -AutoSize -Wrap
    }

# ---------------------------------------------------------------------------
# 07 - Network
# ---------------------------------------------------------------------------

Write-CollectionLog "========== NETWORK =========="

Export-Text `
    (Join-Path $EvidenceRoot "07_Network\netsh_interfaces.txt") `
    {
        netsh.exe interface show interface
    }

Export-Text `
    (Join-Path $EvidenceRoot "07_Network\netsh_ipconfig.txt") `
    {
        netsh.exe interface ip show config
    }

Export-Text `
    (Join-Path $EvidenceRoot "07_Network\firewall.txt") `
    {
        netsh.exe advfirewall show allprofiles
    }

Export-CsvSafe `
    (Join-Path $EvidenceRoot "07_Network\network_adapters.csv") `
    {
        Get-NetAdapter |
            Select-Object *
    }

Export-CsvSafe `
    (Join-Path $EvidenceRoot "07_Network\firewall_rules.csv") `
    {
        Get-NetFirewallRule |
            Select-Object `
                Name,
                DisplayName,
                Enabled,
                Direction,
                Action,
                Profile
    }

# ---------------------------------------------------------------------------
# 08 - Users and Groups
# ---------------------------------------------------------------------------

Write-CollectionLog "========== USERS / GROUPS =========="

Export-CsvSafe `
    (Join-Path $EvidenceRoot "08_Users_Groups\local_users.csv") `
    {
        Get-LocalUser |
            Select-Object *
    }

Export-CsvSafe `
    (Join-Path $EvidenceRoot "08_Users_Groups\local_groups.csv") `
    {
        Get-LocalGroup |
            Select-Object *
    }

Export-Text `
    (Join-Path $EvidenceRoot "08_Users_Groups\whoami_all.txt") `
    {
        whoami.exe /all
    }

Export-Text `
    (Join-Path $EvidenceRoot "08_Users_Groups\domain.txt") `
    {
        Get-CimInstance Win32_ComputerSystem |
            Select-Object Name, Domain, PartOfDomain, DomainRole |
            Format-List
    }

# ---------------------------------------------------------------------------
# 09 - Services
# ---------------------------------------------------------------------------

Write-CollectionLog "========== SERVICES =========="

Export-CsvSafe `
    (Join-Path $EvidenceRoot "09_Services\services.csv") `
    {
        Get-CimInstance Win32_Service |
            Select-Object `
                Name,
                DisplayName,
                State,
                StartMode,
                StartName,
                PathName,
                ProcessId
    }

Export-Text `
    (Join-Path $EvidenceRoot "09_Services\sc_query.txt") `
    {
        sc.exe query type= all state= all
    }

# ---------------------------------------------------------------------------
# 10 - Scheduled Tasks
# ---------------------------------------------------------------------------

Write-CollectionLog "========== SCHEDULED TASKS =========="

Export-CsvSafe `
    (Join-Path $EvidenceRoot "10_ScheduledTasks\tasks.csv") `
    {
        Get-ScheduledTask |
            Select-Object `
                TaskName,
                TaskPath,
                State,
                Author,
                Description
    }

Export-Text `
    (Join-Path $EvidenceRoot "10_ScheduledTasks\schtasks.txt") `
    {
        schtasks.exe /query /fo LIST /v
    }

# ---------------------------------------------------------------------------
# 11 - Registry snapshots / persistence locations
# ---------------------------------------------------------------------------

Write-CollectionLog "========== REGISTRY =========="

$RegistryLocations = @{
    "Run_CurrentUser.txt" =
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"

    "Run_CurrentMachine.txt" =
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run"

    "RunOnce_CurrentUser.txt" =
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce"

    "RunOnce_CurrentMachine.txt" =
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce"
}

foreach ($Item in $RegistryLocations.GetEnumerator()) {

    Export-Text `
        (Join-Path $EvidenceRoot "11_Registry\$($Item.Key)") `
        {
            Get-ItemProperty $Item.Value |
                Format-List *
        }
}

# ---------------------------------------------------------------------------
# 12 - File-system artifacts
# ---------------------------------------------------------------------------

Write-CollectionLog "========== FILESYSTEM ARTIFACTS =========="

# Prefetch
$PrefetchDestination = Join-Path `
    $EvidenceRoot `
    "12_FileSystem\Prefetch"

New-Item `
    -ItemType Directory `
    -Path $PrefetchDestination `
    -Force | Out-Null

if (Test-Path "C:\Windows\Prefetch") {

    Copy-Item `
        "C:\Windows\Prefetch\*" `
        $PrefetchDestination `
        -Force `
        -ErrorAction SilentlyContinue
}

# Amcache
Copy-IfExists `
    "C:\Windows\AppCompat\Programs\Amcache.hve" `
    (Join-Path $EvidenceRoot "12_FileSystem\Amcache.hve")

# SRUM
Copy-IfExists `
    "C:\Windows\System32\sru\SRUDB.dat" `
    (Join-Path $EvidenceRoot "12_FileSystem\SRUDB.dat")

# Recent Windows Defender history
if (Test-Path "C:\ProgramData\Microsoft\Windows Defender") {

    Copy-Item `
        "C:\ProgramData\Microsoft\Windows Defender" `
        (Join-Path $EvidenceRoot "12_FileSystem\WindowsDefender") `
        -Recurse `
        -Force `
        -ErrorAction SilentlyContinue
}

# ---------------------------------------------------------------------------
# 13 - Active Directory evidence
# ---------------------------------------------------------------------------

Write-CollectionLog "========== ACTIVE DIRECTORY =========="

if (Get-Command Get-ADDomain -ErrorAction SilentlyContinue) {

    Export-Text `
        (Join-Path $EvidenceRoot "13_AD\domain.txt") `
        {
            Get-ADDomain | Format-List *
        }

    Export-Text `
        (Join-Path $EvidenceRoot "13_AD\forest.txt") `
        {
            Get-ADForest | Format-List *
        }

    Export-CsvSafe `
        (Join-Path $EvidenceRoot "13_AD\domain_controllers.csv") `
        {
            Get-ADDomainController -Filter * |
                Select-Object *
        }

    Export-CsvSafe `
        (Join-Path $EvidenceRoot "13_AD\users.csv") `
        {
            Get-ADUser -Filter * -Properties * |
                Select-Object `
                    SamAccountName,
                    UserPrincipalName,
                    Enabled,
                    SID,
                    ObjectGUID,
                    DistinguishedName,
                    LastLogonDate,
                    PasswordLastSet,
                    WhenCreated,
                    WhenChanged,
                    ServicePrincipalName
        }

    Export-CsvSafe `
        (Join-Path $EvidenceRoot "13_AD\groups.csv") `
        {
            Get-ADGroup -Filter * -Properties * |
                Select-Object *
        }

    Export-CsvSafe `
        (Join-Path $EvidenceRoot "13_AD\computers.csv") `
        {
            Get-ADComputer -Filter * -Properties * |
                Select-Object `
                    Name,
                    DNSHostName,
                    Enabled,
                    SID,
                    DistinguishedName,
                    OperatingSystem,
                    OperatingSystemVersion,
                    LastLogonDate,
                    WhenCreated,
                    WhenChanged
        }

    Export-CsvSafe `
        (Join-Path $EvidenceRoot "13_AD\trusts.csv") `
        {
            Get-ADTrust -Filter * |
                Select-Object *
        }

    Export-CsvSafe `
        (Join-Path $EvidenceRoot "13_AD\ous.csv") `
        {
            Get-ADOrganizationalUnit -Filter * -Properties * |
                Select-Object *
        }
}
else {

    Write-CollectionLog `
        "ActiveDirectory PowerShell module not installed"

    Export-Text `
        (Join-Path $EvidenceRoot "13_AD\domain_info.txt") `
        {
            nltest.exe /dsgetdc:$env:USERDNSDOMAIN
            nltest.exe /domain_trusts
        }
}

# ---------------------------------------------------------------------------
# 14 - WinRM
# ---------------------------------------------------------------------------

Write-CollectionLog "========== WINRM =========="

Export-Text `
    (Join-Path $EvidenceRoot "14_WinRM\winrm_config.txt") `
    {
        winrm.exe get winrm/config
    }

Export-Text `
    (Join-Path $EvidenceRoot "14_WinRM\winrm_service.txt") `
    {
        Get-Service WinRM |
            Format-List *
    }

# ---------------------------------------------------------------------------
# 15 - Persistence / common suspicious locations
# ---------------------------------------------------------------------------

Write-CollectionLog "========== PERSISTENCE =========="

Export-Text `
    (Join-Path $EvidenceRoot "15_Persistence\startup_locations.txt") `
    {
        Get-ChildItem `
            "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup" `
            -Force |
            Format-List *

        Get-ChildItem `
            "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup" `
            -Force |
            Format-List *
    }

Export-Text `
    (Join-Path $EvidenceRoot "15_Persistence\autoruns_registry.txt") `
    {
        reg.exe query `
            "HKLM\Software\Microsoft\Windows\CurrentVersion\Run"

        reg.exe query `
            "HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce"

        reg.exe query `
            "HKCU\Software\Microsoft\Windows\CurrentVersion\Run"

        reg.exe query `
            "HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce"
    }

# ---------------------------------------------------------------------------
# 16 - Hash everything collected
# ---------------------------------------------------------------------------

Write-CollectionLog "========== HASHING EVIDENCE =========="

$HashFile = Join-Path `
    $EvidenceRoot `
    "16_Hashes\SHA256SUMS.csv"

Get-ChildItem `
    $EvidenceRoot `
    -File `
    -Recurse `
    -Force |
    Where-Object {
        $_.FullName -ne $HashFile
    } |
    Get-FileHash -Algorithm SHA256 |
    Select-Object `
        Algorithm,
        Hash,
        Path |
    Export-Csv `
        $HashFile `
        -NoTypeInformation `
        -Encoding UTF8

# ---------------------------------------------------------------------------
# Final metadata
# ---------------------------------------------------------------------------

$EndTime = Get-Date

[PSCustomObject]@{
    Hostname          = $HostName
    StartTimeUTC      = $StartTime.ToUniversalTime()
    EndTimeUTC        = $EndTime.ToUniversalTime()
    DurationSeconds   = ($EndTime - $StartTime).TotalSeconds
    PowerShellVersion = $PSVersionTable.PSVersion.ToString()
    User              = "$env:USERDOMAIN\$env:USERNAME"
    Is64BitOS         = [Environment]::Is64BitOperatingSystem
    EvidenceDirectory = $EvidenceRoot
    FileCount         = (
        Get-ChildItem $EvidenceRoot -File -Recurse |
        Measure-Object
    ).Count
}

Write-CollectionLog "========== COLLECTION COMPLETE =========="
Write-CollectionLog "Evidence directory: $EvidenceRoot"

Write-Host ""
Write-Host "==============================================="
Write-Host " DarkZeroReturns Evidence Collection Complete"
Write-Host "==============================================="
Write-Host ""
Write-Host "Evidence: $EvidenceRoot"
Write-Host "SHA256:   $(Join-Path $EvidenceRoot '16_Hashes\SHA256SUMS.csv')"
Write-Host ""
