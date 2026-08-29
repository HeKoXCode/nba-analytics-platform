"""Command-line interface with explicit modes and stable exit codes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from nba_pipeline.contracts import contract_bundle
from nba_pipeline.pipeline import run_pipeline
from nba_pipeline.utils import write_json
from nba_pipeline.watch import watch_pipeline

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = REPO_ROOT / "CODE" / "data_raw"


def _path(value: str) -> Path:
    return Path(value).expanduser()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nba-etl",
        description="Contract-driven NBA Analytics ETL and SQL deployment.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    transform = subparsers.add_parser("transform", help="Transform six raw CSV files.")
    transform.add_argument("--input-dir", type=_path, default=DEFAULT_INPUT)
    transform.add_argument("--run-dir", type=_path, required=True)
    transform.add_argument("--evidence-dir", type=_path)

    watch = subparsers.add_parser("watch", help="Run an initial transform and watch for changes.")
    watch.add_argument("--input-dir", type=_path, default=DEFAULT_INPUT)
    watch.add_argument("--runs-dir", type=_path, required=True)
    watch.add_argument("--cooldown-seconds", type=float, default=15.0)
    watch.add_argument("--no-initial-load", action="store_true")

    export = subparsers.add_parser("export-contract", help="Export the full versioned contract.")
    export.add_argument("--output", type=_path, required=True)

    load = subparsers.add_parser(
        "load-sql", help="Deploy and load a completed run into SQL Server."
    )
    load.add_argument("--run-dir", type=_path, required=True)
    load.add_argument("--evidence-dir", type=_path)

    validate = subparsers.add_parser(
        "validate-model", help="Validate SQL, contract and Power BI dependencies."
    )
    validate.add_argument("--run-dir", type=_path)
    return parser


def _configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="backslashreplace")


def main(argv: list[str] | None = None) -> int:
    _configure_console()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "transform":
            outcome = run_pipeline(args.input_dir, args.run_dir, args.evidence_dir)
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "run_id": outcome.run_id,
                        "run_dir": str(outcome.run_dir),
                        "output_rows": outcome.output_rows,
                        "rejected_rows": outcome.rejected_rows,
                    },
                    ensure_ascii=True,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "watch":
            watch_pipeline(
                args.input_dir,
                args.runs_dir,
                initial_load=not args.no_initial_load,
                cooldown_seconds=args.cooldown_seconds,
            )
            return 0
        if args.command == "export-contract":
            write_json(args.output, contract_bundle())
            print(json.dumps({"status": "passed", "output": str(args.output)}))
            return 0
        if args.command == "load-sql":
            from nba_pipeline.sql_loader import load_sql_server

            load_sql_server(args.run_dir, args.evidence_dir)
            return 0
        if args.command == "validate-model":
            from nba_pipeline.model_validation import validate_model

            validate_model(args.run_dir)
            return 0
    except (FileNotFoundError, FileExistsError, ValueError, AssertionError) as exc:
        print(
            json.dumps(
                {"status": "failed", "category": "data_or_contract", "error": str(exc)},
                ensure_ascii=True,
            ),
            file=sys.stderr,
        )
        return 2
    except RuntimeError as exc:
        print(
            json.dumps(
                {"status": "failed", "category": "runtime", "error": str(exc)},
                ensure_ascii=True,
            ),
            file=sys.stderr,
        )
        return 4
    except KeyboardInterrupt:
        return 130
    parser.error(f"Comando no implementado: {args.command}")
    return 2
