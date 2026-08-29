"""Compatibility entry point for the reproducible package pipeline."""

from datetime import UTC, datetime
from pathlib import Path

from nba_pipeline.cli import main

CODE_DIR = Path(__file__).resolve().parent
ROOT = CODE_DIR.parent


if __name__ == "__main__":
    stamp = datetime.now(UTC).strftime("manual-%Y%m%dT%H%M%SZ")
    raise SystemExit(
        main(
            [
                "transform",
                "--input-dir",
                str(CODE_DIR / "data_raw"),
                "--run-dir",
                str(ROOT / ".artifacts" / stamp),
            ]
        )
    )
