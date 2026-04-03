import argparse
import csv
import json
import logging
import hashlib
from pathlib import Path
from multiprocessing import Pool, cpu_count
from evtx import PyEvtxParser

# ==========================================
# EVTX-Omni: Enterprise Event Log Processor
# ==========================================

def setup_logging(debug=False):
    """Configures enterprise-grade logging."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(processName)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("evtx_processor.log")
        ]
    )

def hash_file(filepath):
    """Generates a SHA-256 hash of the evidence file for chain of custody."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def flatten_json(y):
    """Recursively flattens nested JSON, intelligently stripping unnecessary wrapper prefixes."""
    out = {}
    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                # Clean up any leftover XML namespace artifacts just in case
                clean_key = a.replace('@', '').replace('#', '')
                flatten(x[a], name + clean_key + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    # FIX: Windows Event Logs often wrap their payload in a single named 
    # XML tag (like <LogFileCleared>). We safely bypass this top-level 
    # wrapper if it's the only key to prevent ugly CSV headers.
    if isinstance(y, dict) and len(y) == 1:
        first_key = list(y.keys())[0]
        inner_data = y[first_key]
        if isinstance(inner_data, dict):
            # Start flattening from INSIDE the wrapper, dropping the prefix
            flatten(inner_data)
        else:
            flatten(y)
    else:
        flatten(y)
        
    return out

# ------------------------------------------
# PROCESSING ENGINES
# ------------------------------------------

def process_evtx_jsonl(input_path, output_dir):
    """Single-pass engine: Streams to ADX Web-UI friendly JSON Array."""
    output_file = output_dir / f"{input_path.stem}.json" # Outputs as .json
    parser = PyEvtxParser(str(input_path))
    event_count = 0
    
    with open(output_file, mode='w', encoding='utf-8') as outfile:
        # Start the JSON Array
        outfile.write('[\n') 
        first_record = True
        
        for record_string in parser.records_json():
            try:
                # Load the full raw JSON representation of the event
                record_dict = json.loads(record_string['data'])
                event_block = record_dict.get('Event', {})
                system_data = event_block.get('System', {})
                
                # Create the ADX Row: Core fields elevated + entire raw event preserved
                row = {
                    'TimeGenerated': system_data.get('TimeCreated', {}).get('#attributes', {}).get('SystemTime', ''),
                    'EventID': system_data.get('EventID', ''),
                    'Computer': system_data.get('Computer', ''),
                    'RawEvent': event_block # The 100% untouched event payload for dynamic KQL querying
                }
                
                # Add a comma before every record EXCEPT the very first one
                if not first_record:
                    outfile.write(',\n')
                
                outfile.write(json.dumps(row))
                first_record = False
                event_count += 1
                
            except json.JSONDecodeError:
                continue

        # Close the JSON Array
        outfile.write('\n]') 

    return event_count

def process_evtx_csv(input_path, output_dir):
    """Two-pass engine: Discovers schema, then streams to CSV with ZERO data loss."""
    output_file = output_dir / f"{input_path.stem}.csv"
    
    # PASS 1: Header Discovery
    logging.debug(f"Pass 1: Discovering schema for {input_path.name}")
    parser = PyEvtxParser(str(input_path))
    master_fieldnames = set(['TimeGenerated', 'EventID', 'Provider', 'Computer', 'Channel', 'RecordID', 'Level'])
    
    for record_string in parser.records_json():
        try:
            record_dict = json.loads(record_string['data'])
            event_data = record_dict.get('Event', {}).get('EventData', {})
            user_data = record_dict.get('Event', {}).get('UserData', {})
            
            # Combine payloads for discovery to ensure no dropped keys
            payload = {**event_data, **user_data} if isinstance(event_data, dict) and isinstance(user_data, dict) else (event_data or user_data)
            
            flat_payload = flatten_json(payload)
            master_fieldnames.update(flat_payload.keys())
        except json.JSONDecodeError:
            continue
            
    # Structure headers logically
    core_fields = ['TimeGenerated', 'EventID', 'Computer', 'Provider', 'Channel', 'RecordID', 'Level']
    dynamic_fields = sorted([f for f in master_fieldnames if f not in core_fields])
    final_headers = core_fields + dynamic_fields

    # PASS 2: Streaming Write
    logging.debug(f"Pass 2: Writing data to {output_file.name}")
    parser = PyEvtxParser(str(input_path)) # Reset parser
    event_count = 0
    
    with open(output_file, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=final_headers, restval='')
        writer.writeheader()
        
        for record_string in parser.records_json():
            try:
                record_dict = json.loads(record_string['data'])
                system_data = record_dict.get('Event', {}).get('System', {})
                event_data = record_dict.get('Event', {}).get('EventData', {})
                user_data = record_dict.get('Event', {}).get('UserData', {})
                
                payload = {**event_data, **user_data} if isinstance(event_data, dict) and isinstance(user_data, dict) else (event_data or user_data)
                flat_payload = flatten_json(payload)
                
                row = {
                    'TimeGenerated': system_data.get('TimeCreated', {}).get('#attributes', {}).get('SystemTime', ''),
                    'EventID': system_data.get('EventID', ''),
                    'Provider': system_data.get('Provider', {}).get('#attributes', {}).get('Name', ''),
                    'Computer': system_data.get('Computer', ''),
                    'Channel': system_data.get('Channel', ''),
                    'RecordID': system_data.get('EventRecordID', ''),
                    'Level': system_data.get('Level', ''),
                    **flat_payload
                }
                
                writer.writerow(row)
                event_count += 1
                
            except json.JSONDecodeError:
                continue

    return event_count

# ------------------------------------------
# WORKER DISPATCHER
# ------------------------------------------

def worker_dispatcher(args):
    """Unpacks arguments and routes to the correct processing engine."""
    input_file, output_dir_str, output_format = args
    input_path = Path(input_file)
    output_dir = Path(output_dir_str)
    
    file_hash = hash_file(input_path)
    logging.info(f"Processing {input_path.name} [{output_format.upper()}] (SHA256: {file_hash})")
    
    try:
        if output_format == 'jsonl':
            event_count = process_evtx_jsonl(input_path, output_dir)
        elif output_format == 'csv':
            event_count = process_evtx_csv(input_path, output_dir)
        else:
            raise ValueError(f"Unsupported format: {output_format}")
            
        logging.info(f"Success: {input_path.name} -> {event_count} events written.")
        return True
    except Exception as e:
        logging.error(f"Failed {input_path.name}: {str(e)}")
        return False

# ------------------------------------------
# MAIN ENTRY POINT
# ------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="EVTX-Omni: Enterprise Event Log Processor (CSV & ADX JSON)")
    parser.add_argument("-i", "--input", required=True, help="Path to input EVTX file or directory")
    parser.add_argument("-o", "--output", required=True, help="Path to output directory")
    parser.add_argument("-f", "--format", choices=['csv', 'jsonl'], default='jsonl', help="Output format: 'csv' (flattened, zero loss) or 'jsonl' (ADX/Elastic optimized). Default: jsonl")
    parser.add_argument("-w", "--workers", type=int, default=cpu_count(), help="Concurrent workers (default: all CPU cores)")
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logging")
    args = parser.parse_args()

    setup_logging(args.debug)
    
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build list of jobs
    files_to_process = []
    if input_path.is_file() and input_path.suffix.lower() == '.evtx':
        files_to_process.append((str(input_path), str(output_dir), args.format))
    elif input_path.is_dir():
        for evtx_file in input_path.glob('*.evtx'):
            files_to_process.append((str(evtx_file), str(output_dir), args.format))
    else:
        logging.error("Input must be an .evtx file or a directory containing .evtx files.")
        return

    if not files_to_process:
        logging.error("No EVTX files found to process.")
        return

    logging.info(f"Targeting {len(files_to_process)} file(s). Format: {args.format.upper()}. Workers: {args.workers}.")

    # Execute jobs using multiprocessing pool
    with Pool(processes=args.workers) as pool:
        results = pool.map(worker_dispatcher, files_to_process)
    
    successful = sum(1 for r in results if r)
    logging.info(f"Job Complete. {successful}/{len(files_to_process)} files processed successfully.")

if __name__ == "__main__":
    main()