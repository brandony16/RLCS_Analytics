# RLCS Analytics

The analytics application converts Rocket League replay JSON produced by
`rrrocket` into processed frame data and event metadata, then calculates
player statistics from those outputs.

## Process A Replay

From the `analytics` directory:

```bash
python -m src.parsing.cli data/json/replay.json
```

This writes `<match_guid>_frames.csv` and `<match_guid>_metadata.json` to
`data/processed` by default. Use `--output-dir` to choose another directory.

The shell helper still handles the full replay-to-JSON workflow:

```bash
./scripts/process_replay.sh <path-to-file>
```

## Analyze A Processed Match

```bash
python main.py <match_guid>
```

## Source Layout

```text
src/domain/          Shared parser data models
src/parsing/         Replay parsing, actor links, events, and parser CLI
src/analysis/        Boost, speed, scoreboard, and aggregate calculations
src/visualization/   Plotting and terminal output
tests/               Tests grouped by analysis or parsing responsibility
```
