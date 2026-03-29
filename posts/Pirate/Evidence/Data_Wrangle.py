import pandas as pd
import re

def normalize_security_events(file_path):
    print("Loading raw logs...")
    df = pd.read_csv(file_path)
    
    # 1. Standardize Datetime
    df['datetime'] = pd.to_datetime(df['datetime'], format='mixed', utc=True)
    df['message'] = df['message'].fillna('')
    
    # 2. Extract Event ID
    df['EventID'] = df['message'].apply(
        lambda x: re.search(r'^\[(\d+)\s*/', str(x)).group(1) if re.search(r'^\[(\d+)\s*/', str(x)) else None
    )

    print("Extracting and normalizing SOC entities...")

    # 3. Robust Field Extraction (Handling escaped \\t and \\n)
    # We use a helper function that safely looks for a key and grabs the value until the next newline/slash
    def get_field(pattern, text):
        match = re.search(pattern, str(text), re.IGNORECASE)
        if match:
            # Clean up any trailing slashes or spaces
            return match.group(1).replace('\\r', '').replace('\\n', '').strip()
        return None

    # Extract Target Account (often under "Account Name" in the Object/Target section)
    # We use (?:\\t|\s)+ to catch both literal slashes and actual spaces
    df['AccountName'] = df['message'].apply(lambda x: get_field(r'Account Name:(?:\\t|\s)+([^\\]+)', x))
    
    # Extract Logon Type (Event 4624)
    df['LogonType'] = df['message'].apply(lambda x: get_field(r'Logon Type:(?:\\t|\s)+(\d+)', x))
    
    # Extract Source IP (Event 4624 / 4625)
    df['SourceIP'] = df['message'].apply(lambda x: get_field(r'Source Network Address:(?:\\t|\s)+([^\\]+)', x))
    
    # Extract Service / SPN (Event 4769 / 5136)
    df['ServiceName'] = df['message'].apply(lambda x: get_field(r'Service Name:(?:\\t|\s)+([^\\]+)', x))
    df['ModifiedSPN'] = df['message'].apply(lambda x: get_field(r'Value:(?:\\t|\s)+(HTTP/[^\\]+)', x)) # Specific to your attack

    # 4. Clean up columns and sort
    # Drop the noisy original message column if you only want the clean data, or keep it for deep dives
    clean_df = df[['datetime', 'display_name', 'EventID', 'AccountName', 'LogonType', 'SourceIP', 'ServiceName', 'ModifiedSPN', 'message']]
    clean_df = clean_df.sort_values(by='datetime', ascending=False)
    
    return clean_df

# Run it
clean_logs = normalize_security_events('detections_data.csv')
clean_logs.to_csv('normalized_soc_data.csv', index=False)
print("Data normalized and saved to normalized_soc_data.csv")
