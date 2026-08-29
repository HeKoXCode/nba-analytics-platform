"""End-to-end transformation orchestration and evidence generation."""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
import uuid
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import pandas as pd
import psutil

from nba_pipeline import __version__
from nba_pipeline.contracts import SCHEMA_VERSION, TABLE_SPECS, contract_bundle
from nba_pipeline.transform import TransformResult, transform_table
from nba_pipeline.utils import JsonLogger, iso_utc, sha256_file, write_json


@dataclass(frozen=True)
class PipelineOutcome:
    run_id: str
    run_dir: Path
    manifest_path: Path
    reconciliation_path: Path
    output_rows: int
    rejected_rows: int


def _file_record(
    path: Path, *, rows: int | None = None, relative_to: Path | None = None
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "file": path.relative_to(relative_to).as_posix() if relative_to else path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if rows is not None:
        record["rows"] = rows
    return record


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(
        path,
        index=False,
        encoding="utf-8-sig",
        lineterminator="\n",
        na_rep="",
    )


def _best_team_labels(results: dict[str, TransformResult]) -> dict[int, dict[str, Any]]:
    labels: dict[int, dict[str, Any]] = {}

    def remember(
        team_id: Any, *, name: Any = None, abbreviation: Any = None, city: Any = None
    ) -> None:
        if pd.isna(team_id):
            return
        key = int(team_id)
        current = labels.setdefault(key, {})
        for field, value in (("full_name", name), ("abbreviation", abbreviation), ("city", city)):
            if value is not None and not pd.isna(value) and str(value).strip():
                current.setdefault(field, str(value).strip())

    game = results["game"].accepted
    for side in ("home", "away"):
        for row in game[
            [f"team_id_{side}", f"team_name_{side}", f"team_abbreviation_{side}"]
        ].itertuples(index=False):
            remember(row[0], name=row[1], abbreviation=row[2])

    other = results["other_stats"].accepted
    for side in ("home", "away"):
        for row in other[
            [f"team_id_{side}", f"team_abbreviation_{side}", f"team_city_{side}"]
        ].itertuples(index=False):
            remember(row[0], abbreviation=row[1], city=row[2])

    profile = results["common_player_info"].accepted
    for row in profile[["team_id", "team_name", "team_abbreviation", "team_city"]].itertuples(
        index=False
    ):
        remember(row[0], name=row[1], abbreviation=row[2], city=row[3])
    return labels


def _add_historical_team_placeholders(results: dict[str, TransformResult]) -> int:
    dimension = results["team"].accepted
    known = set(int(value) for value in dimension["team_id"].dropna().tolist())
    labels = _best_team_labels(results)
    missing = sorted(set(labels) - known)
    if not missing:
        return 0

    rows = []
    for team_id in missing:
        label = labels[team_id]
        if team_id == 0:
            full_name = "No current team"
            abbreviation = "N/A"
        else:
            full_name = label.get("full_name", f"Historical team {team_id}")
            abbreviation = label.get("abbreviation", f"H{team_id}")
        rows.append(
            {
                "team_id": team_id,
                "full_name": full_name,
                "abbreviation": abbreviation,
                "nickname": pd.NA,
                "city": label.get("city", pd.NA),
                "state": pd.NA,
                "year_founded": pd.NA,
                "is_historical_unmapped": True,
            }
        )
    placeholders = pd.DataFrame(rows).astype(
        {
            "team_id": "Int64",
            "full_name": "string",
            "abbreviation": "string",
            "nickname": "string",
            "city": "string",
            "state": "string",
            "year_founded": "Int64",
            "is_historical_unmapped": "boolean",
        }
    )
    results["team"].accepted = (
        pd.concat([dimension, placeholders], ignore_index=True)
        .sort_values("team_id", kind="stable")
        .reset_index(drop=True)
    )
    results["team"].metrics["generated_rows"] = len(placeholders)
    results["team"].metrics["output_rows"] = len(results["team"].accepted)
    return len(placeholders)


def _validate_cross_table_integrity(results: dict[str, TransformResult]) -> dict[str, int]:
    games = set(int(value) for value in results["game"].accepted["game_id"])
    players = set(int(value) for value in results["player"].accepted["player_id"])
    teams = set(int(value) for value in results["team"].accepted["team_id"])

    summary_orphans = (
        set(int(value) for value in results["game_summary"].accepted["game_id"]) - games
    )
    other_orphans = set(int(value) for value in results["other_stats"].accepted["game_id"]) - games
    profile_player_orphans = (
        set(int(value) for value in results["common_player_info"].accepted["player_id"]) - players
    )

    observed_teams: set[int] = set()
    for table_name in ("game", "other_stats"):
        frame = results[table_name].accepted
        observed_teams.update(int(value) for value in frame["team_id_home"].dropna())
        observed_teams.update(int(value) for value in frame["team_id_away"].dropna())
    observed_teams.update(
        int(value) for value in results["common_player_info"].accepted["team_id"].dropna()
    )
    team_orphans = observed_teams - teams

    checks = {
        "game_summary_without_game": len(summary_orphans),
        "other_stats_without_game": len(other_orphans),
        "player_profile_without_player": len(profile_player_orphans),
        "observed_team_without_dimension": len(team_orphans),
    }
    if any(checks.values()):
        raise ValueError(f"Integridad referencial incumplida: {checks}")
    return checks


def _copy_evidence(source_dir: Path, evidence_dir: Path) -> None:
    if evidence_dir.exists():
        raise FileExistsError(
            f"El directorio de evidencia ya existe; use una ruta nueva: {evidence_dir}"
        )
    evidence_dir.mkdir(parents=True)
    for name in (
        "manifest.json",
        "reconciliation.json",
        "input_manifest.json",
        "contract_snapshot.json",
        "run.log.jsonl",
    ):
        shutil.copy2(source_dir / name, evidence_dir / name)


def run_pipeline(
    input_dir: Path, run_dir: Path, evidence_dir: Path | None = None
) -> PipelineOutcome:
    input_dir = input_dir.resolve()
    run_dir = run_dir.resolve()
    evidence_dir = evidence_dir.resolve() if evidence_dir else None
    if not input_dir.is_dir():
        raise FileNotFoundError(f"No existe el directorio de entrada: {input_dir}")
    if run_dir.exists():
        raise FileExistsError(f"El directorio de ejecución ya existe: {run_dir}")

    expected = {spec.source_file for spec in TABLE_SPECS.values()}
    actual = {path.name for path in input_dir.glob("*_raw.csv")}
    if actual != expected:
        raise ValueError(
            f"Se requieren exactamente seis CSV: missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )

    started = datetime.now(UTC)
    input_digest = "".join(sha256_file(input_dir / name) for name in sorted(expected))
    run_id = f"nba-{started.strftime('%Y%m%dT%H%M%SZ')}-{input_digest[:10].lower()}"
    staging = run_dir.with_name(f".{run_dir.name}.staging-{uuid.uuid4().hex}")
    staging.mkdir(parents=True)
    process = psutil.Process(os.getpid())
    peak_rss = process.memory_info().rss
    started_perf = perf_counter()

    try:
        with ExitStack() as stack:
            log_stream = stack.enter_context(
                (staging / "run.log.jsonl").open("w", encoding="utf-8", newline="\n")
            )
            logger = JsonLogger(log_stream, run_id)
            logger.emit("pipeline_started", schema_version=SCHEMA_VERSION, input_files=6)

            input_records = []
            results: dict[str, TransformResult] = {}
            for name, spec in TABLE_SPECS.items():
                path = input_dir / spec.source_file
                result = transform_table(path, spec)
                results[name] = result
                input_records.append(_file_record(path, rows=result.metrics["input_rows"]))
                peak_rss = max(peak_rss, process.memory_info().rss)
                logger.emit(
                    "table_transformed",
                    table=name,
                    input_rows=result.metrics["input_rows"],
                    accepted_rows=result.metrics["accepted_source_rows"],
                    rejected_rows=result.metrics["rejected_rows"],
                )

            generated_teams = _add_historical_team_placeholders(results)
            cross_checks = _validate_cross_table_integrity(results)
            logger.emit(
                "cross_table_integrity_passed",
                generated_team_placeholders=generated_teams,
                **cross_checks,
            )

            output_records: list[dict[str, Any]] = []
            reject_records: list[dict[str, Any]] = []
            reconciliation: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "run_id": run_id,
                "tables": {},
                "cross_table_checks": cross_checks,
            }
            for name in TABLE_SPECS:
                result = results[name]
                output_path = staging / "data" / f"{result.output_name}.csv"
                reject_path = staging / "rejects" / f"{name}_rejected.csv"
                _write_csv(result.accepted, output_path)
                _write_csv(result.rejected, reject_path)
                output_records.append(
                    _file_record(
                        output_path,
                        rows=len(result.accepted),
                        relative_to=staging,
                    )
                )
                reject_records.append(
                    _file_record(
                        reject_path,
                        rows=len(result.rejected),
                        relative_to=staging,
                    )
                )
                reconciliation["tables"][name] = result.metrics
                if (
                    result.metrics["input_rows"]
                    != result.metrics["accepted_source_rows"] + result.metrics["rejected_rows"]
                ):
                    raise AssertionError(f"Reconciliación de filas inválida: {name}")

            elapsed = perf_counter() - started_perf
            finished = datetime.now(UTC)
            manifest = {
                "schema_version": SCHEMA_VERSION,
                "pipeline_version": __version__,
                "run_id": run_id,
                "status": "passed",
                "started_at_utc": iso_utc(started),
                "finished_at_utc": iso_utc(finished),
                "duration_seconds": round(elapsed, 3),
                "python": platform.python_version(),
                "pandas": pd.__version__,
                "platform": platform.platform(),
                "peak_rss_bytes": peak_rss,
                "inputs": sorted(input_records, key=lambda item: item["file"]),
                "outputs": sorted(output_records, key=lambda item: item["file"]),
                "rejects": sorted(reject_records, key=lambda item: item["file"]),
                "totals": {
                    "input_rows": sum(item.metrics["input_rows"] for item in results.values()),
                    "accepted_source_rows": sum(
                        item.metrics["accepted_source_rows"] for item in results.values()
                    ),
                    "generated_rows": sum(
                        item.metrics["generated_rows"] for item in results.values()
                    ),
                    "output_rows": sum(len(item.accepted) for item in results.values()),
                    "rejected_rows": sum(len(item.rejected) for item in results.values()),
                },
            }
            write_json(
                staging / "input_manifest.json", {"run_id": run_id, "inputs": manifest["inputs"]}
            )
            write_json(staging / "reconciliation.json", reconciliation)
            write_json(staging / "manifest.json", manifest)
            write_json(staging / "contract_snapshot.json", contract_bundle())
            logger.emit("pipeline_passed", **manifest["totals"], duration_seconds=round(elapsed, 3))

        run_dir.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staging, run_dir)
        if evidence_dir:
            _copy_evidence(run_dir, evidence_dir)
        return PipelineOutcome(
            run_id=run_id,
            run_dir=run_dir,
            manifest_path=run_dir / "manifest.json",
            reconciliation_path=run_dir / "reconciliation.json",
            output_rows=manifest["totals"]["output_rows"],
            rejected_rows=manifest["totals"]["rejected_rows"],
        )
    except Exception:
        if staging.exists():
            failure = {
                "status": "failed",
                "run_id": run_id,
                "failed_at_utc": iso_utc(),
                "error": f"{sys.exc_info()[0].__name__}: {sys.exc_info()[1]}",
            }
            write_json(staging / "failure.json", failure)
        raise


def load_manifest(run_dir: Path) -> dict[str, Any]:
    return json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
