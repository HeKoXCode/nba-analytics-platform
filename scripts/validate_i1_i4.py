"""Validate committed NBA-I1 through NBA-I4 evidence and deliverables."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "NBA-I1-I4" / "real-run-lf"
SQL_EVIDENCE = ROOT / "evidence" / "NBA-I1-I4" / "ci-sql" / "sql_reconciliation.json"
PBIT = ROOT / "CODE" / "Dashboard - POWERBI" / "Analisis_NBA_BestTeam.pbit"
PROJECT = ROOT / "CODE" / "Dashboard - POWERBI" / "Analisis_NBA_BestTeam"
EXPECTED_TOTALS = {
    "input_rows": 161_111,
    "accepted_source_rows": 160_956,
    "generated_rows": 53,
    "output_rows": 161_009,
    "rejected_rows": 155,
}
EXPECTED_PAGES = {
    "Inicio": 0,
    "Historia y evolución": 1,
    "Eficiencia y consistencia": 2,
    "Talento y perfil": 3,
    "Rachas y actualidad": 4,
    "Metodología y cierre": 5,
}
EXPECTED_PBIT = {
    "bytes": 6_374_566,
    "sha256": "18B49F8F2EE420D470358F08A08504C82EAB2CD34040ADD6A5D96756058478F5",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_evidence() -> dict:
    manifest = read_json(EVIDENCE / "manifest.json")
    reconciliation = read_json(EVIDENCE / "reconciliation.json")
    snapshot = read_json(EVIDENCE / "contract_snapshot.json")
    require(manifest["status"] == "passed", "Real-run manifest is not passed")
    require(manifest["schema_version"] == "1.0.0", "Unexpected schema version")
    require(manifest["totals"] == EXPECTED_TOTALS, "Real-run totals changed")
    require(sum(item["bytes"] for item in manifest["inputs"]) == 30_638_984, "Input bytes changed")
    require(sum(item["rows"] for item in manifest["inputs"]) == 161_111, "Input rows changed")
    require(set(reconciliation["cross_table_checks"].values()) == {0}, "Cross-table orphan found")
    require(snapshot["schema_version"] == manifest["schema_version"], "Contract snapshot mismatch")
    require(
        (EVIDENCE / "run.log.jsonl").read_text(encoding="utf-8").count("\n") == 9,
        "Structured real-run log is incomplete",
    )
    return manifest


def validate_model_files() -> None:
    contract = ROOT / "contracts" / "schema_v1.0.0.json"
    dictionary = ROOT / "DOCS" / "canonical_data_dictionary.md"
    require(
        contract.is_file() and contract.stat().st_size > 100_000, "Contract is absent or incomplete"
    )
    require(
        dictionary.is_file() and "dim_team" in dictionary.read_text(encoding="utf-8"),
        "Dictionary missing",
    )
    require((ROOT / "DOCS" / "data_model.md").is_file(), "ERD is missing")

    analytics = (ROOT / "CODE" / "SQL" / "20_analytics_views.sql").read_text(encoding="utf-8")
    require("analytics.dim_season" in analytics, "dim_season is missing")
    require("analytics.vw_bridge_team_season" in analytics, "team-season bridge is missing")
    require(not re.search(r"(?im)^\s*DELETE\s+FROM", analytics), "Analytics SQL deletes data")

    tables = sorted((PROJECT / "Model" / "tables").glob("*.tmdl"))
    require(len(tables) == 15, "Power BI does not expose 15 TMDL objects")
    for path in tables:
        text = path.read_text(encoding="utf-8")
        require('Sql.Databases("localhost,1433")' in text, f"Non-portable source: {path.name}")
        require("100.74.116.125" not in text, f"Former personal host remains: {path.name}")

    sql_evidence = read_json(SQL_EVIDENCE)
    require(sql_evidence["status"] == "passed", "CI SQL load is not passed")
    require(sum(sql_evidence["inserted_rows"].values()) == 161_009, "SQL loaded rows changed")
    require(
        sql_evidence["powerbi_contract"] == {"columns": 65, "objects": 15},
        "SQL/Power BI contract changed",
    )
    require(
        set(sql_evidence["reconciliation"]["integrity"].values()) == {0}, "SQL integrity failed"
    )
    require(
        sql_evidence["reconciliation"]["kpis"]["team_game_rows"] == 131_284,
        "Team-game grain changed",
    )


def validate_report() -> None:
    sections = PROJECT / "Report" / "sections"
    pages = {
        read_json(path / "section.json")["displayName"]: read_json(path / "section.json")["ordinal"]
        for path in sections.iterdir()
        if path.is_dir()
    }
    require(pages == EXPECTED_PAGES, f"Unexpected report pages: {pages}")
    report_text = "\n".join(
        path.read_text(encoding="utf-8") for path in (PROJECT / "Report").rglob("*.json")
    )
    for required in (
        "1946–2022",
        "2013–2022",
        "30.638.984 bytes",
        "155 duplicados",
        "Última validación integral",
    ):
        require(required in report_text, f"Report methodology/title evidence missing: {required}")

    require(PBIT.stat().st_size == EXPECTED_PBIT["bytes"], "PBIT byte size changed")
    digest = hashlib.sha256(PBIT.read_bytes()).hexdigest().upper()
    require(digest == EXPECTED_PBIT["sha256"], "PBIT SHA-256 changed")
    with zipfile.ZipFile(PBIT) as archive:
        require(archive.testzip() is None, "PBIT ZIP contains a corrupt member")
        names = set(archive.namelist())
        require(
            {"Report/Layout", "DataModelSchema", "[Content_Types].xml"} <= names,
            "PBIT parts missing",
        )
        layout = json.loads(archive.read("Report/Layout").decode("utf-16"))
    compiled_pages = {page["displayName"]: page["ordinal"] for page in layout["sections"]}
    require(compiled_pages == EXPECTED_PAGES, "Compiled PBIT pages do not match source")


def validate_automation() -> None:
    workflow = (ROOT / ".github" / "workflows" / "i1-i4-verification.yml").read_text(
        encoding="utf-8"
    )
    for required in ("requirements-dev.lock", "pytest", "transform", "load-sql", "validate-model"):
        require(required in workflow, f"CI does not exercise: {required}")


def main() -> int:
    try:
        manifest = validate_evidence()
        validate_model_files()
        validate_report()
        validate_automation()
    except (AssertionError, KeyError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=True))
        return 1
    print(
        json.dumps(
            {
                "status": "passed",
                "run_id": manifest["run_id"],
                "input_rows": manifest["totals"]["input_rows"],
                "output_rows": manifest["totals"]["output_rows"],
                "rejected_rows": manifest["totals"]["rejected_rows"],
                "powerbi_pages": len(EXPECTED_PAGES),
                "pbit_sha256": EXPECTED_PBIT["sha256"],
            },
            ensure_ascii=True,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
