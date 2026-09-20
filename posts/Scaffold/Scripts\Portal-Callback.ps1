#Requires -Version 5.1
<#
.SYNOPSIS
    Portal Callback Helper. called by Deploy-Engine.ps1 after each deployment attempt.
    Posts the engine result back to the Scaffold Portal REST endpoint so the web UI
    reflects the current deployment state without a manual refresh.

.NOTES
    This script runs in the context of Deploy-Engine.ps1 (SYSTEM account).
    It uses Windows Integrated Auth (current process token) to authenticate to the portal.
    The portal endpoint /api/engine/result accepts POST from SYSTEM / Deployment_Admins only.
#>

param(
    [Parameter(Mandatory)][int]    $PackageId,
    [Parameter(Mandatory)][string] $Result,          # Success | Failed | AlreadyCurrent | Skipped
    [Parameter(Mandatory)][string] $EngineOutput,
    [string] $FailureReason  = '',
    [bool]   $HashChecked    = $false,
    [bool]   $SignatureValid = $true,
    [string] $PortalBaseUrl  = 'https://portal.scaffold.htb'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-EngineLog {
    param([string]$Level, [string]$Message)
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff'
    Write-Host "[$ts] [$Level] [CALLBACK] $Message"
}

try {
    $body = @{
        packageId      = $PackageId
        result         = $Result
        engineOutput   = $EngineOutput
        failureReason  = $FailureReason
        hashChecked    = $HashChecked
        signatureValid = $SignatureValid
        machineName    = $env:COMPUTERNAME
    } | ConvertTo-Json -Depth 3

    $params = @{
        Uri             = "$PortalBaseUrl/api/engine/result"
        Method          = 'POST'
        Body            = $body
        ContentType     = 'application/json'
        UseDefaultCredentials = $true          # Kerberos / NTLM as SYSTEM
        TimeoutSec      = 30
    }

    $resp = Invoke-RestMethod @params
    Write-EngineLog 'SUCCESS' "Portal updated for package $PackageId — result: $Result"
    return $resp
}
catch {
    # Non-fatal — engine deployment already completed; portal sync failure is logged only
    Write-EngineLog 'WARN' "Portal callback failed for package $PackageId`: $_"
}
