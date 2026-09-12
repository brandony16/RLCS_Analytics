"""Command-line interface for converting rrrocket JSON into analytics files."""

import argparse

from src.parsing.replay_parser import parse_and_save_replay


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert an rrrocket replay JSON file into CSV and metadata."
    )
    parser.add_argument("input_json", help="Path to an rrrocket JSON replay file")
    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="Directory for generated CSV and metadata files",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    parse_and_save_replay(args.input_json, args.output_dir)


if __name__ == "__main__":
    main()
