#!/bin/bash

# 1. Create a timestamped subdirectory in ./output
TIMESTAMP=$(date -u +"%Y-%m-%dT%H-%M-%SZ")
OUTPUT_DIR="./runs_output/batchrun_${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"
echo "Created output directory: $OUTPUT_DIR"

# 2. Define the list of addresses to process
ADDRESSES=(
    "0x51db92258a3ab0f81de0feab5d59a77e49b57275"
    "0x3feC8fd95b122887551c19c73F6b2bbf445B8C87"
    "0x38e247893BbC8517a317c54Ed34F9C62cb5F26c0"
    "0x7a29aE65Bf25Dfb6e554BF0468a6c23ed99a8DC2"
)

# 3. Loop through each address, run the command, and redirect output
for addr in "${ADDRESSES[@]}"; do
    LOG_FILE="$OUTPUT_DIR/${addr}.log"
    echo "Processing address: $addr"
    echo "Logging output to: $LOG_FILE"
    
    # The -u flag ensures that Python's stdout is unbuffered, preserving the order of logs and prints.
    poetry run python -u -m src.cli -v "$addr" > "$LOG_FILE" 2>&1
    
    echo "Finished processing $addr"
    echo "---------------------------------"
done

echo "All addresses processed."