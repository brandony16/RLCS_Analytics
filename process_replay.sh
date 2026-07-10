#!/bin/bash
# Usage: ./process_replay.sh my_game.replay

REPLAY_FILE=$1
BASENAME=$(basename "$REPLAY_FILE" .replay)
JSON_FILE="data/json/${BASENAME}.json"
CSV_FILE="data/processed/${BASENAME}.csv"

echo "Processing $REPLAY_FILE..."

# Ensure directories exist
mkdir -p data/json data/processed

# 1. Run rrrocket
./rrrocket -np "$REPLAY_FILE" | Out-File -Encoding utf8 "$JSON_FILE" 2>/dev/null || ./rrrocket -np "$REPLAY_FILE" > "$JSON_FILE"

# 2. Run Python Parser
python parse_json_replay.py "$JSON_FILE" "$CSV_FILE"

echo "Done! Output: $CSV_FILE"