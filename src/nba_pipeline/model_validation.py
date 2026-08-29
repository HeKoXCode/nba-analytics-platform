"""Validate alignment between contracts, SQL views and the Power BI TMDL model."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from nba_pipeline.contracts import SCHEMA_VERSION, contract_bundle
from nba_pipeline.utils import json_bytes, sha256_file

ROOT = Path(__file__).resolve().parents[2]
MODEL_TABLES = ROOT / "CODE" / "Dashboard - POWERBI" / "Analisis_NBA_BestTeam" / "Model" / "tables"
ANALYTICS_SQL = ROOT / "CODE" / "SQL" / "20_analytics_views.sql"
CONTRACT_PATH = ROOT / "contracts" / f"schema_v{SCHEMA_VERSION}.json"


def powerbi_contract() -> dict[str, dict[str, Any]]:
    objects: dict[str, dict[str, Any]] = {}
    for path in sorted(MODEL_TABLES.glob("*.tmdl")):
        text = path.read_text(encoding="utf-8-sig")
        table_match = re.search(r"(?m)^table\s+(.+)$", text)
        object_match = re.search(r'\[Schema="([^"]+)",Item="([^"]+)"\]', text)
        if not table_match or not object_match:
            raise ValueError(f"TMDL incompleto: {path.relative_to(ROOT)}")
        table = table_match.group(1).strip().strip("'")
        columns = [
            match.group(1).strip().strip("'")
            for match in re.finditer(r"(?m)^\s*column\s+(.+)$", text)
        ]
        servers = sorted(set(re.findall(r'Sql\.Databases\("([^"]+)"\)', text)))
        objects[table] = {
            "file": path.relative_to(ROOT).as_posix(),
            "schema": object_match.group(1),
            "object": object_match.group(2),
            "columns": columns,
            "servers": servers,
        }
    return objects


def validate_run(run_dir: Path) -> None:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "passed" or manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("El manifiesto de ejecución no está aprobado o usa otro contrato.")
    for group in ("outputs", "rejects"):
        for record in manifest[group]:
            path = run_dir / record["file"]
            if not path.is_file() or path.stat().st_size != record["bytes"]:
                raise ValueError(f"Artefacto ausente o con tamaño distinto: {record['file']}")
            if sha256_file(path) != record["sha256"]:
                raise ValueError(f"Checksum inválido: {record['file']}")


def validate_static_model() -> dict[str, Any]:
    if not CONTRACT_PATH.exists() or CONTRACT_PATH.read_bytes() != json_bytes(contract_bundle()):
        raise ValueError("El contrato generado está desactualizado.")
    objects = powerbi_contract()
    if len(objects) != 15:
        raise ValueError(f"Power BI debe exponer 15 objetos; encontrados: {len(objects)}")
    sql = ANALYTICS_SQL.read_text(encoding="utf-8")
    for details in objects.values():
        if details["schema"] != "analytics":
            raise ValueError(f"Schema Power BI inesperado: {details}")
        marker = f"CREATE OR ALTER VIEW analytics.{details['object']}"
        if marker.lower() not in sql.lower():
            raise ValueError(f"El SQL no crea el objeto requerido: {details['object']}")
        if details["servers"] != ["localhost,1433"]:
            raise ValueError(
                f"Origen Power BI no portable en {details['file']}: {details['servers']}"
            )
    if re.search(r"(?im)^\s*DELETE\s+FROM\s+(?:\[?core\]?|\[?analytics\]?)", sql):
        raise ValueError("El modelo analítico contiene un borrado silencioso.")
    return {"powerbi_objects": len(objects), "contract_version": SCHEMA_VERSION}


def validate_sql_objects(cursor) -> dict[str, int]:
    objects = powerbi_contract()
    checked_columns = 0
    for details in objects.values():
        columns = ", ".join(f"[{column}]" for column in details["columns"])
        cursor.execute(f"SELECT TOP (0) {columns} FROM [{details['schema']}].[{details['object']}]")
        checked_columns += len(details["columns"])
    return {"objects": len(objects), "columns": checked_columns}


def validate_model(run_dir: Path | None = None) -> dict[str, Any]:
    result = validate_static_model()
    if run_dir:
        validate_run(run_dir.resolve())
        result["run_artifacts"] = "passed"
    print(json.dumps({"status": "passed", **result}, ensure_ascii=True, sort_keys=True))
    return result
