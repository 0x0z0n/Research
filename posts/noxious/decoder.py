import yaml
import re
import sys
import argparse
from datetime import datetime

# -------------------------------------------------------------------------
# CONFIGURATION & CONSTANTS
# -------------------------------------------------------------------------

# Common Port Mappings for Protocol Identification
PORT_MAP = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 88: "Kerberos", 110: "POP3", 135: "RPC", 139: "NetBIOS",
    143: "IMAP", 389: "LDAP", 443: "HTTPS", 445: "SMB", 464: "Kerberos-PW",
    587: "SMTP-Sub", 636: "LDAP-SSL", 993: "IMAP-SSL", 995: "POP3-SSL",
    1433: "SQL", 3306: "MySQL", 3389: "RDP", 5900: "VNC", 5985: "WinRM-HTTP",
    5986: "WinRM-HTTPS", 8080: "HTTP-Alt"
}

def get_protocol_name(src_port, dst_port, payload):
    """
    Guesses protocol based on port or binary signature.
    """
    # 1. Check Binary Signatures
    if len(payload) > 4:
        if payload.startswith(b'\xfeSMB'): return "SMB2/3"
        if payload.startswith(b'\xffSMB'): return "SMB1"
        if payload.startswith(b'\x16\x03'): return "TLS/SSL"
        if payload.startswith(b'HTTP'): return "HTTP"
        if payload.startswith(b'ssh-'): return "SSH"
    
    # 2. Check Ports
    if src_port in PORT_MAP: return PORT_MAP[src_port]
    if dst_port in PORT_MAP: return PORT_MAP[dst_port]
    
    return "TCP/UDP"

def extract_strings(data):
    """
    Universally extracts readable strings from binary data.
    Captures both ASCII (Network/Linux) and UTF-16LE (Windows/SMB/RDP).
    """
    found = []
    
    # 1. Extract ASCII strings (min length 4)
    # Regex: 4 or more printable characters
    ascii_hits = re.findall(b'[ -~]{4,}', data)
    for s in ascii_hits:
        try:
            found.append(s.decode('utf-8'))
        except: pass

    # 2. Extract UTF-16LE strings (Common in Windows environments)
    # Regex: 4 or more chars where every second byte is null (basic latin in utf-16)
    wide_hits = re.findall(b'(?:[ -~]\x00){4,}', data)
    for s in wide_hits:
        try:
            found.append(s.decode('utf-16le'))
        except: pass
        
    return list(set(found)) # Remove duplicates

def format_hexdump(data, length=16):
    """
    Returns a single line hexdump preview of the start of the packet.
    """
    preview = data[:length]
    hex_str = ' '.join(f'{b:02x}' for b in preview)
    return hex_str.upper()

# -------------------------------------------------------------------------
# MAIN LOGIC
# -------------------------------------------------------------------------

def analyze_yaml(input_file, output_file):
    print(f"[*] Reading {input_file}...")
    
    try:
        with open(input_file, 'r') as f:
            doc = yaml.safe_load(f)
    except Exception as e:
        print(f"[!] Error reading YAML: {e}")
        return

    # Map Peer ID to Host:Port
    peers = {}
    if 'peers' in doc:
        for p in doc['peers']:
            peers[p['peer']] = {'host': p['host'], 'port': p['port']}
    
    print(f"[*] Decoding {len(doc.get('packets', []))} packets...")
    print(f"[*] Writing results to {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as out:
        # File Header
        out.write("="*80 + "\n")
        out.write(f"UNIVERSAL PACKET DECODE REPORT\n")
        out.write(f"Generated: {datetime.now()}\n")
        out.write(f"Source File: {input_file}\n")
        out.write("="*80 + "\n\n")

        # Process Packets
        for pkt in doc.get('packets', []):
            # Basic Metadata
            ts = datetime.fromtimestamp(pkt['timestamp']).strftime('%Y-%m-%d %H:%M:%S.%f')
            pid = pkt['packet']
            peer_idx = pkt['peer']
            
            # Resolve Source/Dest
            # Assumption: The 'peer' in the packet entry is the SENDER.
            src_info = peers.get(peer_idx, {'host': 'Unknown', 'port': 0})
            
            # Find the "other" peer for Destination (assuming 2-party convo)
            dst_idx = 1 if peer_idx == 0 else 0
            dst_info = peers.get(dst_idx, {'host': 'Unknown', 'port': 0})
            
            payload = pkt['data']
            protocol = get_protocol_name(src_info['port'], dst_info['port'], payload)
            strings = extract_strings(payload)

            # --- WRITE PACKET BLOCK ---
            out.write(f"Packet #{pid} | Time: {ts} | Protocol: {protocol}\n")
            out.write(f"Flow: {src_info['host']}:{src_info['port']} --> {dst_info['host']}:{dst_info['port']}\n")
            out.write(f"Hex Preview: {format_hexdump(payload)}\n")
            
            if strings:
                out.write("Decoded Strings:\n")
                for s in strings:
                    # Clean up newlines for cleaner output
                    clean_s = s.replace('\n', ' ').replace('\r', '')
                    out.write(f"    > {clean_s}\n")
            else:
                out.write("    (No readable strings found)\n")
            
            out.write("-" * 60 + "\n")

    print("[+] Done! Check the output file.")

# -------------------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------------------

if __name__ == "__main__":
    # If run without arguments, looks for 'dump.yaml' and writes 'decoded_traffic.txt'
    # You can also pass arguments: python decoder.py input.yaml output.txt
    
    in_file = "dump.yaml"
    out_file = "decoded_traffic.txt"
    
    if len(sys.argv) > 1:
        in_file = sys.argv[1]
    if len(sys.argv) > 2:
        out_file = sys.argv[2]
        
    analyze_yaml(in_file, out_file)
