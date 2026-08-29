"""Small, deterministic and explicitly synthetic six-table fixture."""

from __future__ import annotations

import csv
from pathlib import Path

from nba_pipeline.contracts import TABLE_SPECS, ColumnSpec, TableSpec


def _value(column: ColumnSpec) -> str:
    if column.allowed:
        return str(column.allowed[0])
    if column.nullable:
        return ""
    if column.dtype == "string":
        return "Synthetic"
    if column.dtype in {"integer", "float"}:
        return str(column.minimum if column.minimum is not None else 1)
    if column.dtype == "boolean":
        return "0"
    if column.dtype == "date":
        return "2020-01-01"
    raise AssertionError(column)


def _base(spec: TableSpec) -> dict[str, str]:
    return {column.name: _value(column) for column in spec.columns}


def synthetic_rows() -> dict[str, list[dict[str, str]]]:
    player = _base(TABLE_SPECS["player"])
    player.update(id="10", full_name="Test Player", first_name="Test", last_name="Player")

    profile = _base(TABLE_SPECS["common_player_info"])
    profile.update(
        person_id="10",
        first_name="Test",
        last_name="Player",
        display_first_last="Test Player",
        display_last_comma_first="Player, Test",
        display_fi_last="T. Player",
        player_slug="test-player",
        birthdate="2000-01-01",
        last_affiliation="Synthetic University",
        height="6-6",
        weight="210",
        season_exp="2",
        rosterstatus="Active",
        team_id="1",
        team_name="Test Home",
        team_abbreviation="THM",
        team_city="Test City",
        draft_year="Undrafted",
    )

    home = _base(TABLE_SPECS["team"])
    home.update(
        id="1", full_name="Test Home", abbreviation="THM", city="Test City", year_founded="2000"
    )
    away = _base(TABLE_SPECS["team"])
    away.update(
        id="2", full_name="Test Away", abbreviation="TAW", city="Away City", year_founded="2001"
    )

    game = _base(TABLE_SPECS["game"])
    game.update(
        season_id="22020",
        team_id_home="1",
        team_abbreviation_home="THM",
        team_name_home="Test Home",
        game_id="100",
        game_date="2020-01-01",
        matchup_home="THM vs. TAW",
        wl_home="W",
        min="240",
        pts_home="110",
        fg_pct_home="0.50",
        tov_home="10",
        team_id_away="2",
        team_abbreviation_away="TAW",
        team_name_away="Test Away",
        matchup_away="TAW @ THM",
        wl_away="L",
        pts_away="100",
        fg_pct_away="0.45",
        tov_away="12",
        season_type="Regular Season",
    )

    summary = _base(TABLE_SPECS["game_summary"])
    summary.update(
        game_date_est="2020-01-01",
        game_id="100",
        game_status_id="3",
        gamecode="20200101/TAWTHM",
        home_team_id="1",
        visitor_team_id="2",
        season="2020",
        live_period="4",
        wh_status="1",
    )

    other = _base(TABLE_SPECS["other_stats"])
    other.update(
        game_id="100",
        league_id="0",
        team_id_home="1",
        team_abbreviation_home="THM",
        team_city_home="Test City",
        pts_paint_home="44",
        team_id_away="2",
        team_abbreviation_away="TAW",
        team_city_away="Away City",
        pts_paint_away="40",
    )
    return {
        "common_player_info": [profile],
        "game": [game],
        "game_summary": [summary],
        "other_stats": [other],
        "player": [player],
        "team": [home, away],
    }


def write_synthetic_fixture(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for name, rows in synthetic_rows().items():
        spec = TABLE_SPECS[name]
        with (directory / spec.source_file).open("w", encoding="utf-8-sig", newline="") as target:
            writer = csv.DictWriter(
                target, fieldnames=list(spec.input_columns), lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(rows)
    return directory
