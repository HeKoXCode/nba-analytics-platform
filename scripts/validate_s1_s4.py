"""Validate the evidence and remediation delivered in NBA-S1 through NBA-S4."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POWERBI = ROOT / "CODE" / "Dashboard - POWERBI"
PROJECT = POWERBI / "Analisis_NBA_BestTeam"
PBIT = POWERBI / "Analisis_NBA_BestTeam.pbit"
EXPECTED_RAW_BYTES = 30_638_984
EXPECTED_OUTPUTS = {
    "common_player_info_final",
    "game_final",
    "game_summary_final",
    "other_stats_final",
    "player_final",
    "team_final",
}
EXPECTED_PAGES = {
    "Inicio": 0,
    "Análisis_1": 1,
    "Análisis_2": 2,
    "Análisis_3": 3,
    "Insights": 4,
    "Conclusión": 5,
}


class Check:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.passes = 0

    def require(self, condition: bool, message: str) -> None:
        if condition:
            self.passes += 1
        else:
            self.failures.append(message)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def walk(value: object):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def validate_documentation(check: Check) -> None:
    readme = read(ROOT / "README.md")
    check.require("30,638,984" in readme, "README lacks the verified raw-byte total")
    check.require("2.31 GB" in readme, "README lacks the separately identified source-folder volume")
    check.require(not re.search(r"22\s*GB", readme, re.I), "README still claims a 22 GB processed dataset")
    check.require("fully reproducible" not in readme.lower(), "README still claims full reproducibility")
    check.require("DOCS/raw_data_download.md" in readme, "README does not link the actual source note")
    check.require("Analisis_NBA_BestTeam.pbit" in readme, "README does not identify the cleaned PBIT")

    joined_docs = "\n".join(
        read(path)
        for path in (
            ROOT / "README.md",
            ROOT / "CODE" / "README.md",
            ROOT / "DOCS" / "technical_documentation.md",
        )
    )
    for output in EXPECTED_OUTPUTS:
        check.require(output in joined_docs, f"Canonical output is undocumented: {output}")

    check.require((ROOT / "DOCS" / "security_review.md").exists(), "S2 security review is missing")
    security = read(ROOT / "DOCS" / "security_review.md").lower()
    check.require("rotate" in security or "rotar" in security, "Security review omits credential rotation")
    check.require("history" in security or "historial" in security, "Security review omits Git-history risk")

    contributors = read(ROOT / "CONTRIBUTORS.md")
    for name in ("Percy", "Lucas Roca", "HeKoXCode"):
        check.require(name in contributors, f"Contributor evidence is missing: {name}")

    notebook = json.loads(read(ROOT / "CODE" / "Preguntas.ipynb"))
    notebook_text = json.dumps(notebook, ensure_ascii=False)
    check.require("Lucas Roca" in notebook_text, "Notebook does not preserve Lucas Roca attribution")
    check.require("HeKoXCode" in notebook_text, "Notebook does not identify S1-S4 maintenance")


def validate_data_scope(check: Check) -> None:
    files = sorted((ROOT / "CODE" / "data_raw").glob("*_raw.csv"))
    check.require(len(files) == 6, f"Expected 6 versioned raw CSV files, found {len(files)}")
    check.require(sum(path.stat().st_size for path in files) == EXPECTED_RAW_BYTES, "Raw CSV byte total changed")


def validate_security(check: Check) -> None:
    watchdog_path = ROOT / "CODE" / "watchdog_ingestion.py"
    watchdog = read(watchdog_path)
    ast.parse(watchdog, filename=str(watchdog_path))
    for variable in ("NBA_SQL_SERVER", "NBA_SQL_DATABASE", "NBA_SQL_USER", "NBA_SQL_PASSWORD"):
        check.require(variable in watchdog, f"Watchdog does not use {variable}")
    for forbidden in ("PCLUCAS", "SQL_CONFIG =", '"PASSWORD":', "'PASSWORD':"):
        check.require(forbidden not in watchdog, f"Watchdog still contains fixed configuration: {forbidden}")

    env_lines = {
        key: value
        for line in read(ROOT / "CODE" / ".env.example").splitlines()
        if line and not line.startswith("#") and "=" in line
        for key, value in (line.split("=", 1),)
    }
    check.require(env_lines.get("NBA_SQL_USER") == "", ".env.example contains a SQL username")
    check.require(env_lines.get("NBA_SQL_PASSWORD") == "", ".env.example contains a SQL password")

    audit_log = read(ROOT / "CODE" / "etl_audit_log.txt")
    check.require(not re.search(r"[A-Za-z]:\\Users\\", audit_log), "Audit log contains a personal Windows path")
    check.require("/Users/" not in audit_log, "Audit log contains a personal POSIX path")

    project_text = "\n".join(
        read(path)
        for path in PROJECT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".json", ".tmdl", ".txt"}
    )
    check.require("PCLUCAS" not in project_text.upper(), "Power BI source exposes the former local SQL host")
    check.require(not re.search(r"[A-Za-z]:\\Users\\", project_text), "Power BI source contains a personal path")


def validate_powerbi_source(check: Check) -> None:
    ast.parse(read(ROOT / "scripts" / "update_powerbi_project_s4.py"), filename="update_powerbi_project_s4.py")
    check.require((PROJECT / ".pbixproj.json").exists(), "Versionable Power BI project is missing")

    json_files = sorted(PROJECT.rglob("*.json"))
    payloads: list[object] = []
    for path in json_files:
        try:
            payloads.append(json.loads(read(path)))
        except json.JSONDecodeError as exc:
            check.failures.append(f"Invalid JSON: {path.relative_to(ROOT)} ({exc})")
    check.require(len(json_files) >= 850, f"Power BI extraction looks incomplete: {len(json_files)} JSON files")

    sections = PROJECT / "Report" / "sections"
    page_dirs = sorted(path for path in sections.iterdir() if path.is_dir())
    check.require(len(page_dirs) == 6, f"Expected 6 extracted report pages, found {len(page_dirs)}")
    check.require(not any("Duplicado" in path.name for path in page_dirs), "Duplicate conclusion page remains")

    page_state: dict[str, int] = {}
    for path in page_dirs:
        section = json.loads(read(path / "section.json"))
        page_state[section["displayName"]] = section["ordinal"]
    check.require(page_state == EXPECTED_PAGES, f"Unexpected extracted page order: {page_state}")

    nodes = [node for payload in payloads for node in walk(payload)]
    slicers = [
        node
        for node in nodes
        if isinstance(node, dict)
        and isinstance(node.get("singleVisual"), dict)
        and node["singleVisual"].get("visualType") == "slicer"
    ]
    check.require(len(slicers) == 4, f"Expected 4 built-in dropdown slicers, found {len(slicers)}")
    source_text = "\n".join(json.dumps(payload, ensure_ascii=False) for payload in payloads)
    check.require("advancedSlicerVisual" not in source_text, "Custom advanced slicer remains in source")
    check.require(source_text.count("'Dropdown'") == 8, "Not every converted slicer has dropdown configuration")

    forbidden_claims = (
        "ingresos deportivos/futuros playoffs",
        "garantiza retorno",
        "menor riesgo para el inversor",
        "estilo exportable/mercadeable",
        "mejor potencial de inversión deportiva",
        "modelo que gane siempre",
    )
    lowered = source_text.lower()
    for claim in forbidden_claims:
        check.require(claim.lower() not in lowered, f"Unsupported claim remains in Power BI source: {claim}")
    for emoji in ("📊", "💡", "🏀", "🌠", "🏆", "🔥", "🎯"):
        check.require(emoji not in source_text, f"Decorative emoji remains in Power BI source: {emoji}")

    for page in ("004_Insights", "006_Conclusión"):
        config = json.loads(read(sections / page / "config.json"))
        backgrounds = config.get("objects", {}).get("background", [])
        check.require(
            all("image" not in item.get("properties", {}) for item in backgrounds),
            f"Decorative page background remains: {page}",
        )


def validate_pbit(check: Check) -> tuple[str, int]:
    check.require(PBIT.exists(), "Cleaned PBIT is missing")
    check.require(not (POWERBI / "Analisis_NBA_BestTeam.pbix").exists(), "Obsolete PBIX remains published")
    check.require(not list((ROOT / "IMAGES").glob("*.jpg")), "Obsolete dashboard screenshots remain published")
    check.require((ROOT / "IMAGES" / "README.md").exists(), "Screenshot policy is missing")

    digest = hashlib.sha256(PBIT.read_bytes()).hexdigest().upper()
    size = PBIT.stat().st_size
    verification_note = read(ROOT / "DOCS" / "s1_s4_verification.md")
    check.require(f"{size:,} bytes" in verification_note, "Verification note has a stale PBIT size")
    check.require(digest in verification_note, "Verification note has a stale PBIT SHA-256")
    try:
        with zipfile.ZipFile(PBIT) as archive:
            bad_file = archive.testzip()
            names = set(archive.namelist())
            check.require(bad_file is None, f"PBIT ZIP member is corrupt: {bad_file}")
            for member in ("Report/Layout", "DataModelSchema", "[Content_Types].xml"):
                check.require(member in names, f"PBIT lacks required member: {member}")
            raw_layout = archive.read("Report/Layout").decode("utf-16")
    except (OSError, zipfile.BadZipFile, UnicodeError) as exc:
        check.failures.append(f"PBIT cannot be inspected: {exc}")
        return digest, size

    layout = json.loads(raw_layout)
    page_state = {
        section["displayName"]: section["ordinal"]
        for section in layout["sections"]
    }
    check.require(page_state == EXPECTED_PAGES, f"Unexpected compiled PBIT page order: {page_state}")
    check.require("advancedSlicerVisual" not in raw_layout, "Compiled PBIT still contains custom advanced slicers")
    check.require(raw_layout.count(r'\"visualType\":\"slicer\"') == 4, "Compiled PBIT does not contain 4 built-in slicers")
    for claim in (
        "ingresos deportivos/futuros playoffs",
        "garantiza retorno",
        "menor riesgo para el inversor",
        "estilo exportable/mercadeable",
        "mejor potencial de inversión deportiva",
        "modelo que gane siempre",
    ):
        check.require(claim.lower() not in raw_layout.lower(), f"Unsupported claim remains in compiled PBIT: {claim}")
    return digest, size


def main() -> int:
    check = Check()
    validate_documentation(check)
    validate_data_scope(check)
    validate_security(check)
    validate_powerbi_source(check)
    digest, size = validate_pbit(check)

    if check.failures:
        print(f"FAILED: {len(check.failures)} of {check.passes + len(check.failures)} checks")
        for failure in check.failures:
            print(f"- {failure}")
        return 1

    print(f"PASS: {check.passes} NBA-S1-S4 checks")
    print(f"PBIT: {size:,} bytes | SHA256 {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
