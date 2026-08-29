from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd
import pytest

from nba_pipeline.contracts import TABLE_SPECS
from nba_pipeline.model_validation import validate_model, validate_run
from nba_pipeline.pipeline import run_pipeline
from nba_pipeline.transform import convert_column, transform_table
from tests.fixture_factory import synthetic_rows, write_synthetic_fixture


def test_fixture_pipeline_reconciles_and_derives(tmp_path: Path) -> None:
    raw = write_synthetic_fixture(tmp_path / "raw")
    outcome = run_pipeline(raw, tmp_path / "run", tmp_path / "evidence")
    manifest = json.loads(outcome.manifest_path.read_text(encoding="utf-8"))
    reconciliation = json.loads(outcome.reconciliation_path.read_text(encoding="utf-8"))

    assert manifest["status"] == "passed"
    assert manifest["totals"] == {
        "input_rows": 7,
        "accepted_source_rows": 7,
        "generated_rows": 0,
        "output_rows": 7,
        "rejected_rows": 0,
    }
    assert set(reconciliation["cross_table_checks"].values()) == {0}
    fact = pd.read_csv(outcome.run_dir / "data" / "fact_game.csv")
    profile = pd.read_csv(outcome.run_dir / "data" / "dim_player_profile.csv")
    assert fact.loc[0, "season_year"] == 2020
    assert fact.loc[0, "season_stage"] == "Regular Season"
    assert profile.loc[0, "height_inches"] == 78
    assert profile.loc[0, "height_cm"] == pytest.approx(198.12)
    assert pd.isna(profile.loc[0, "draft_year"])
    validate_run(outcome.run_dir)


def test_duplicate_primary_key_is_quarantined(tmp_path: Path) -> None:
    raw = write_synthetic_fixture(tmp_path / "raw")
    path = raw / TABLE_SPECS["game"].source_file
    rows = synthetic_rows()["game"] * 2
    with path.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(TABLE_SPECS["game"].input_columns))
        writer.writeheader()
        writer.writerows(rows)

    result = transform_table(path, TABLE_SPECS["game"])
    assert len(result.accepted) == 1
    assert len(result.rejected) == 1
    assert result.rejected.loc[0, "_reject_reasons"] == "duplicate_primary_key"


def test_invalid_numeric_is_rejected_without_silent_coercion(tmp_path: Path) -> None:
    raw = write_synthetic_fixture(tmp_path / "raw")
    path = raw / TABLE_SPECS["game"].source_file
    rows = synthetic_rows()["game"]
    rows[0]["min"] = "not-a-number"
    with path.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(TABLE_SPECS["game"].input_columns))
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match=r"100 % de game\.min"):
        transform_table(path, TABLE_SPECS["game"])


def test_missing_column_fails_contract(tmp_path: Path) -> None:
    raw = write_synthetic_fixture(tmp_path / "raw")
    path = raw / TABLE_SPECS["player"].source_file
    path.write_text(
        "id,full_name,first_name,last_name\n10,Test Player,Test,Player\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="is_active"):
        transform_table(path, TABLE_SPECS["player"])


def test_run_directory_cannot_be_overwritten(tmp_path: Path) -> None:
    raw = write_synthetic_fixture(tmp_path / "raw")
    run_dir = tmp_path / "run"
    run_pipeline(raw, run_dir)
    with pytest.raises(FileExistsError):
        run_pipeline(raw, run_dir)


def test_boolean_domain_and_fractional_integer_conversion() -> None:
    integer = TABLE_SPECS["player"].columns[0]
    converted, invalid = convert_column(pd.Series(["10", "10.5"]), integer)
    assert converted.iloc[0] == 10
    assert pd.isna(converted.iloc[1])
    assert invalid.tolist() == [False, True]


def test_static_model_matches_contract_and_local_sql() -> None:
    result = validate_model()
    assert result == {"powerbi_objects": 15, "contract_version": "1.0.0"}
