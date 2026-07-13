#!/usr/bin/env python3
"""Submit a frozen R5 input to the OpenAI Batch API without persisting the key."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

import r3_batch_api
import r5_crsi as r5


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "confirmatory"], required=True)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--poll-seconds", type=int, default=20)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    run_name = args.run_name or args.split
    run = project / "experiments" / r5.EXPERIMENT_ID / "api" / run_name
    key = getpass.getpass("OpenAI API key: ")
    try:
        r3_batch_api.submit_and_wait(
            api_key=key, input_path=run / "batch_input.jsonl", run_dir=run,
            metadata={"experiment": r5.EXPERIMENT_ID, "phase": run_name},
            poll_seconds=args.poll_seconds,
        )
    finally:
        key = ""
    return 0


if __name__ == "__main__":
    sys.exit(main())
