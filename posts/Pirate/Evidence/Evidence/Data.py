import os
import csv
import json
import concurrent.futures
import shutil
from evtx import PyEvtxParser # <-- Changed import to use the faster Rust wrapper

# Define the standard ADX columns globally
FIELDNAMES = ['TimeCreated', 'EventID', 'Provider', 'Computer', 'Channel', 'EventData']

def parse_evtx_to_temp_csv(filepath, temp_dir):
    """Worker function: Parses a single EVTX file and writes to a temporary CSV."""
    filename = os.path.basename(filepath)
    temp_csv_path = os.path.join(temp_dir, f"{filename}.tmp.csv")
    
    # We do NOT write headers in the temp files to make the final merge simpler
    try:
        with open(temp_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            
            # Initialize the Rust parser
            parser = PyEvtxParser(filepath)
            
            # records_json() yields a dictionary where 'data' contains the JSON string of the event
            for r in parser.records_json():
                try:
                    data_dict = json.loads(r['data'])
                    event = data_dict.get('Event', {})
                    system = event.get('System', {})

                    # Extract standard fields (Defensive gets to handle the JSON schema)
                    tc = system.get('TimeCreated', {})
                    time_created = tc.get('SystemTime', tc.get('#attributes', {}).get('SystemTime', ''))
                    
                    eid = system.get('EventID', '')
                    event_id = eid.get('#text', eid) if isinstance(eid, dict) else eid
                    
                    prov = system.get('Provider', {})
                    provider = prov.get('Name', prov.get('#attributes', {}).get('Name', ''))
                    
                    computer = system.get('Computer', '')
                    channel = system.get('Channel', '')

                    # Extract payload and serialize back to a tight JSON string for ADX
                    event_data = event.get('EventData', event.get('UserData', {}))
                    event_data_json = json.dumps(event_data) if event_data else '{}'

                    # Write row
                    writer.writerow({
                        'TimeCreated': time_created,
                        'EventID': event_id,
                        'Provider': provider,
                        'Computer': computer,
                        'Channel': channel,
                        'EventData': event_data_json
                    })
                except Exception:
                    # Skip malformed individual records
                    continue
        return temp_csv_path, None
    except Exception as e:
        return None, f"Error processing {filename}: {str(e)}"

def process_concurrently(input_dir, output_csv, max_workers=None):
    temp_dir = os.path.join(input_dir, "_temp_csvs")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    evtx_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.lower().endswith('.evtx')]
    print(f"Found {len(evtx_files)} EVTX files. Booting up {max_workers or os.cpu_count()} worker processes...")

    temp_csv_files = []

    # 1. PARSE CONCURRENTLY
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(parse_evtx_to_temp_csv, filepath, temp_dir): filepath for filepath in evtx_files}
        
        for future in concurrent.futures.as_completed(futures):
            filepath = futures[future]
            filename = os.path.basename(filepath)
            
            temp_path, error = future.result()
            if error:
                print(f"[!] {error}")
            else:
                print(f"[✓] Finished parsing: {filename}")
                temp_csv_files.append(temp_path)

    # 2. MERGE INTO SINGLE CSV
    print(f"\nMerging {len(temp_csv_files)} temporary files into {output_csv}...")
    with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=FIELDNAMES)
        writer.writeheader()
        
        for temp_file in temp_csv_files:
            with open(temp_file, 'r', encoding='utf-8') as infile:
                shutil.copyfileobj(infile, outfile)

    # 3. CLEANUP
    print("Cleaning up temporary files...")
    shutil.rmtree(temp_dir)
    print("Success! All operations completed.")

if __name__ == "__main__":
    # --- CONFIGURATION ---
    INPUT_DIRECTORY = "./evtx_files" 
    OUTPUT_FILE = "./adx_ingest_ready.csv"
    
    WORKER_CORES = None 
    
    if not os.path.exists(INPUT_DIRECTORY):
        os.makedirs(INPUT_DIRECTORY)
        print(f"Created directory '{INPUT_DIRECTORY}'. Please put your EVTX files there and run again.")
    else:
        process_concurrently(INPUT_DIRECTORY, OUTPUT_FILE, max_workers=WORKER_CORES)
