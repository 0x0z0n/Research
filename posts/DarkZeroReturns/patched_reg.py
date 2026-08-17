#!/usr/bin/env python3
# patched_reg.py
import sys, importlib.util, importlib

# 1. patch smb3 first, before reg.py (or anything it imports) binds a reference
import impacket.smb3 as smb3
_orig_kerberosLogin = smb3.SMB3.kerberosLogin

def patched_kerberosLogin(self, *args, **kwargs):
    print("[PATCH] kerberosLogin CALLED", file=sys.stderr, flush=True)
    print("[PATCH] args before override:", args, file=sys.stderr, flush=True)
    print("[PATCH] kwargs before override:", kwargs, file=sys.stderr, flush=True)
    args = list(args)
    if len(args) >= 3:
        print(f"[PATCH] overriding args[2] domain: {args[2]!r} -> 'DARKZERO.EXT'", file=sys.stderr, flush=True)
        args[2] = 'DARKZERO.EXT'
    else:
        print(f"[PATCH] overriding kwargs domain: {kwargs.get('domain')!r} -> 'DARKZERO.EXT'", file=sys.stderr, flush=True)
        kwargs['domain'] = 'DARKZERO.EXT'
    return _orig_kerberosLogin(self, *args, **kwargs)

smb3.SMB3.kerberosLogin = patched_kerberosLogin
print(f"[PATCH] smb3 module id={id(smb3)} file={smb3.__file__}", file=sys.stderr, flush=True)
print(f"[PATCH] SMB3.kerberosLogin now = {smb3.SMB3.kerberosLogin}", file=sys.stderr, flush=True)

# 2. locate the real reg.py path from the console-script shim, then exec it
REG_PY_PATH = "/usr/share/doc/python3-impacket/examples/reg.py"

spec = importlib.util.spec_from_file_location("__main__", REG_PY_PATH)
mod = importlib.util.module_from_spec(spec)
sys.argv[0] = REG_PY_PATH  # so argparse's usage string looks right
spec.loader.exec_module(mod)  # runs the script's __main__ block, patched smb3 already active
