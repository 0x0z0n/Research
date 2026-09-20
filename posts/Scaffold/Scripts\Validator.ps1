#Requires -Version 5.1

<#
.SYNOPSIS
    Low-privilege MSI pre-validation tool.

.DESCRIPTION
    Developers/operators run this before releasing an MSI into Packages\Ready.
    It validates repository metadata, signature trust, ProductCode, ProductName,
    and optional SHA256 allowlists. It never installs software.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$MsiPath,

    [string]$BaseDir = "C:\Software"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SupportedApps = @("PuTTY", "GoogleChrome", "WinSCP", "7zip", "7-Zip", "NotepadPlusPlus")
$RepositoryDir = Join-Path $BaseDir "Repository"
$ValidatorLogDir = Join-Path $BaseDir "Logs\Validator"
$LogFile = $null
$validationStream = $null
$ValidationUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
if ([string]::IsNullOrWhiteSpace($ValidationUser)) {
    $ValidationUser = "$env:USERDOMAIN\$env:USERNAME"
}

function Initialize-ValidatorLog {
    if (-not (Test-Path -LiteralPath $ValidatorLogDir)) {
        New-Item -ItemType Directory -Path $ValidatorLogDir -Force | Out-Null
    }
    $script:LogFile = Join-Path $ValidatorLogDir ("Validator_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
}

function Write-ValidatorLog {
    param(
        [string]$Message,
        [ValidateSet("INFO","WARN","ERROR","SUCCESS")]
        [string]$Level = "INFO"
    )

    $entry = "[{0}] [{1}] [VALIDATOR] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"), $Level, $Message
    if ($script:LogFile) {
        Add-Content -LiteralPath $script:LogFile -Value $entry -Encoding UTF8
    }
    Write-Host $entry
}

function Normalize-MsiGuid {
    param([string]$GuidValue)
    if ([string]::IsNullOrWhiteSpace($GuidValue)) { return $null }
    $parsedGuid = [System.Guid]::Empty
    if (-not [System.Guid]::TryParse($GuidValue.Trim(), [ref]$parsedGuid)) { return $null }
    return $parsedGuid.ToString("B").ToUpperInvariant()
}

function Get-MsiProperty {
    param([string]$Path, [string]$PropertyName)

    $installer = $null
    $database = $null
    $view = $null
    $record = $null

    try {
        $installer = New-Object -ComObject WindowsInstaller.Installer
        $database = $installer.OpenDatabase($Path, 0)
        $view = $database.OpenView("SELECT Value FROM Property WHERE Property='$PropertyName'")
        $view.Execute()
        $record = $view.Fetch()
        if ($null -ne $record) { return $record.StringData(1) }
        return $null
    }
    finally {
        if ($null -ne $record)    { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($record)    | Out-Null }
        if ($null -ne $view)      { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($view)      | Out-Null }
        if ($null -ne $database)  { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($database)  | Out-Null }
        if ($null -ne $installer) { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($installer) | Out-Null }
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()
    }
}

function Get-MsiMetadata {
    param([string]$Path)
    return @{
        ProductCode = Get-MsiProperty -Path $Path -PropertyName "ProductCode"
        ProductVersion = Get-MsiProperty -Path $Path -PropertyName "ProductVersion"
        ProductName = Get-MsiProperty -Path $Path -PropertyName "ProductName"
    }
}

function Get-MatchingConfig {
    param([hashtable]$MsiMeta)

    $msiProductCode = Normalize-MsiGuid -GuidValue $MsiMeta.ProductCode
    foreach ($appName in $SupportedApps) {
        $configPath = Join-Path (Join-Path $RepositoryDir $appName) "deploy.json"
        if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) { continue }

        $config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
        $configProductCode = Normalize-MsiGuid -GuidValue $config.ProductCode
        $nameMatches = ($MsiMeta.ProductName -like "*$($config.DisplayNameMatch)*")
        if (($configProductCode -eq $msiProductCode) -or $nameMatches) {
            return @{ Config = $config; ConfigPath = $configPath }
        }
    }

    throw "No approved Repository deploy.json matched ProductName='$($MsiMeta.ProductName)' ProductCode='$($MsiMeta.ProductCode)'."
}

function Test-RequiredConfig {
    param([psobject]$Config, [string]$ConfigPath)
    foreach ($field in @("AppName","TrustedSubject","TrustedIssuerKeyword","ProductCode","DisplayNameMatch")) {
        if ($Config.PSObject.Properties.Name -notcontains $field -or [string]::IsNullOrWhiteSpace([string]$Config.$field)) {
            throw "Config '$ConfigPath' is missing required field '$field'."
        }
    }
    if ($SupportedApps -notcontains $Config.AppName) {
        throw "Config AppName '$($Config.AppName)' is not allowlisted."
    }
}

function Test-HashAllowlist {
    param([string]$Path, [psobject]$Config)

    $hashPath = Join-Path (Join-Path $RepositoryDir $Config.AppName) "hashes.json"
    $sha256 = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
    Write-ValidatorLog "MSI SHA256: $sha256" -Level INFO

    if (-not (Test-Path -LiteralPath $hashPath -PathType Leaf)) {
        Write-ValidatorLog "No hashes.json found for '$($Config.AppName)'; optional hash allowlist skipped." -Level WARN
        return
    }

    $hashConfig = Get-Content -LiteralPath $hashPath -Raw | ConvertFrom-Json
    if ($hashConfig.PSObject.Properties.Name -notcontains "AllowedSHA256") {
        throw "Hash config '$hashPath' is missing AllowedSHA256."
    }

    $allowed = @($hashConfig.AllowedSHA256 | ForEach-Object { ([string]$_).Trim().ToUpperInvariant() })
    if ($allowed -notcontains $sha256) {
        throw "SHA256 is not approved by '$hashPath'."
    }
}

function Test-Signature {
    param([string]$Path, [psobject]$Config)

    $sig = Get-AuthenticodeSignature -LiteralPath $Path
    if ($sig.Status -ne [System.Management.Automation.SignatureStatus]::Valid) {
        throw "Authenticode status is '$($sig.Status)' - expected 'Valid'."
    }

    $cert = $sig.SignerCertificate
    if ($null -eq $cert) { throw "No signer certificate found." }
    if ((Get-Date) -gt $cert.NotAfter) { throw "Signer certificate expired on $($cert.NotAfter)." }
    if ($cert.Subject -ne $Config.TrustedSubject) { throw "Signer subject mismatch. Got '$($cert.Subject)', expected '$($Config.TrustedSubject)'." }
    if ($cert.Issuer -notlike "*$($Config.TrustedIssuerKeyword)*") { throw "Signer issuer '$($cert.Issuer)' does not contain '$($Config.TrustedIssuerKeyword)'." }
}

try {
    Initialize-ValidatorLog
    Write-ValidatorLog "Validating MSI: '$MsiPath'." -Level INFO
    Write-ValidatorLog "Validation requested by user: '$ValidationUser'." -Level INFO

    if (-not [System.IO.Path]::IsPathRooted($MsiPath)) { throw "MsiPath must be absolute." }
    if (-not (Test-Path -LiteralPath $MsiPath -PathType Leaf)) { throw "MSI does not exist: '$MsiPath'." }

    # Hold a read lock during validation so the result describes one stable file image.
    $validationStream = [System.IO.File]::Open($MsiPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::Read)

    $meta = Get-MsiMetadata -Path $MsiPath
    Write-ValidatorLog "ProductName='$($meta.ProductName)' ProductCode='$($meta.ProductCode)' ProductVersion='$($meta.ProductVersion)'." -Level INFO

    $match = Get-MatchingConfig -MsiMeta $meta
    $config = $match.Config
    Test-RequiredConfig -Config $config -ConfigPath $match.ConfigPath

    $actualProductCode = Normalize-MsiGuid -GuidValue $meta.ProductCode
    $expectedProductCode = Normalize-MsiGuid -GuidValue $config.ProductCode
    if ($actualProductCode -ne $expectedProductCode) {
        throw "ProductCode mismatch. Expected '$expectedProductCode', got '$actualProductCode'."
    }
    if ($meta.ProductName -notlike "*$($config.DisplayNameMatch)*") {
        throw "ProductName '$($meta.ProductName)' does not match DisplayNameMatch '$($config.DisplayNameMatch)'."
    }

    Test-Signature -Path $MsiPath -Config $config
    Test-HashAllowlist -Path $MsiPath -Config $config

    Write-ValidatorLog "VALID - '$MsiPath' is approved for '$($config.AppName)' by '$ValidationUser'." -Level SUCCESS
    Write-Output "VALID: User=$ValidationUser"
    exit 0
}
catch {
    $reason = $_.Exception.Message
    Write-ValidatorLog "REJECTED - User='$ValidationUser' Reason='$reason'" -Level ERROR
    Write-Output "REJECTED: User=$ValidationUser Reason=$reason"
    exit 1
}
finally {
    if ($null -ne $validationStream) {
        $validationStream.Close()
    }
}
