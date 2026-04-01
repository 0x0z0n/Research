import yaml
from datetime import datetime

def parse_pcap_yaml(file_path):
    try:
        with open(file_path, 'r') as file:
            # safe_load automatically handles the !!binary base64 decoding
            pcap_data = yaml.safe_load(file)
    except Exception as e:
        print(f"Error reading YAML file: {e}")
        return

    # Map peer IDs to their host:port representation for easy lookup
    peers = {}
    for peer in pcap_data.get('peers', []):
        peers[peer['peer']] = f"{peer['host']}:{peer['port']}"

    print("=" * 80)
    print(f"{'PCAP YAML PARSER':^80}")
    print("=" * 80)

    # Iterate through each packet
    for packet in pcap_data.get('packets', []):
        pkt_id = packet.get('packet')
        peer_id = packet.get('peer')
        timestamp = packet.get('timestamp')
        raw_data = packet.get('data') 

        # Convert UNIX timestamp to a human-readable datetime string
        dt_object = datetime.fromtimestamp(float(timestamp))
        formatted_time = dt_object.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        peer_info = peers.get(peer_id, f"Unknown Peer ({peer_id})")

        print(f"\n[ Packet {pkt_id} ] | Time: {formatted_time} | Peer: {peer_info}")
        print("-" * 80)

        if raw_data:
            # Decode bytes to string. 
            # errors='replace' ensures that the binary payload (like the encrypted Kerberos ticket) 
            # doesn't crash the script and prints as '' while leaving HTTP text readable.
            readable_data = raw_data.decode('utf-8', errors='replace')
            print(readable_data.strip())
        else:
            print("<No Data>")
            
        print("=" * 80)

if __name__ == "__main__":
    # Replace 'capture.yaml' with the actual path to your YAML file
    parse_pcap_yaml("capture.yaml")
