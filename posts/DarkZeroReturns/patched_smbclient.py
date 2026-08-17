#!/usr/bin/env python3
# patched_smbclient.py
import sys, importlib.util

import impacket.smb3 as smb3
_orig_kerberosLogin = smb3.SMB3.kerberosLogin

def patched_kerberosLogin(self, *args, **kwargs):
    args = list(args)
    if len(args) >= 3:
        args[2] = 'DARKZERO.EXT'
    else:
        kwargs['domain'] = 'DARKZERO.EXT'
    return _orig_kerberosLogin(self, *args, **kwargs)

smb3.SMB3.kerberosLogin = patched_kerberosLogin

# use the SYSTEM package copy (same one the real impacket-smbclient shell wrapper
# invokes) - this one has the __main__ execution guard; the venv's examples/smbclient.py
# apparently does not run standalone the same way
SMBCLIENT_PY_PATH = "/usr/share/doc/python3-impacket/examples/smbclient.py"

spec = importlib.util.spec_from_file_location("__main__", SMBCLIENT_PY_PATH)
mod = importlib.util.module_from_spec(spec)
sys.argv[0] = SMBCLIENT_PY_PATH
spec.loader.exec_module(mod)
