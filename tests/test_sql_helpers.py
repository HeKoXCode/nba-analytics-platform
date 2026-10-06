from __future__ import annotations

from pathlib import Path

import pytest

from nba_pipeline.model_validation import powerbi_contract, validate_sql_objects
from nba_pipeline.sql_loader import (
    _convert,
    _utc_naive,
    connection_string,
    database_name,
    read_sql,
    split_batches,
)


def test_split_batches_and_database_replacement(tmp_path: Path) -> None:
    path = tmp_path / "test.sql"
    path.write_text("SELECT '$(NBA_DATABASE)'\nGO\nSELECT 2\n", encoding="utf-8")
    assert read_sql(path, database="NBA_Test").startswith("SELECT 'NBA_Test'")
    assert split_batches(read_sql(path)) == ["SELECT '$(NBA_DATABASE)'", "SELECT 2"]


def test_sql_scalar_conversion() -> None:
    assert _convert("", "integer") is None
    assert _convert("2", "integer") == 2
    assert _convert("2.5", "float") == 2.5
    assert _convert("true", "boolean") is True
    assert str(_convert("2020-01-01", "date")) == "2020-01-01"
    assert _convert("text", "string") == "text"
    assert str(_utc_naive("2026-08-29T00:21:54.088913Z")) == "2026-08-29 00:21:54.088913"


def test_connection_string_uses_environment_without_exposing_defaults(monkeypatch) -> None:
    monkeypatch.setenv("NBA_SQL_DRIVER", "ODBC Driver 18 for SQL Server")
    monkeypatch.setenv("NBA_SQL_SERVER", "localhost,1433")
    monkeypatch.setenv("NBA_SQL_USER", "sa")
    monkeypatch.setenv("NBA_SQL_PASSWORD", "local-test-only")
    monkeypatch.setenv("NBA_SQL_DATABASE", "NBA_Test")
    value = connection_string(database_name())
    assert "SERVER=localhost,1433" in value
    assert "DATABASE=NBA_Test" in value
    assert "UID=sa" in value
    assert "Encrypt=no" in value


def test_invalid_database_name_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("NBA_SQL_DATABASE", "NBA_Project;DROP")
    with pytest.raises(RuntimeError, match="sólo admite"):
        database_name()


def test_powerbi_display_names_keep_explicit_sql_source_columns() -> None:
    objects = powerbi_contract()
    season = objects["analytics dim_season"]
    assert season["columns"][2] == "Season decade"
    assert season["source_columns"][2] == "decade"
    recent = objects["analytics vw_q10_recent_top"]
    assert recent["columns"][2:4] == [
        "Win rate (last 10 seasons)",
        "Points per game (last 10 seasons)",
    ]
    assert recent["source_columns"][2:4] == ["win_rate_10y", "ppg_10y"]


def test_sql_contract_queries_source_aliases_not_display_names() -> None:
    class Cursor:
        statements: list[str]

        def __init__(self) -> None:
            self.statements = []

        def execute(self, statement: str) -> None:
            self.statements.append(statement)

    cursor = Cursor()
    assert validate_sql_objects(cursor) == {"objects": 15, "columns": 65}
    queries = "\n".join(cursor.statements)
    assert "[win_rate_10y]" in queries
    assert "[decade]" in queries
    assert "[Season decade]" not in queries
