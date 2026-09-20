#Requires -Version 5.1
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Enterprise MSI deployment engine.

.DESCRIPTION
    SYSTEM-run deployment worker for approved MSI packages in Packages\Ready.
    Developers/operators pre-validate packages with Scripts\Validator.ps1 before
    release. Only approved MSIs are copied into Ready. The engine validates
    repository metadata again, installs only newer versions, writes audit logs,
    and moves packages through Ready -> Archive / Rejected.

.NOTES
    Repository stores application metadata, hash allowlists, and History.
    Intended for Scheduled Task execution as SYSTEM.
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$BaseDir = "C:\Software"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:SupportedApps = @("PuTTY", "7-Zip")
$script:PackagesDir = Join-Path $BaseDir "Packages"
$script:ReadyDir = Join-Path $script:PackagesDir "Ready"
$script:ArchiveDir = Join-Path $script:PackagesDir "Archive"
$script:RejectedDir = Join-Path $script:PackagesDir "Rejected"
$script:RepositoryDir = Join-Path $BaseDir "Repository"
$script:EngineLogDir = Join-Path $BaseDir "Logs\Engine"
$script:WatcherLogDir = Join-Path $BaseDir "Logs\Watcher"
$script:ValidatorLogDir = Join-Path $BaseDir "Logs\Validator"
$script:LocksDir = Join-Path $BaseDir "Locks"
$script:ConfigDir = Join-Path $BaseDir "Config"
$script:ReportsDir = Join-Path $BaseDir "Reports"
$script:ScriptsDir = Join-Path $BaseDir "Scripts"
$script:LockPath = Join-Path $script:LocksDir "Deploy-Engine.lock"
$script:ProcessingDir = Join-Path $script:LocksDir "Processing"
$script:LogFile = $null
$script:TranscriptStarted = $false
$script:LockAcquired = $false
$script:EngineCmdlet = $PSCmdlet

$script:ForbiddenPathPrefixes = @(
    "$env:TEMP",
    "$env:TMP",
    "$env:APPDATA",
    "$env:LOCALAPPDATA",
    "C:\Users"
)

function Initialize-RestrictedDirectory {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }

    # Engine state is restricted because it runs as SYSTEM and writes audit data.
    $acl = Get-Acl -LiteralPath $Path
    $acl.SetAccessRuleProtection($true, $false)
    $adminRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
        "BUILTIN\Administrators", "FullControl", "ContainerInherit,ObjectInherit",
        "None", "Allow"
    )
    $systemRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
        "NT AUTHORITY\SYSTEM", "FullControl", "ContainerInherit,ObjectInherit",
        "None", "Allow"
    )
    $acl.SetAccessRule($adminRule)
    $acl.SetAccessRule($systemRule)
    Set-Acl -LiteralPath $Path -AclObject $acl
}

function Initialize-Directory {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Initialize-EngineDirectories {
    foreach ($dir in @($script:EngineLogDir, $script:LocksDir)) {
        Initialize-RestrictedDirectory -Path $dir
    }

    foreach ($dir in @($script:PackagesDir, $script:ReadyDir, $script:ArchiveDir, $script:RejectedDir, $script:RepositoryDir, $script:WatcherLogDir, $script:ValidatorLogDir, $script:ConfigDir, $script:ReportsDir, $script:ScriptsDir)) {
        Initialize-Directory -Path $dir
    }

    # Claimed packages are moved here before validation/install to close TOCTOU gaps.
    Initialize-RestrictedDirectory -Path $script:ProcessingDir

    foreach ($appName in $script:SupportedApps) {
        $appRepo = Join-Path $script:RepositoryDir $appName
        $historyDir = Join-Path $appRepo "History"
        Initialize-Directory -Path $appRepo
        Initialize-Directory -Path $historyDir
    }
}

function Write-Log {
    param(
        [Parameter(Mandatory)][string]$Message,
        [ValidateSet("INFO","WARN","ERROR","SECURITY","SUCCESS")]
        [string]$Level = "INFO"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $entry = "[$timestamp] [$Level] [ENGINE] $Message"

    if ($script:LogFile) {
        Add-Content -LiteralPath $script:LogFile -Value $entry -Encoding UTF8
    }

    $colour = switch ($Level) {
        "INFO"     { "Cyan" }
        "WARN"     { "Yellow" }
        "ERROR"    { "Red" }
        "SECURITY" { "Magenta" }
        "SUCCESS"  { "Green" }
    }
    Write-Host $entry -ForegroundColor $colour
}

function New-DeploymentError {
    param([string]$Message, [int]$Code)
    $ex = New-Object System.InvalidOperationException($Message)
    $ex.Data["ExitCode"] = $Code
    return $ex
}

function Acquire-EngineLock {
    if (Test-Path -LiteralPath $script:LockPath) {
        $existing = Get-Content -LiteralPath $script:LockPath -ErrorAction SilentlyContinue | Out-String
        throw (New-DeploymentError -Message "Another deployment engine run appears active. Lock: '$($script:LockPath)'. Existing: $existing" -Code 90)
    }

    $lockText = "PID=$PID`r`nComputer=$env:COMPUTERNAME`r`nUser=$env:USERDOMAIN\$env:USERNAME`r`nStarted=$(Get-Date -Format o)"
    New-Item -ItemType File -Path $script:LockPath -Value $lockText -ErrorAction Stop | Out-Null
    $script:LockAcquired = $true
    Write-Log "Acquired engine lock: '$($script:LockPath)'." -Level INFO
}

function Release-EngineLock {
    if ($script:LockAcquired -and (Test-Path -LiteralPath $script:LockPath)) {
        Remove-Item -LiteralPath $script:LockPath -Force
        $script:LockAcquired = $false
    }
}

function Get-ObjectValue {
    param($InputObject, [string]$Name, [string]$Default = "")

    if ($null -eq $InputObject) { return $Default }
    if ($InputObject -is [hashtable]) {
        if ($InputObject.ContainsKey($Name)) { return $InputObject[$Name] }
        return $Default
    }
    if ($InputObject.PSObject.Properties.Name -contains $Name) { return $InputObject.$Name }
    return $Default
}

function Assert-ReadyPath {
    param([string]$MsiPath)

    $readyRoot = [System.IO.Path]::GetFullPath($script:ReadyDir).TrimEnd('\') + '\'
    $fullPath = [System.IO.Path]::GetFullPath($MsiPath)

    if (-not $fullPath.StartsWith($readyRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw (New-DeploymentError -Message "SECURITY VIOLATION: MSI is outside Ready directory: '$MsiPath'" -Code 10)
    }

    foreach ($prefix in $script:ForbiddenPathPrefixes) {
        $expandedPrefix = [System.Environment]::ExpandEnvironmentVariables($prefix)
        if (-not [string]::IsNullOrWhiteSpace($expandedPrefix)) {
            $blockedRoot = [System.IO.Path]::GetFullPath($expandedPrefix).TrimEnd('\') + '\'
            if ($fullPath.StartsWith($blockedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
                throw (New-DeploymentError -Message "SECURITY VIOLATION: MSI path is in a forbidden location: '$MsiPath'" -Code 11)
            }
        }
    }
}

function Normalize-MsiGuid {
    param([string]$GuidValue)

    if ([string]::IsNullOrWhiteSpace($GuidValue)) { return $null }
    $parsedGuid = [System.Guid]::Empty
    if (-not [System.Guid]::TryParse($GuidValue.Trim(), [ref]$parsedGuid)) { return $null }
    return $parsedGuid.ToString("B").ToUpperInvariant()
}

function ConvertTo-VersionOrNull {
    param([string]$VersionText)

    if ([string]::IsNullOrWhiteSpace($VersionText)) { return $null }
    try { return [System.Version]::Parse($VersionText.Trim()) }
    catch {
        Write-Log "Could not parse version string '$VersionText'." -Level WARN
        return $null
    }
}

function Get-MsiProperty {
    param([string]$MsiPath, [string]$PropertyName)

    $installer = $null
    $database = $null
    $view = $null
    $record = $null

    try {
        $installer = New-Object -ComObject WindowsInstaller.Installer
        $database = $installer.OpenDatabase($MsiPath, 0)
        $view = $database.OpenView("SELECT Value FROM Property WHERE Property='$PropertyName'")
        $view.Execute()
        $record = $view.Fetch()
        if ($null -ne $record) { return $record.StringData(1) }
        return $null
    }
    finally {
        # Release COM objects explicitly to avoid Windows Installer handle leaks.
        if ($null -ne $record)    { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($record)    | Out-Null }
        if ($null -ne $view)      { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($view)      | Out-Null }
        if ($null -ne $database)  { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($database)  | Out-Null }
        if ($null -ne $installer) { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($installer) | Out-Null }
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()
    }
}

function Get-MsiMetadata {
    param([string]$MsiPath)

    Write-Log "Reading MSI metadata from: '$MsiPath'." -Level INFO
    $meta = @{
        ProductCode = Get-MsiProperty -MsiPath $MsiPath -PropertyName "ProductCode"
        PackageCode = Get-MsiProperty -MsiPath $MsiPath -PropertyName "PackageCode"
        ProductVersion = Get-MsiProperty -MsiPath $MsiPath -PropertyName "ProductVersion"
        ProductName = Get-MsiProperty -MsiPath $MsiPath -PropertyName "ProductName"
        Manufacturer = Get-MsiProperty -MsiPath $MsiPath -PropertyName "Manufacturer"
    }

    Write-Log "MSI ProductCode   : $($meta.ProductCode)" -Level INFO
    Write-Log "MSI PackageCode   : $($meta.PackageCode)" -Level INFO
    Write-Log "MSI ProductVersion: $($meta.ProductVersion)" -Level INFO
    Write-Log "MSI ProductName   : $($meta.ProductName)" -Level INFO
    return $meta
}

function Test-AppConfig {
    param([psobject]$Config, [string]$ConfigPath)

    foreach ($field in @("AppName","TrustedSubject","TrustedIssuerKeyword","ProductCode","InstallDir","VerifyFile","VerifyCommand","DisplayNameMatch")) {
        if ($Config.PSObject.Properties.Name -notcontains $field) {
            throw (New-DeploymentError -Message "Config '$ConfigPath' is missing required field '$field'." -Code 20)
        }
        if (($field -ne "VerifyCommand") -and [string]::IsNullOrWhiteSpace([string]$Config.$field)) {
            throw (New-DeploymentError -Message "Config '$ConfigPath' has empty required field '$field'." -Code 21)
        }
    }

    if ($script:SupportedApps -notcontains $Config.AppName) {
        throw (New-DeploymentError -Message "Config '$ConfigPath' AppName '$($Config.AppName)' is not allowlisted." -Code 22)
    }
    if ($null -eq (Normalize-MsiGuid -GuidValue $Config.ProductCode)) {
        throw (New-DeploymentError -Message "Config '$ConfigPath' ProductCode is invalid." -Code 23)
    }
}

function Get-AppConfig {
    param([hashtable]$MsiMeta)

    $msiProductCode = Normalize-MsiGuid -GuidValue $MsiMeta.ProductCode
    if ($null -eq $msiProductCode) {
        throw (New-DeploymentError -Message "MSI ProductCode is missing or invalid: '$($MsiMeta.ProductCode)'." -Code 24)
    }

    foreach ($appName in $script:SupportedApps) {
        $configPath = Join-Path (Join-Path $script:RepositoryDir $appName) "deploy.json"
        if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
            Write-Log "Repository config not present for '$appName': '$configPath'." -Level WARN
            continue
        }

        $config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
        Test-AppConfig -Config $config -ConfigPath $configPath

        $configProductCode = Normalize-MsiGuid -GuidValue $config.ProductCode
        $nameMatches = ($MsiMeta.ProductName -like "*$($config.DisplayNameMatch)*")
        if (($configProductCode -eq $msiProductCode) -or $nameMatches) {
            Write-Log "Matched MSI to approved repository app '$($config.AppName)'." -Level SUCCESS
            return $config
        }
    }

    throw (New-DeploymentError -Message "MSI is not approved by any Repository deploy.json. ProductName='$($MsiMeta.ProductName)', ProductCode='$($MsiMeta.ProductCode)'." -Code 25)
}

function Test-MsiHash {
    param([string]$MsiPath, [psobject]$Config)

    $hashPath = Join-Path (Join-Path $script:RepositoryDir $Config.AppName) "hashes.json"
    $sha256 = (Get-FileHash -LiteralPath $MsiPath -Algorithm SHA256).Hash.ToUpperInvariant()
    Write-Log "MSI SHA256         : $sha256" -Level INFO

    if (-not (Test-Path -LiteralPath $hashPath -PathType Leaf)) {
        Write-Log "No hashes.json found for '$($Config.AppName)'; optional hash allowlist skipped." -Level WARN
        return @{ Checked = $false; SHA256 = $sha256; Reason = "hashes.json not present" }
    }

    $hashConfig = Get-Content -LiteralPath $hashPath -Raw | ConvertFrom-Json
    if ($hashConfig.PSObject.Properties.Name -notcontains "AllowedSHA256") {
        throw (New-DeploymentError -Message "Hash config '$hashPath' is missing AllowedSHA256." -Code 26)
    }

    $allowed = @($hashConfig.AllowedSHA256 | ForEach-Object { ([string]$_).Trim().ToUpperInvariant() })
    if ($allowed -notcontains $sha256) {
        throw (New-DeploymentError -Message "MSI SHA256 is not approved by '$hashPath'." -Code 27)
    }

    Write-Log "MSI SHA256 allowlist validation: PASS." -Level SUCCESS
    return @{ Checked = $true; SHA256 = $sha256; Reason = "approved" }
}

function Test-MsiSignature {
    param([string]$MsiPath, [psobject]$Config)

    $sig = Get-AuthenticodeSignature -LiteralPath $MsiPath
    if ($sig.Status -ne [System.Management.Automation.SignatureStatus]::Valid) {
        return @{ Valid = $false; Reason = "Authenticode status is '$($sig.Status)' - expected 'Valid'."; Status = $sig.Status.ToString() }
    }

    $cert = $sig.SignerCertificate
    if ($null -eq $cert) {
        return @{ Valid = $false; Reason = "No signer certificate found despite Valid status." }
    }

    if ((Get-Date) -gt $cert.NotAfter) {
        return @{ Valid = $false; Reason = "Certificate expired on $($cert.NotAfter)."; Subject = $cert.Subject; Issuer = $cert.Issuer; Thumbprint = $cert.Thumbprint; NotAfter = $cert.NotAfter }
    }
    if ($cert.Subject -ne $Config.TrustedSubject) {
        return @{ Valid = $false; Reason = "Certificate Subject mismatch. Got '$($cert.Subject)', expected '$($Config.TrustedSubject)'."; Subject = $cert.Subject; Issuer = $cert.Issuer; Thumbprint = $cert.Thumbprint; NotAfter = $cert.NotAfter }
    }
    if ($cert.Issuer -notlike "*$($Config.TrustedIssuerKeyword)*") {
        return @{ Valid = $false; Reason = "Certificate Issuer does not contain '$($Config.TrustedIssuerKeyword)'. Got '$($cert.Issuer)'."; Subject = $cert.Subject; Issuer = $cert.Issuer; Thumbprint = $cert.Thumbprint; NotAfter = $cert.NotAfter }
    }

    Write-Log "Signature validation PASSED for '$($Config.AppName)'." -Level SUCCESS
    return @{ Valid = $true; Reason = "All signature checks passed."; Subject = $cert.Subject; Issuer = $cert.Issuer; Thumbprint = $cert.Thumbprint; Status = $sig.Status.ToString(); NotAfter = $cert.NotAfter }
}

function Assert-MsiProductCode {
    param([string]$ActualProductCode, [psobject]$Config)

    $expected = Normalize-MsiGuid -GuidValue $Config.ProductCode
    $actual = Normalize-MsiGuid -GuidValue $ActualProductCode
    if ($actual -ne $expected) {
        throw (New-DeploymentError -Message "SECURITY VIOLATION: ProductCode mismatch. Expected='$expected', Actual='$actual', Raw='$ActualProductCode'." -Code 28)
    }
    Write-Log "ProductCode validation: PASS ($actual)." -Level SUCCESS
}

function Get-InstalledAppVersion {
    param([psobject]$Config)

    foreach ($regPath in @("HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")) {
        if (-not (Test-Path -LiteralPath $regPath)) { continue }
        foreach ($app in (Get-ChildItem -Path $regPath -ErrorAction SilentlyContinue)) {
            $displayName = $app.GetValue("DisplayName")
            $uninstallString = $app.GetValue("UninstallString")
            $keyProductCode = Normalize-MsiGuid -GuidValue $app.PSChildName
            $configProductCode = Normalize-MsiGuid -GuidValue $Config.ProductCode
            $nameMatches = ($displayName -and ($displayName -like "*$($Config.DisplayNameMatch)*"))
            $productMatches = ($keyProductCode -and ($keyProductCode -eq $configProductCode))
            $uninstallMatches = ($uninstallString -and ($uninstallString -like "*$($Config.ProductCode)*"))

            if ($nameMatches -or $productMatches -or $uninstallMatches) {
                $versionText = $app.GetValue("DisplayVersion")
                $installLocation = $app.GetValue("InstallLocation")
                Write-Log "Installed $($Config.AppName) found: '$displayName' version '$versionText'." -Level INFO
                return @{ Found = $true; Version = ConvertTo-VersionOrNull -VersionText $versionText; VersionText = $versionText; DisplayName = $displayName; InstallLocation = $installLocation; RegistryKey = $app.PSPath }
            }
        }
    }

    Write-Log "No existing $($Config.AppName) installation detected." -Level INFO
    return @{ Found = $false; Version = $null; VersionText = ""; DisplayName = ""; InstallLocation = ""; RegistryKey = "" }
}

function Compare-Versions {
    param([System.Version]$InstalledVersion, [System.Version]$MsiVersion)

    if ($null -eq $InstalledVersion) { return "UnknownInstalledVersion" }
    $result = $InstalledVersion.CompareTo($MsiVersion)
    if ($result -lt 0) { return "Older" }
    if ($result -eq 0) { return "Equal" }
    return "Newer"
}

function Invoke-MsiUninstall {
    param([psobject]$Config)

    $productCode = Normalize-MsiGuid -GuidValue $Config.ProductCode
    $args = "/x $productCode /qn"
    Write-Log "Uninstalling existing $($Config.AppName): msiexec.exe $args" -Level INFO
    $proc = Start-Process -FilePath "msiexec.exe" -ArgumentList $args -Wait -PassThru -NoNewWindow
    Write-Log "msiexec uninstall exit code: $($proc.ExitCode)" -Level INFO
    if ($proc.ExitCode -notin @(0, 3010, 1605)) {
        throw (New-DeploymentError -Message "Uninstallation failed with exit code $($proc.ExitCode)." -Code 40)
    }
    Start-Sleep -Seconds 3
    return $proc.ExitCode
}

function Invoke-MsiInstall {
    param([string]$MsiPath, [psobject]$Config)

    $msiLogPath = Join-Path $script:EngineLogDir ("msiexec_{0}_{1}.log" -f $Config.AppName, (Get-Date -Format "yyyyMMdd_HHmmss"))
    $args = "/i `"$MsiPath`" /qn /norestart /L*V `"$msiLogPath`""
    $msiexecPath = "$env:SystemRoot\System32\msiexec.exe"
    Write-Log "Installing $($Config.AppName): '$msiexecPath' $args" -Level INFO
    $proc = Start-Process -FilePath $msiexecPath -ArgumentList $args -Wait -PassThru -NoNewWindow
    Write-Log "msiexec install exit code: $($proc.ExitCode)" -Level INFO
    Write-Log "msiexec verbose log: '$msiLogPath'" -Level INFO
    if ($proc.ExitCode -notin @(0, 3010)) {
        throw (New-DeploymentError -Message "Installation failed with exit code $($proc.ExitCode)." -Code 41)
    }
    return @{ ExitCode = $proc.ExitCode; MsiLogPath = $msiLogPath }
}

function Resolve-VerifyPath {
    param(
        [psobject]$Config,
        [hashtable]$InstalledInfo
    )

    $candidateDirs = New-Object System.Collections.ArrayList

    $registryInstallLocation = Get-ObjectValue $InstalledInfo "InstallLocation"
    if (-not [string]::IsNullOrWhiteSpace($registryInstallLocation)) {
        [void]$candidateDirs.Add($registryInstallLocation)
    }

    if (-not [string]::IsNullOrWhiteSpace($Config.InstallDir)) {
        [void]$candidateDirs.Add([System.Environment]::ExpandEnvironmentVariables($Config.InstallDir))
    }

    if ($Config.PSObject.Properties.Name -contains "InstallDirCandidates") {
        foreach ($dir in @($Config.InstallDirCandidates)) {
            if (-not [string]::IsNullOrWhiteSpace([string]$dir)) {
                [void]$candidateDirs.Add([System.Environment]::ExpandEnvironmentVariables([string]$dir))
            }
        }
    }

    $programFiles = [System.Environment]::GetFolderPath("ProgramFiles")
    $programFilesX86 = [System.Environment]::GetFolderPath("ProgramFilesX86")
    foreach ($root in @($programFiles, $programFilesX86)) {
        if (-not [string]::IsNullOrWhiteSpace($root)) {
            [void]$candidateDirs.Add((Join-Path $root $Config.DisplayNameMatch))
            [void]$candidateDirs.Add((Join-Path $root $Config.AppName))
        }
    }

    $checked = New-Object System.Collections.ArrayList
    foreach ($dir in $candidateDirs) {
        if ([string]::IsNullOrWhiteSpace($dir)) { continue }
        $candidate = Join-Path $dir $Config.VerifyFile
        if ($checked -contains $candidate) { continue }
        [void]$checked.Add($candidate)
        Write-Log "Checking post-install verify candidate: '$candidate'." -Level INFO
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }

    throw (New-DeploymentError -Message "POST-INSTALL FAILURE: verify file '$($Config.VerifyFile)' not found. Checked: $($checked -join '; ')." -Code 50)
}

function Test-PostInstall {
    param(
        [psobject]$Config,
        [hashtable]$InstalledInfo
    )

    $verifyPath = Resolve-VerifyPath -Config $Config -InstalledInfo $InstalledInfo

    $outputText = ""
    $exitCode = 0
    $verifyCommand = Get-ObjectValue -InputObject $Config -Name "VerifyCommand"
    if (-not [string]::IsNullOrWhiteSpace($verifyCommand)) {
        $verifyArgs = $verifyCommand -split "\s+"
        $output = & $verifyPath @verifyArgs 2>&1
        $exitCode = $LASTEXITCODE
        $outputText = $output -join "`n"
    }
    else {
        Write-Log "No VerifyCommand configured; post-install verification is file presence only for '$verifyPath'." -Level INFO
        $outputText = "VerifyCommand not configured; verify file exists."
    }

    Write-Log "Post-install verification passed for '$verifyPath' by running verify command. ExitCode=$exitCode." -Level SUCCESS
    return @{ VerifyFile = $verifyPath; SignatureStatus = "Skipped"; Signer = "Not checked"; Output = $outputText; ExitCode = $exitCode }
}

function Write-AuditRecord {
    param(
        [string]$MsiPath,
        [psobject]$Config,
        [hashtable]$SignatureInfo,
        [hashtable]$MsiMeta,
        [hashtable]$InstalledInfo,
        [hashtable]$HashInfo,
        [string]$MsiVersion,
        [string]$InstallAction,
        [string]$InstallResult,
        [hashtable]$PostInstallInfo,
        [string]$FinalState,
        [string]$FailureReason
    )

    $separator = "=" * 70
    Write-Log $separator -Level INFO
    Write-Log "DEPLOYMENT AUDIT RECORD" -Level INFO
    Write-Log $separator -Level INFO
    Write-Log "Timestamp           : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -Level INFO
    Write-Log "Final State         : $FinalState" -Level INFO
    Write-Log "Failure Reason      : $FailureReason" -Level INFO
    Write-Log "Application         : $(Get-ObjectValue $Config AppName Unknown)" -Level INFO
    Write-Log "MSI Path            : $MsiPath" -Level INFO
    Write-Log "MSI ProductName     : $(Get-ObjectValue $MsiMeta ProductName)" -Level INFO
    Write-Log "MSI ProductCode     : $(Get-ObjectValue $MsiMeta ProductCode)" -Level INFO
    Write-Log "MSI Version         : $MsiVersion" -Level INFO
    Write-Log "MSI SHA256          : $(Get-ObjectValue $HashInfo SHA256)" -Level INFO
    Write-Log "Hash Checked        : $(Get-ObjectValue $HashInfo Checked False)" -Level INFO
    Write-Log "Installed Found     : $(Get-ObjectValue $InstalledInfo Found False)" -Level INFO
    Write-Log "Installed Name      : $(Get-ObjectValue $InstalledInfo DisplayName)" -Level INFO
    Write-Log "Installed Version   : $(Get-ObjectValue $InstalledInfo VersionText)" -Level INFO
    Write-Log "Action Taken        : $InstallAction" -Level INFO
    Write-Log "Install Result      : $InstallResult" -Level INFO
    Write-Log "Sig Validation      : $(Get-ObjectValue $SignatureInfo Reason)" -Level INFO
    Write-Log "Cert Subject        : $(Get-ObjectValue $SignatureInfo Subject)" -Level INFO
    Write-Log "Cert Issuer         : $(Get-ObjectValue $SignatureInfo Issuer)" -Level INFO
    Write-Log "Cert Thumbprint     : $(Get-ObjectValue $SignatureInfo Thumbprint)" -Level INFO
    Write-Log "Verify File         : $(Get-ObjectValue $PostInstallInfo VerifyFile)" -Level INFO
    Write-Log "Verify Output       : $(Get-ObjectValue $PostInstallInfo Output)" -Level INFO
    Write-Log $separator -Level INFO
}

function Move-ProcessedMsi {
    param([string]$MsiPath, [ValidateSet("Archive","Rejected")][string]$State, [string]$AppName)

    $targetRoot = if ($State -eq "Archive") { $script:ArchiveDir } else { $script:RejectedDir }
    $safeAppName = if ([string]::IsNullOrWhiteSpace($AppName)) { "Unknown" } else { $AppName }
    $targetDir = Join-Path $targetRoot $safeAppName
    Initialize-RestrictedDirectory -Path $targetDir

    $leaf = Split-Path -Path $MsiPath -Leaf
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($leaf)
    $extension = [System.IO.Path]::GetExtension($leaf)
    $targetPath = Join-Path $targetDir $leaf
    if (Test-Path -LiteralPath $targetPath) {
        $targetPath = Join-Path $targetDir ("{0}_{1}{2}" -f $baseName, (Get-Date -Format "yyyyMMdd_HHmmss"), $extension)
    }

    Move-Item -LiteralPath $MsiPath -Destination $targetPath -Force
    Write-Log "Moved MSI to $State path: '$targetPath'." -Level INFO
}

function Protect-ClaimedMsi {
    param([string]$Path)

    $acl = Get-Acl -LiteralPath $Path
    $acl.SetAccessRuleProtection($true, $false)
    $adminRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
        "BUILTIN\Administrators", "FullControl", "None", "None", "Allow"
    )
    $systemRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
        "NT AUTHORITY\SYSTEM", "FullControl", "None", "None", "Allow"
    )
    $acl.SetAccessRule($adminRule)
    $acl.SetAccessRule($systemRule)
    Set-Acl -LiteralPath $Path -AclObject $acl

    $stream = $null
    try {
        $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    }
    catch {
        throw (New-DeploymentError -Message "Claimed MSI is still open by another process and will not be installed: '$Path'. $($_.Exception.Message)" -Code 61)
    }
    finally {
        if ($null -ne $stream) {
            $stream.Close()
        }
    }
}

function Claim-ReadyMsi {
    param([System.IO.FileInfo]$MsiFile)

    $sourcePath = $MsiFile.FullName
    Assert-ReadyPath -MsiPath $sourcePath
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
        throw (New-DeploymentError -Message "MSI disappeared before it could be claimed: '$sourcePath'." -Code 60)
    }

    $leaf = Split-Path -Path $sourcePath -Leaf
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($leaf)
    $extension = [System.IO.Path]::GetExtension($leaf)
    $claimName = "{0}_{1}_{2}{3}" -f $baseName, (Get-Date -Format "yyyyMMdd_HHmmssfff"), ([System.Guid]::NewGuid().ToString("N")), $extension
    $claimedPath = Join-Path $script:ProcessingDir $claimName
    $moved = $false

    try {
        # Atomic same-volume move: after this point, validation and install use only the claimed file.
        Move-Item -LiteralPath $sourcePath -Destination $claimedPath -ErrorAction Stop
        $moved = $true
        Protect-ClaimedMsi -Path $claimedPath
    }
    catch {
        if ($moved -and (Test-Path -LiteralPath $claimedPath -PathType Leaf)) {
            try { Move-ProcessedMsi -MsiPath $claimedPath -State "Rejected" -AppName "Unknown" } catch { }
        }
        throw
    }

    Write-Log "Claimed Ready MSI into restricted processing path: '$claimedPath'." -Level INFO

    return Get-Item -LiteralPath $claimedPath
}

function Get-ReadyMsiFiles {
    if (-not (Test-Path -LiteralPath $script:ReadyDir -PathType Container)) { return }
    Get-ChildItem -LiteralPath $script:ReadyDir -Filter "*.msi" -File | Sort-Object LastWriteTimeUtc, Name
}

function Invoke-MsiDeployment {
    param([System.IO.FileInfo]$MsiFile)

    $msiPath = $MsiFile.FullName
    $config = [pscustomobject]@{ AppName = "Unknown" }
    $sigInfo = @{ Reason = "Not evaluated." }
    $msiMeta = @{}
    $installedInfo = @{ Found = $false; Version = $null; VersionText = ""; DisplayName = "" }
    $hashInfo = @{ Checked = $false; SHA256 = ""; Reason = "Not evaluated." }
    $postInstallInfo = @{ VerifyFile = ""; Signer = ""; Output = "" }
    $installAction = "Unknown"
    $installResult = "Not attempted"
    $msiVersionText = ""

    try {
        Write-Log "Processing claimed MSI: '$msiPath'." -Level INFO
        if (-not (Test-Path -LiteralPath $msiPath -PathType Leaf)) {
            throw (New-DeploymentError -Message "MSI file not found: '$msiPath'." -Code 12)
        }

        $msiMeta = Get-MsiMetadata -MsiPath $msiPath
        $config = Get-AppConfig -MsiMeta $msiMeta
        $hashInfo = Test-MsiHash -MsiPath $msiPath -Config $config
        $sigInfo = Test-MsiSignature -MsiPath $msiPath -Config $config
        if (-not $sigInfo.Valid) {
            throw (New-DeploymentError -Message "MSI REJECTED - Signature validation failed: $($sigInfo.Reason)" -Code 29)
        }
        Assert-MsiProductCode -ActualProductCode $msiMeta.ProductCode -Config $config

        $msiVersion = ConvertTo-VersionOrNull -VersionText $msiMeta.ProductVersion
        if ($null -eq $msiVersion) {
            throw (New-DeploymentError -Message "Could not parse MSI ProductVersion '$($msiMeta.ProductVersion)'." -Code 30)
        }
        $msiVersionText = $msiVersion.ToString()

        $installedInfo = Get-InstalledAppVersion -Config $config
        if (-not $installedInfo.Found) {
            $installAction = "Fresh Install"
        }
        else {
            $comparison = Compare-Versions -InstalledVersion $installedInfo.Version -MsiVersion $msiVersion
            Write-Log "Version comparison: Installed=$($installedInfo.VersionText), MSI=$msiVersion, Result=$comparison." -Level INFO

            if ($comparison -eq "Older") {
                $installAction = "Upgrade (Uninstall + Install)"
                if ($script:EngineCmdlet.ShouldProcess($config.AppName, "Uninstall older version")) {
                    Invoke-MsiUninstall -Config $config | Out-Null
                }
            }
            elseif ($comparison -eq "Equal") {
                $installAction = "Skipped (Already Current)"
                $installResult = "Skipped - version $($installedInfo.VersionText) already installed."
                $postInstallInfo = Test-PostInstall -Config $config -InstalledInfo $installedInfo
                return @{ State = "Archive"; AppName = $config.AppName; Config = $config; SignatureInfo = $sigInfo; MsiMeta = $msiMeta; InstalledInfo = $installedInfo; HashInfo = $hashInfo; MsiVersion = $msiVersionText; InstallAction = $installAction; InstallResult = $installResult; PostInstallInfo = $postInstallInfo; FailureReason = "" }
            }
            elseif ($comparison -eq "Newer") {
                throw (New-DeploymentError -Message "Downgrade prevented. Installed version '$($installedInfo.VersionText)' is newer than MSI '$msiVersion'." -Code 31)
            }
            else {
                throw (New-DeploymentError -Message "Installed version could not be parsed; refusing ambiguous install." -Code 32)
            }
        }

        if ($script:EngineCmdlet.ShouldProcess($msiPath, "Install $($config.AppName) MSI")) {
            $installInfo = Invoke-MsiInstall -MsiPath $msiPath -Config $config
            $installResult = "Success (msiexec exit code: $($installInfo.ExitCode), log: $($installInfo.MsiLogPath))"
        }

        $installedInfo = Get-InstalledAppVersion -Config $config
        $postInstallInfo = Test-PostInstall -Config $config -InstalledInfo $installedInfo
        return @{ State = "Archive"; AppName = $config.AppName; Config = $config; SignatureInfo = $sigInfo; MsiMeta = $msiMeta; InstalledInfo = $installedInfo; HashInfo = $hashInfo; MsiVersion = $msiVersionText; InstallAction = $installAction; InstallResult = $installResult; PostInstallInfo = $postInstallInfo; FailureReason = "" }
    }
    catch {
        $failure = $_.Exception.Message
        Write-Log $failure -Level SECURITY
        return @{ State = "Rejected"; AppName = (Get-ObjectValue $config AppName Unknown); Config = $config; SignatureInfo = $sigInfo; MsiMeta = $msiMeta; InstalledInfo = $installedInfo; HashInfo = $hashInfo; MsiVersion = $msiVersionText; InstallAction = $installAction; InstallResult = $installResult; PostInstallInfo = $postInstallInfo; FailureReason = $failure }
    }
}

try {
    Initialize-EngineDirectories

    $script:LogFile = Join-Path $script:EngineLogDir ("DeployEngine_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    $transcriptFile = Join-Path $script:EngineLogDir ("Transcript_DeployEngine_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    Start-Transcript -LiteralPath $transcriptFile -Append
    $script:TranscriptStarted = $true

    Write-Log "Enterprise MSI Deployment Engine - Starting." -Level INFO
    Write-Log "Workflow: developers validate packages, approved MSIs enter Ready, SYSTEM engine installs, Repository preserves metadata/history." -Level INFO
    Write-Log "Ready Directory     : $($script:ReadyDir)" -Level INFO
    Write-Log "Processing Directory: $($script:ProcessingDir)" -Level INFO
    Write-Log "Repository Directory: $($script:RepositoryDir)" -Level INFO
    Write-Log "Engine Log File     : $($script:LogFile)" -Level INFO
    Write-Log "Supported Apps      : $($script:SupportedApps -join ', ')" -Level INFO

    Acquire-EngineLock

    $readyFiles = @(Get-ReadyMsiFiles)
    if ($readyFiles.Count -eq 0) {
        Write-Log "No MSI files found in Ready directory. Nothing to process." -Level INFO
        exit 0
    }

    $processedCount = 0
    $rejectedCount = 0
    foreach ($msiFile in $readyFiles) {
        try {
            $claimedMsi = Claim-ReadyMsi -MsiFile $msiFile
        }
        catch {
            Write-Log "Could not claim Ready MSI '$($msiFile.FullName)': $($_.Exception.Message)" -Level WARN
            continue
        }

        $result = Invoke-MsiDeployment -MsiFile $claimedMsi
        Write-AuditRecord -MsiPath $claimedMsi.FullName -Config $result.Config -SignatureInfo $result.SignatureInfo -MsiMeta $result.MsiMeta -InstalledInfo $result.InstalledInfo -HashInfo $result.HashInfo -MsiVersion $result.MsiVersion -InstallAction $result.InstallAction -InstallResult $result.InstallResult -PostInstallInfo $result.PostInstallInfo -FinalState $result.State -FailureReason $result.FailureReason
        Move-ProcessedMsi -MsiPath $claimedMsi.FullName -State $result.State -AppName $result.AppName
        $processedCount++
        if ($result.State -eq "Rejected") { $rejectedCount++ }
    }

    Write-Log "Deployment engine completed. Processed=$processedCount, Rejected=$rejectedCount." -Level SUCCESS
    if ($rejectedCount -gt 0) { exit 2 }
    exit 0
}
catch {
    $line = $_.InvocationInfo.ScriptLineNumber
    Write-Log "UNHANDLED ENGINE EXCEPTION at line $line : $($_.Exception.Message)" -Level ERROR
    Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level ERROR
    exit 99
}
finally {
    Release-EngineLock
    if ($script:TranscriptStarted) {
        try { Stop-Transcript } catch { <# Ignore transcript stop errors #> }
    }
}
