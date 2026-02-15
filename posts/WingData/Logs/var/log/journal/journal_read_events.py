import re
import binascii

def decode_hex_proctitle(hex_str):
    """Decodes hex strings (like 637000...) into readable text with spaces."""
    try:
        # Check if it looks like valid hex (even length, hex chars only)
        if len(hex_str) > 8 and len(hex_str) % 2 == 0 and re.match(r'^[0-9A-Fa-f]+$', hex_str):
            # Decode to bytes, then string, replacing null bytes with spaces
            decoded = binascii.unhexlify(hex_str).decode('utf-8', errors='replace')
            return decoded.replace('\x00', ' ').strip()
    except Exception:
        pass
    return hex_str  # Return original if not hex

def parse_journal(filename):
    print(f"{'TIME':<20} | {'UID':<6} | {'COMMAND (EXE)':<40} | {'FULL ARGUMENTS (PROCTITLE)'}")
    print("-" * 120)

    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        current_entry = {}
        
        for line in f:
            line = line.strip()
            
            # 1. Extract Timestamp (e.g., Feb 15 05:28:06)
            ts_match = re.match(r'^([A-Z][a-z]{2}\s+\d+\s\d{2}:\d{2}:\d{2})', line)
            timestamp = ts_match.group(1) if ts_match else "Unknown"

            # 2. Handle SYSCALL Lines (The main event)
            if "type=SYSCALL" in line or "SYSCALL " in line:
                # Extract key=value pairs
                kv_pairs = dict(re.findall(r'(\w+)=(".*?"|\S+)', line))
                
                # We only care about specific fields
                exe = kv_pairs.get("exe", "?").strip('"')
                uid = kv_pairs.get("uid", "?")
                comm = kv_pairs.get("comm", "?").strip('"')
                
                # Print the main event row
                print(f"{timestamp:<20} | {uid:<6} | {exe:<40} | ", end="")
                
                # If we don't find a proctitle immediately, we leave the line open or print comm
                current_entry['waiting_for_proctitle'] = True

            # 3. Handle PROCTITLE Lines (The detailed arguments)
            elif "type=PROCTITLE" in line or "PROCTITLE " in line:
                # Extract the proctitle value
                match = re.search(r'proctitle=(\S+)', line)
                if match:
                    raw_title = match.group(1).strip('"')
                    # Check if it needs hex decoding
                    decoded_title = decode_hex_proctitle(raw_title)
                    print(f"{decoded_title}")
                    current_entry['waiting_for_proctitle'] = False
                else:
                    # Sometimes proctitle is quoted with spaces
                    match_q = re.search(r'proctitle="(.*?)"', line)
                    if match_q:
                        print(f"{match_q.group(1)}")
                        current_entry['waiting_for_proctitle'] = False
            
            # If we moved to a new log line and were waiting, just print a newline to close the row
            elif current_entry.get('waiting_for_proctitle') and "audit" in line:
                 print("(No args found)")
                 current_entry['waiting_for_proctitle'] = False

if __name__ == "__main__":
    # Run the parser
    parse_journal("readable_journal.txt")
