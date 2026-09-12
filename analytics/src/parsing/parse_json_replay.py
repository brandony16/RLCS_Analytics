"""Backward-compatible entrypoint for replay parsing.

Use ``python -m src.parsing.cli`` for the explicit command-line interface.
"""

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.parsing.replay_parser import parse_and_save_replay, parse_network_frames, save_metadata

__all__ = ["parse_and_save_replay", "parse_network_frames", "save_metadata"]


if __name__ == "__main__":
    from src.parsing.cli import main

    main()
