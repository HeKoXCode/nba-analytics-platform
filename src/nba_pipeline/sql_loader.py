"""Transactional SQL Server deployment and canonical CSV loading."""

from __future__ import annotations

import csv
import json
import os
import re
from collections.abc import Iterable
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pyodbc

from nba_pipeline.contracts import OUTPUT_SPECS, SCHEMA_VERSION, TABLE_SPECS
from nba_pipeline.model_validation import ROOT, validate_run, validate_sql_objects
from nba_pipeline.utils import iso_utc, write_json

SQL_DIR = ROOT / "CODE" / "SQL"
LOAD_ORDER = (
    "dim_team",
    "dim_player",
    "fact_game",
    "dim_player_profile",
    "fact_game_summary",
    "fact_other_stats",
)
GO_PATTERN = re.compile(r"(?im)^\s*GO\s*(?:--.*)?$")
SAFE_DATABASE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")


def required_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or not value.strip():
        raise RuntimeError(f"Falta la variable de entorno requerida: {name}")
    return value.strip()


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "si", "sí"}


def database_name() -> str:
    value = required_env("NBA_SQL_DATABASE", "NBA_Project")
    if not SAFE_DATABASE.fullmatch(value):
        raise RuntimeError("NBA_SQL_DATABASE sólo admite letras, números y guion bajo.")
    return value


def connection_string(database: str) -> str:
    driver = required_env("NBA_SQL_DRIVER", "SQL Server")
    server = required_env("NBA_SQL_SERVER", "localhost,1433")
    trusted = env_bool("NBA_SQL_TRUSTED_CONNECTION", False)
    parts = [f"DRIVER={{{driver}}}", f"SERVER={server}", f"DATABASE={database}"]
    if trusted:
        parts.append("Trusted_Connection=yes")
    else:
        parts.extend(
            [f"UID={required_env('NBA_SQL_USER')}", f"PWD={required_env('NBA_SQL_PASSWORD')}"]
        )
    parts.append(f"Encrypt={'yes' if env_bool('NBA_SQL_ENCRYPT', False) else 'no'}")
    trust_certificate = "yes" if env_bool("NBA_SQL_TRUST_SERVER_CERTIFICATE", True) else "no"
    parts.append(f"TrustServerCertificate={trust_certificate}")
    return ";".join(parts) + ";"


def connect(database: str, *, autocommit: bool = False):
    return pyodbc.connect(connection_string(database), timeout=30, autocommit=autocommit)


def read_sql(path: Path, *, database: str | None = None) -> str:
    text = path.read_text(encoding="utf-8-sig")
    return text.replace("$(NBA_DATABASE)", database) if database else text


def split_batches(text: str) -> list[str]:
    return [batch.strip() for batch in GO_PATTERN.split(text) if batch.strip()]


def execute_script(cursor, path: Path, *, database: str | None = None) -> None:
    for batch in split_batches(read_sql(path, database=database)):
        cursor.execute(batch)
        while cursor.nextset():
            pass


def _convert(value: str, dtype: str) -> Any:
    if value == "":
        return None
    if dtype == "integer":
        return int(value)
    if dtype == "float":
        return float(value)
    if dtype == "boolean":
        return value.strip().lower() in {"true", "1"}
    if dtype == "date":
        return date.fromisoformat(value)
    return value


def _utc_naive(value: str) -> datetime:
    """Convert a manifest ISO timestamp to SQL Server DATETIME2 UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(UTC).replace(tzinfo=None)


def _rows(path: Path, output_name: str) -> tuple[list[str], Iterable[tuple[Any, ...]]]:
    spec = OUTPUT_SPECS[output_name]
    column_specs = (*spec.columns, *spec.derived_columns)
    columns = [column.canonical_name for column in column_specs]

    def iterator():
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            if reader.fieldnames != columns:
                raise ValueError(f"Columnas de salida inesperadas en {path.name}")
            for row in reader:
                yield tuple(
                    _convert(row[name], column.dtype)
                    for name, column in zip(columns, column_specs, strict=True)
                )

    return columns, iterator()


def _chunks(rows: Iterable[tuple[Any, ...]], size: int = 2_000):
    chunk = []
    for row in rows:
        chunk.append(row)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def _insert_table(cursor, run_dir: Path, output_name: str) -> int:
    spec = OUTPUT_SPECS[output_name]
    path = run_dir / "data" / f"{output_name}.csv"
    columns, rows = _rows(path, output_name)
    placeholders = ", ".join("?" for _ in columns)
    column_sql = ", ".join(f"[{name}]" for name in columns)
    schema, table = spec.sql_table.split(".")
    statement = f"INSERT INTO [{schema}].[{table}] ({column_sql}) VALUES ({placeholders})"
    cursor.fast_executemany = True
    inserted = 0
    for chunk in _chunks(rows):
        cursor.executemany(statement, chunk)
        inserted += len(chunk)
    return inserted


def _reconciliation(cursor) -> dict[str, Any]:
    results = []
    for batch in split_batches(read_sql(SQL_DIR / "30_reconciliation.sql")):
        cursor.execute(batch)
        if cursor.description:
            row = cursor.fetchone()
            results.append(
                {column[0]: value for column, value in zip(cursor.description, row, strict=True)}
            )
    return {"kpis": results[0], "integrity": results[1]}


def load_sql_server(run_dir: Path, evidence_dir: Path | None = None) -> dict[str, Any]:
    run_dir = run_dir.resolve()
    evidence_dir = evidence_dir.resolve() if evidence_dir else None
    validate_run(run_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    database = database_name()

    with connect("master", autocommit=True) as master:
        execute_script(master.cursor(), SQL_DIR / "00_create_database.sql", database=database)

    inserted: dict[str, int] = {}
    with connect(database) as connection:
        cursor = connection.cursor()
        execute_script(cursor, SQL_DIR / "10_core_schema.sql")
        try:
            for output_name in reversed(LOAD_ORDER):
                schema, table = OUTPUT_SPECS[output_name].sql_table.split(".")
                cursor.execute(f"DELETE FROM [{schema}].[{table}]")
            for output_name in LOAD_ORDER:
                inserted[output_name] = _insert_table(cursor, run_dir, output_name)

            cursor.execute(
                "DELETE FROM [audit].[table_reconciliation] WHERE run_id = ?", manifest["run_id"]
            )
            cursor.execute("DELETE FROM [audit].[etl_run] WHERE run_id = ?", manifest["run_id"])
            insert_run = (
                "INSERT INTO [audit].[etl_run] "
                "(run_id, schema_version, started_at_utc, status, input_rows, output_rows, "
                "rejected_rows) VALUES (?, ?, ?, ?, ?, ?, ?)"
            )
            cursor.execute(
                insert_run,
                manifest["run_id"],
                SCHEMA_VERSION,
                _utc_naive(manifest["started_at_utc"]),
                "passed",
                manifest["totals"]["input_rows"],
                manifest["totals"]["output_rows"],
                manifest["totals"]["rejected_rows"],
            )
            reconciliation = json.loads(
                (run_dir / "reconciliation.json").read_text(encoding="utf-8")
            )
            source_by_output = {spec.output_name: source for source, spec in TABLE_SPECS.items()}
            for output_name, loaded_rows in inserted.items():
                metrics = reconciliation["tables"][source_by_output[output_name]]
                insert_reconciliation = (
                    "INSERT INTO [audit].[table_reconciliation] "
                    "(run_id, table_name, input_rows, accepted_rows, generated_rows, "
                    "rejected_rows, loaded_rows) VALUES (?, ?, ?, ?, ?, ?, ?)"
                )
                cursor.execute(
                    insert_reconciliation,
                    manifest["run_id"],
                    output_name,
                    metrics["input_rows"],
                    metrics["accepted_source_rows"],
                    metrics["generated_rows"],
                    metrics["rejected_rows"],
                    loaded_rows,
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

        execute_script(cursor, SQL_DIR / "20_analytics_views.sql")
        connection.commit()
        model_check = validate_sql_objects(cursor)
        sql_reconciliation = _reconciliation(cursor)

        expected = {
            record["file"].split("/")[-1].removesuffix(".csv"): record["rows"]
            for record in manifest["outputs"]
        }
        if inserted != {name: expected[name] for name in LOAD_ORDER}:
            raise RuntimeError(f"Las filas cargadas no coinciden con el manifiesto: {inserted}")
        kpis = sql_reconciliation["kpis"]
        integrity = sql_reconciliation["integrity"]
        if int(kpis["team_game_rows"]) != int(kpis["fact_game_rows"]) * 2:
            raise RuntimeError("La vista equipo-partido no reconcilia 2 filas por juego.")
        if int(kpis["q1_total_team_games"]) != int(kpis["team_game_rows"]):
            raise RuntimeError("La pregunta histórica no reconcilia con equipo-partido.")
        if any(int(value or 0) for value in integrity.values()):
            raise RuntimeError(f"Integridad SQL incumplida: {integrity}")

    evidence = {
        "status": "passed",
        "run_id": manifest["run_id"],
        "database": database,
        "loaded_at_utc": iso_utc(),
        "inserted_rows": inserted,
        "powerbi_contract": model_check,
        "reconciliation": sql_reconciliation,
    }
    write_json(run_dir / "sql_reconciliation.json", evidence)
    if evidence_dir:
        evidence_dir.mkdir(parents=True, exist_ok=True)
        write_json(evidence_dir / "sql_reconciliation.json", evidence)
    print(json.dumps(evidence, ensure_ascii=True, sort_keys=True, default=str))
    return evidence
