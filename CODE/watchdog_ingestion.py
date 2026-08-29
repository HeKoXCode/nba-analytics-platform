"""Compatibility launcher for the package watch command.

Prefer ``python -m nba_pipeline watch``. This file remains so existing shortcuts do
not silently execute the obsolete row-by-row loader.
"""

from pathlib import Path

from nba_pipeline.cli import main

ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    raise SystemExit(
        main(
            [
                "watch",
                "--input-dir",
                str(Path(__file__).resolve().parent / "data_raw"),
                "--runs-dir",
                str(ROOT / ".artifacts" / "watch"),
            ]
        )
    )
