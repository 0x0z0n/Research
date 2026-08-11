$body = @{IsSysAdmin="true";OldPassword="whatever";Username="admin";NewPassword="P@ssw0rd123!@#";ConfirmPassword="P@ssw0rd123!@#"} | ConvertTo-Json
try {
    $r = Invoke-WebRequest -Uri "http://localhost:17017/api/v1/auth/force-reset-password" -Method Post -Body $body -ContentType "application/json" -UseBasicParsing
    "STATUS:$($r.StatusCode)`nBODY:$($r.Content)" | Out-File -FilePath C:\Windows\Temp\smres2.txt -Encoding ascii -Force
} catch {
    $errMsg = $_.ErrorDetails.Message
    "STATUS:ERR`nBODY:$errMsg" | Out-File -FilePath C:\Windows\Temp\smres2.txt -Encoding ascii -Force
}
