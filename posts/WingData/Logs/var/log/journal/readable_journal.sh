#!/bin/bash

# 1. Capture the directory from the command line argument
JOURNAL_DIR="$1"
OUTPUT_FILE="readable_journal.txt"

# 2. Check if the user actually provided a directory
if [ -z "$JOURNAL_DIR" ]; then
    echo "Error: You must specify the journal directory."
    echo "Usage: ./convert_journal.sh ./var/log/journal/d7191fe43d42493b8eff7c566ecfc9a6/"
    exit 1
fi

# 3. Check if the directory actually exists
if [ ! -d "$JOURNAL_DIR" ]; then
    echo "Error: Directory '$JOURNAL_DIR' not found."
    exit 1
fi

# 4. Run the conversion
echo "Converting journals in '$JOURNAL_DIR' to text..."
journalctl -D "$JOURNAL_DIR" > "$OUTPUT_FILE"

# 5. Success message
if [ $? -eq 0 ]; then
    echo "Success! Output saved to: $OUTPUT_FILE"
    echo "Lines extracted: $(wc -l < $OUTPUT_FILE)"
else
    echo "Failed to convert journals."
fi
