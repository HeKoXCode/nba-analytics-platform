"""Versioned, explicit contracts for the six source tables and canonical outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

SCHEMA_VERSION = "1.0.0"
DEFAULT_NULL_TOKENS = ("", "nan", "none", "null", "nat")


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    dtype: str
    nullable: bool = True
    output_name: str | None = None
    allowed: tuple[Any, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    null_tokens: tuple[str, ...] = DEFAULT_NULL_TOKENS

    @property
    def canonical_name(self) -> str:
        return self.output_name or self.name


@dataclass(frozen=True)
class TableSpec:
    name: str
    source_file: str
    output_name: str
    primary_key: tuple[str, ...]
    columns: tuple[ColumnSpec, ...]
    derived_columns: tuple[ColumnSpec, ...] = ()
    description: str = ""
    sql_table: str = ""

    @property
    def input_columns(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.columns)

    @property
    def output_columns(self) -> tuple[str, ...]:
        return tuple(column.canonical_name for column in self.columns) + tuple(
            column.canonical_name for column in self.derived_columns
        )

    @property
    def output_primary_key(self) -> tuple[str, ...]:
        by_name = {column.name: column.canonical_name for column in self.columns}
        return tuple(by_name[name] for name in self.primary_key)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema_version"] = SCHEMA_VERSION
        payload["input_columns"] = [asdict(column) for column in self.columns]
        payload["output_columns"] = [
            {**asdict(column), "name": column.canonical_name}
            for column in (*self.columns, *self.derived_columns)
        ]
        payload["output_primary_key"] = list(self.output_primary_key)
        payload.pop("columns")
        payload.pop("derived_columns")
        return payload


def col(
    name: str,
    dtype: str,
    *,
    nullable: bool = True,
    output_name: str | None = None,
    allowed: tuple[Any, ...] = (),
    minimum: float | None = None,
    maximum: float | None = None,
    null_tokens: tuple[str, ...] = DEFAULT_NULL_TOKENS,
) -> ColumnSpec:
    return ColumnSpec(
        name=name,
        dtype=dtype,
        nullable=nullable,
        output_name=output_name,
        allowed=allowed,
        minimum=minimum,
        maximum=maximum,
        null_tokens=null_tokens,
    )


def string_columns(names: tuple[str, ...], *, nullable: bool = True) -> tuple[ColumnSpec, ...]:
    return tuple(col(name, "string", nullable=nullable) for name in names)


def float_columns(names: tuple[str, ...], *, nullable: bool = True) -> tuple[ColumnSpec, ...]:
    return tuple(col(name, "float", nullable=nullable) for name in names)


BOOL = (False, True)


COMMON_PLAYER_INFO = TableSpec(
    name="common_player_info",
    source_file="common_player_info_raw.csv",
    output_name="dim_player_profile",
    sql_table="core.dim_player_profile",
    primary_key=("person_id",),
    description="Player biography and roster attributes; one optional profile per player.",
    columns=(
        col("person_id", "integer", nullable=False, output_name="player_id", minimum=1),
        col("first_name", "string"),
        *string_columns(
            (
                "last_name",
                "display_first_last",
                "display_last_comma_first",
                "display_fi_last",
                "player_slug",
            ),
            nullable=False,
        ),
        col("birthdate", "date", nullable=False),
        *string_columns(("school", "country")),
        col("last_affiliation", "string", nullable=False),
        col("height", "string"),
        col("weight", "float", minimum=100, maximum=500),
        col("season_exp", "integer", nullable=False, minimum=0, maximum=40),
        *string_columns(("jersey", "position")),
        col("rosterstatus", "string", nullable=False, allowed=("Active", "Inactive")),
        col("games_played_current_season_flag", "boolean", nullable=False, allowed=BOOL),
        col("team_id", "integer", minimum=0),
        *string_columns(("team_name", "team_abbreviation", "team_code", "team_city")),
        col("playercode", "string"),
        col("from_year", "integer", minimum=1940, maximum=2100),
        col("to_year", "integer", minimum=1940, maximum=2100),
        col("dleague_flag", "boolean", nullable=False, allowed=BOOL),
        col("nba_flag", "boolean", nullable=False, allowed=BOOL),
        col("games_played_flag", "boolean", nullable=False, allowed=BOOL),
        col(
            "draft_year",
            "integer",
            minimum=1940,
            maximum=2100,
            null_tokens=(*DEFAULT_NULL_TOKENS, "undrafted"),
        ),
        *string_columns(("draft_round", "draft_number")),
        col("greatest_75_flag", "boolean", nullable=False, allowed=BOOL),
    ),
    derived_columns=(
        col("height_inches", "float"),
        col("height_cm", "float"),
    ),
)


GAME_FLOATS = (
    "fgm_home",
    "fga_home",
    "fg_pct_home",
    "fg3m_home",
    "fg3a_home",
    "fg3_pct_home",
    "ftm_home",
    "fta_home",
    "ft_pct_home",
    "oreb_home",
    "dreb_home",
    "reb_home",
    "ast_home",
    "stl_home",
    "blk_home",
    "tov_home",
    "pf_home",
    "pts_home",
    "plus_minus_home",
    "fgm_away",
    "fga_away",
    "fg_pct_away",
    "fg3m_away",
    "fg3a_away",
    "fg3_pct_away",
    "ftm_away",
    "fta_away",
    "ft_pct_away",
    "oreb_away",
    "dreb_away",
    "reb_away",
    "ast_away",
    "stl_away",
    "blk_away",
    "tov_away",
    "pf_away",
    "pts_away",
    "plus_minus_away",
)


GAME = TableSpec(
    name="game",
    source_file="game_raw.csv",
    output_name="fact_game",
    sql_table="core.fact_game",
    primary_key=("game_id",),
    description="One canonical wide row per game after deterministic duplicate quarantine.",
    columns=(
        col("season_id", "integer", nullable=False, minimum=10000, maximum=49999),
        col("team_id_home", "integer", nullable=False, minimum=1),
        *string_columns(("team_abbreviation_home", "team_name_home"), nullable=False),
        col("game_id", "integer", nullable=False, minimum=1),
        col("game_date", "date", nullable=False),
        col("matchup_home", "string", nullable=False),
        col("wl_home", "string", allowed=("W", "L")),
        col("min", "integer", nullable=False, minimum=0),
        *float_columns(GAME_FLOATS[:19]),
        col("video_available_home", "boolean", nullable=False, allowed=BOOL),
        col("team_id_away", "integer", nullable=False, minimum=1),
        *string_columns(
            ("team_abbreviation_away", "team_name_away", "matchup_away"), nullable=False
        ),
        col("wl_away", "string", allowed=("W", "L")),
        *float_columns(GAME_FLOATS[19:]),
        col("video_available_away", "boolean", nullable=False, allowed=BOOL),
        col(
            "season_type",
            "string",
            nullable=False,
            allowed=("Regular Season", "Pre Season", "Playoffs", "All Star", "All-Star"),
        ),
    ),
    derived_columns=(
        col("season_year", "integer", nullable=False, minimum=1940, maximum=2100),
        col("season_stage", "string", nullable=False),
    ),
)


GAME_SUMMARY = TableSpec(
    name="game_summary",
    source_file="game_summary_raw.csv",
    output_name="fact_game_summary",
    sql_table="core.fact_game_summary",
    primary_key=("game_id",),
    description="Scheduling and status attributes keyed by game.",
    columns=(
        col("game_date_est", "date", nullable=False),
        col("game_sequence", "integer", minimum=0),
        col("game_id", "integer", nullable=False, minimum=1),
        col("game_status_id", "integer", nullable=False, minimum=0),
        col("game_status_text", "string"),
        col("gamecode", "string", nullable=False),
        col("home_team_id", "integer", nullable=False, minimum=1),
        col("visitor_team_id", "integer", nullable=False, minimum=1),
        col(
            "season",
            "integer",
            nullable=False,
            output_name="season_year",
            minimum=1940,
            maximum=2100,
        ),
        col("live_period", "integer", nullable=False, minimum=0),
        *string_columns(
            ("live_pc_time", "natl_tv_broadcaster_abbreviation", "live_period_time_bcast")
        ),
        col("wh_status", "integer", nullable=False, minimum=0),
    ),
)


OTHER_STATS_FLOATS = (
    "pts_paint_home",
    "pts_2nd_chance_home",
    "pts_fb_home",
    "largest_lead_home",
    "lead_changes",
    "times_tied",
    "team_turnovers_home",
    "total_turnovers_home",
    "team_rebounds_home",
    "pts_off_to_home",
    "pts_paint_away",
    "pts_2nd_chance_away",
    "pts_fb_away",
    "largest_lead_away",
    "team_turnovers_away",
    "total_turnovers_away",
    "team_rebounds_away",
    "pts_off_to_away",
)


OTHER_STATS = TableSpec(
    name="other_stats",
    source_file="other_stats_raw.csv",
    output_name="fact_other_stats",
    sql_table="core.fact_other_stats",
    primary_key=("game_id",),
    description="Supplementary team-level metrics for the subset of games that exposes them.",
    columns=(
        col("game_id", "integer", nullable=False, minimum=1),
        col("league_id", "integer", nullable=False, minimum=0),
        col("team_id_home", "integer", nullable=False, minimum=1),
        *string_columns(("team_abbreviation_home", "team_city_home"), nullable=False),
        *float_columns(OTHER_STATS_FLOATS[:10]),
        col("team_id_away", "integer", nullable=False, minimum=1),
        *string_columns(("team_abbreviation_away", "team_city_away"), nullable=False),
        *float_columns(OTHER_STATS_FLOATS[10:]),
    ),
)


PLAYER = TableSpec(
    name="player",
    source_file="player_raw.csv",
    output_name="dim_player",
    sql_table="core.dim_player",
    primary_key=("id",),
    description="Canonical player identity dimension.",
    columns=(
        col("id", "integer", nullable=False, output_name="player_id", minimum=1),
        col("full_name", "string", nullable=False),
        col("first_name", "string"),
        col("last_name", "string", nullable=False),
        col("is_active", "boolean", nullable=False, allowed=BOOL),
    ),
)


TEAM = TableSpec(
    name="team",
    source_file="team_raw.csv",
    output_name="dim_team",
    sql_table="core.dim_team",
    primary_key=("id",),
    description="Current franchises plus generated placeholders for observed historical IDs.",
    columns=(
        col("id", "integer", nullable=False, output_name="team_id", minimum=1),
        *string_columns(("full_name", "abbreviation"), nullable=False),
        *string_columns(("nickname", "city", "state")),
        col("year_founded", "integer", minimum=1940, maximum=2100),
    ),
    derived_columns=(col("is_historical_unmapped", "boolean", nullable=False),),
)


TABLE_SPECS = {
    spec.name: spec for spec in (COMMON_PLAYER_INFO, GAME, GAME_SUMMARY, OTHER_STATS, PLAYER, TEAM)
}
OUTPUT_SPECS = {spec.output_name: spec for spec in TABLE_SPECS.values()}


def contract_bundle() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tables": {name: spec.to_dict() for name, spec in TABLE_SPECS.items()},
    }
