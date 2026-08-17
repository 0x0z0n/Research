<#
.SYNOPSIS
    Collects logs/artifacts mapped to each stage of the attack chain, for
    reconstructing a timeline in a CTF writeup.

.DESCRIPTION
    Run as Administrator (evil-winrm etc). Targets the specific evidence
    trail for:
      anderson.w -> WAC -> SmarterMail/svc_mail -> noah.b -> DPAPI -> alex.o
      -> ForceChangePassword -> jake.h -> AD CS (OID/template/DACL writes)
      -> ESC1 cert request -> PKINIT -> Administrator

.NOTES
    For use on systems you are authorized to assess (e.g. your own HTB/lab
    instance).
#>

param(
    [string]$OutDir = "C:\Windows\Temp\attack_chain_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
)

$ErrorActionPreference = 'SilentlyContinue'
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

function Save($Name, [ScriptBlock]$Block) {
    $path = Join-Path $OutDir "$Name.txt"
    Write-Host "[*] $Name..."
    try { & $Block | Out-File -FilePath $path -Encoding UTF8 -Width 4096 }
    catch { "ERROR: $($_.Exception.Message)" | Out-File -FilePath $path -Encoding UTF8 }
}

# ============================================================
# STAGE 0 - Raw event logs (full .evtx, for offline timeline tools
# like Timeline Explorer / EvtxECmd / Chainsaw)
# ============================================================
$evtxDir = Join-Path $OutDir "evtx"
New-Item -ItemType Directory -Path $evtxDir -Force | Out-Null
$logsToExport = @(
    'Security',
    'System',
    'Application',
    'Windows PowerShell',
    'Microsoft-Windows-PowerShell/Operational',
    'Microsoft-Windows-WinRM/Operational',
    'Microsoft-Windows-TerminalServices-LocalSessionManager/Operational',
    'Microsoft-Windows-TerminalServices-RemoteConnectionManager/Operational',
    'Microsoft-Windows-CAPI2/Operational',              # cert enrollment / crypto ops
    'Microsoft-Windows-CertificateServicesClient-Lifecycle-System/Operational',
    'Microsoft-Windows-CertificateServicesClient-CredentialRoaming/Operational',
    'Microsoft-Windows-Kerberos/Operational',            # PKINIT / TGT requests
    'Directory Service',                                  # AD object creation/modification
    'Microsoft-Windows-ActiveDirectory_DomainService/Operational',
    'Microsoft-Windows-Sysmon/Operational'                # if Sysmon is installed
)
foreach ($log in $logsToExport) {
    $safe = $log -replace '[\\/ ]', '_'
    wevtutil epl $log (Join-Path $evtxDir "$safe.evtx") 2>$null
}

# CA-specific application log (AD CS server role, if this host is the CA)
wevtutil epl "Microsoft-Windows-CertificationAuthority/Operational" (Join-Path $evtxDir "CertificationAuthority.evtx") 2>$null

# ============================================================
# STAGE 1 - anderson.w / WAC authentication + PowerShell RCE
# ============================================================
Save "01_logon_events_4624_4625" {
    Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624,4625} -MaxEvents 1000 |
    Select-Object TimeCreated, Id,
        @{N='Account';E={ ($_.Properties[5]).Value }},
        @{N='LogonType';E={ ($_.Properties[8]).Value }},
        @{N='SourceIP';E={ ($_.Properties[18]).Value }} |
    Sort-Object TimeCreated
}
Save "01_powershell_script_block_log" {
    Get-WinEvent -LogName 'Microsoft-Windows-PowerShell/Operational' -FilterXPath "*[System[(EventID=4104)]]" -MaxEvents 1000 |
    Select-Object TimeCreated, Id, Message | Sort-Object TimeCreated
}
Save "01_wac_iis_logs" {
    Get-ChildItem "C:\inetpub\logs\LogFiles" -Recurse -Filter *.log -EA SilentlyContinue |
    ForEach-Object { "== $($_.FullName) =="; Get-Content $_.FullName }
}

# ============================================================
# STAGE 2 - SmarterMail RCE (svc_mail) — process creation events
# ============================================================
Save "02_process_creation_4688" {
    Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4688} -MaxEvents 2000 |
    Select-Object TimeCreated,
        @{N='NewProcessName';E={ ($_.Properties[5]).Value }},
        @{N='CommandLine';E={ ($_.Properties[8]).Value }},
        @{N='ParentProcessName';E={ ($_.Properties[13]).Value }},
        @{N='SubjectUserName';E={ ($_.Properties[1]).Value }} |
    Sort-Object TimeCreated
}
Save "02_smartermail_logs" {
    Get-ChildItem "C:\SmarterMail" -Recurse -Include *.log,*.txt -EA SilentlyContinue |
    Select-Object FullName, LastWriteTime, Length
}

# ============================================================
# STAGE 3 - noah.b RunasCs logon + DPAPI masterkey/credential access
# ============================================================
Save "03_noahb_logon_events" {
    Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624,4648} -MaxEvents 1000 |
    Where-Object { $_.Message -match 'noah.b' } |
    Select-Object TimeCreated, Id, Message
}
Save "03_dpapi_masterkey_files" {
    Get-ChildItem "C:\Users\*\AppData\Roaming\Microsoft\Protect" -Recurse -Force -EA SilentlyContinue |
    Select-Object FullName, LastWriteTime, Length
}
Save "03_credential_manager_files" {
    Get-ChildItem "C:\Users\*\AppData\Local\Microsoft\Credentials" -Recurse -Force -EA SilentlyContinue |
    Select-Object FullName, LastWriteTime, Length
}
Save "03_capi2_dpapi_events" {
    Get-WinEvent -LogName 'Microsoft-Windows-CAPI2/Operational' -MaxEvents 500 |
    Select-Object TimeCreated, Id, Message
}

# ============================================================
# STAGE 4 - alex.o -> ForceChangePassword on jake.h
# ============================================================
Save "04_password_change_events_4724_4738" {
    Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4724,4738} -MaxEvents 500 |
    Select-Object TimeCreated, Id,
        @{N='TargetAccount';E={ ($_.Properties[0]).Value }},
        @{N='SubjectAccount';E={ ($_.Properties[4]).Value }} |
    Sort-Object TimeCreated
}

# ============================================================
# STAGE 5-10 - jake.h AD CS abuse: OID creation, template creation,
# DACL modification, template ESC1 conversion
# ============================================================
Save "05_directory_service_changes_5136_5137_5141" {
    Get-WinEvent -FilterHashtable @{LogName='Security'; Id=5136,5137,5141} -MaxEvents 2000 |
    Select-Object TimeCreated, Id,
        @{N='SubjectAccount';E={ ($_.Properties[1]).Value }},
        @{N='ObjectDN';E={ ($_.Properties[6]).Value }},
        @{N='AttributeLDAPDisplayName';E={ ($_.Properties[8]).Value }},
        @{N='AttributeValue';E={ ($_.Properties[9]).Value }} |
    Sort-Object TimeCreated
}
Save "05_certificate_template_objects" {
    "Enumerate current AD CS template + OID objects for cross-reference:"
    certutil -template
}
Save "05_dacl_backup_files" {
    Get-ChildItem -Path C:\ -Filter "dacledit-*.bak" -Recurse -EA SilentlyContinue
}

# ============================================================
# STAGE 11-13 - Certificate enrollment (ESC1) + PKINIT as Administrator
# ============================================================
Save "06_cert_services_enrollment_events" {
    Get-WinEvent -LogName 'Microsoft-Windows-CertificationAuthority/Operational' -MaxEvents 500 |
    Select-Object TimeCreated, Id, Message
}
Save "06_issued_certificates" {
    certutil -view -restrict "Disposition=20" -out "RequestID,Request.RequesterName,CommonName,NotBefore,NotAfter,CertificateTemplate" csv
}
Save "06_kerberos_pkinit_events" {
    Get-WinEvent -LogName 'Microsoft-Windows-Kerberos/Operational' -MaxEvents 500 |
    Select-Object TimeCreated, Id, Message
}
Save "06_kerberos_tgt_requests_4768" {
    Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4768,4769} -MaxEvents 1000 |
    Select-Object TimeCreated, Id,
        @{N='TargetUserName';E={ ($_.Properties[0]).Value }},
        @{N='IpAddress';E={ ($_.Properties[9]).Value }},
        @{N='CertIssuerName';E={ ($_.Properties[19]).Value }} |
    Sort-Object TimeCreated
}

# ============================================================
# STAGE 14 - Administrator access confirmation
# ============================================================
Save "07_admin_logon_events" {
    Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624} -MaxEvents 500 |
    Where-Object { $_.Message -match 'Administrator' } |
    Select-Object TimeCreated, Id, Message
}
Save "07_winrm_connections" {
    Get-WinEvent -LogName 'Microsoft-Windows-WinRM/Operational' -MaxEvents 500 |
    Select-Object TimeCreated, Id, Message
}

# ============================================================
# Consolidated timeline (merge all Security log events chronologically)
# ============================================================
Save "00_FULL_TIMELINE_security_log" {
    Get-WinEvent -LogName Security -MaxEvents 5000 |
    Select-Object TimeCreated, Id, LevelDisplayName,
        @{N='Account';E={ if ($_.Properties.Count -gt 5) { ($_.Properties[5]).Value } }} |
    Sort-Object TimeCreated
}

# ============================================================
# Package everything
# ============================================================
$zipPath = "$OutDir.zip"
Compress-Archive -Path "$OutDir\*" -DestinationPath $zipPath -Force
Write-Host "`n[+] Attack chain evidence collected."
Write-Host "[+] Folder : $OutDir"
Write-Host "[+] Archive: $zipPath"
Write-Host "`n[i] Pull the .zip off the box (e.g. via evil-winrm 'download') and load"
Write-Host "    the evtx/ folder into Timeline Explorer / EvtxECmd / Chainsaw for"
Write-Host "    a full cross-referenced timeline of the compromise."
