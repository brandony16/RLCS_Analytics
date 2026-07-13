#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: ./scripts/process_replay.sh <path-to-replay>.replay" >&2
    exit 1
fi

REPLAY_FILE=$1

BASENAME=$(basename "$REPLAY_FILE" .replay)
JSON_FILE="data/json/${BASENAME}.json"

echo "Processing $REPLAY_FILE..."

# Ensure directories exist
mkdir -p data/json data/processed

echo "starting rrrocket parsing step"
# 1. Run rrrocket
./rrrocket -np "$REPLAY_FILE" | Out-File -Encoding utf8 "$JSON_FILE" 2>/dev/null || ./rrrocket -np "$REPLAY_FILE" > "$JSON_FILE"

echo "Finished rrrocket parsing"
echo "Starting json parsing"

# 2. Run Python Parser
python ./scripts/parse_json_replay.py "$JSON_FILE"

echo "Done!"