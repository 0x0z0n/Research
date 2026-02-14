for f in *.evtx; do python3 /usr/bin/evtx_dump.py "$f" > "$f.json"; done
