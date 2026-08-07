"""Command line entry point for the supply chain pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pipeline import run_pipeline
from src.utils import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Run supply chain analytics pipeline stages.")
    parser.add_argument(
        "stage",
        choices=["generate", "ingest", "validate", "transform", "train", "optimize", "report", "all"],
        nargs="?",
        default="all",
    )
    parser.add_argument("--config", default="config/config.yaml", help="Path to YAML configuration.")
    args = parser.parse_args()
    run_pipeline(args.stage, load_config(args.config))


if __name__ == "__main__":
    main()
