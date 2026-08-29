# Canonical data dictionary — NBA-I1–I3

Contract version: `1.0.0`.

This file is generated from `src/nba_pipeline/contracts.py`. Nullable historical
statistics remain null; they are not imputed as zero.

## `core.dim_team` / `dim_team.csv`

Current franchises plus generated placeholders for observed historical IDs.

| Column | Type | Nullable | Rule |
|---|---|---:|---|
| `team_id` | `integer` | no | min=1<br>primary key |
| `full_name` | `string` | no | — |
| `abbreviation` | `string` | no | — |
| `nickname` | `string` | yes | — |
| `city` | `string` | yes | — |
| `state` | `string` | yes | — |
| `year_founded` | `integer` | yes | min=1940<br>max=2100 |
| `is_historical_unmapped` | `boolean` | no | — |

## `core.dim_player` / `dim_player.csv`

Canonical player identity dimension.

| Column | Type | Nullable | Rule |
|---|---|---:|---|
| `player_id` | `integer` | no | min=1<br>primary key |
| `full_name` | `string` | no | — |
| `first_name` | `string` | yes | — |
| `last_name` | `string` | no | — |
| `is_active` | `boolean` | no | domain=False, True |

## `core.fact_game` / `fact_game.csv`

One canonical wide row per game after deterministic duplicate quarantine.

| Column | Type | Nullable | Rule |
|---|---|---:|---|
| `season_id` | `integer` | no | min=10000<br>max=49999 |
| `team_id_home` | `integer` | no | min=1 |
| `team_abbreviation_home` | `string` | no | — |
| `team_name_home` | `string` | no | — |
| `game_id` | `integer` | no | min=1<br>primary key |
| `game_date` | `date` | no | — |
| `matchup_home` | `string` | no | — |
| `wl_home` | `string` | yes | domain=W, L |
| `min` | `integer` | no | min=0 |
| `fgm_home` | `float` | yes | — |
| `fga_home` | `float` | yes | — |
| `fg_pct_home` | `float` | yes | — |
| `fg3m_home` | `float` | yes | — |
| `fg3a_home` | `float` | yes | — |
| `fg3_pct_home` | `float` | yes | — |
| `ftm_home` | `float` | yes | — |
| `fta_home` | `float` | yes | — |
| `ft_pct_home` | `float` | yes | — |
| `oreb_home` | `float` | yes | — |
| `dreb_home` | `float` | yes | — |
| `reb_home` | `float` | yes | — |
| `ast_home` | `float` | yes | — |
| `stl_home` | `float` | yes | — |
| `blk_home` | `float` | yes | — |
| `tov_home` | `float` | yes | — |
| `pf_home` | `float` | yes | — |
| `pts_home` | `float` | yes | — |
| `plus_minus_home` | `float` | yes | — |
| `video_available_home` | `boolean` | no | domain=False, True |
| `team_id_away` | `integer` | no | min=1 |
| `team_abbreviation_away` | `string` | no | — |
| `team_name_away` | `string` | no | — |
| `matchup_away` | `string` | no | — |
| `wl_away` | `string` | yes | domain=W, L |
| `fgm_away` | `float` | yes | — |
| `fga_away` | `float` | yes | — |
| `fg_pct_away` | `float` | yes | — |
| `fg3m_away` | `float` | yes | — |
| `fg3a_away` | `float` | yes | — |
| `fg3_pct_away` | `float` | yes | — |
| `ftm_away` | `float` | yes | — |
| `fta_away` | `float` | yes | — |
| `ft_pct_away` | `float` | yes | — |
| `oreb_away` | `float` | yes | — |
| `dreb_away` | `float` | yes | — |
| `reb_away` | `float` | yes | — |
| `ast_away` | `float` | yes | — |
| `stl_away` | `float` | yes | — |
| `blk_away` | `float` | yes | — |
| `tov_away` | `float` | yes | — |
| `pf_away` | `float` | yes | — |
| `pts_away` | `float` | yes | — |
| `plus_minus_away` | `float` | yes | — |
| `video_available_away` | `boolean` | no | domain=False, True |
| `season_type` | `string` | no | domain=Regular Season, Pre Season, Playoffs, All Star, All-Star |
| `season_year` | `integer` | no | min=1940<br>max=2100 |
| `season_stage` | `string` | no | — |

## `core.dim_player_profile` / `dim_player_profile.csv`

Player biography and roster attributes; one optional profile per player.

| Column | Type | Nullable | Rule |
|---|---|---:|---|
| `player_id` | `integer` | no | min=1<br>primary key |
| `first_name` | `string` | yes | — |
| `last_name` | `string` | no | — |
| `display_first_last` | `string` | no | — |
| `display_last_comma_first` | `string` | no | — |
| `display_fi_last` | `string` | no | — |
| `player_slug` | `string` | no | — |
| `birthdate` | `date` | no | — |
| `school` | `string` | yes | — |
| `country` | `string` | yes | — |
| `last_affiliation` | `string` | no | — |
| `height` | `string` | yes | — |
| `weight` | `float` | yes | min=100<br>max=500 |
| `season_exp` | `integer` | no | min=0<br>max=40 |
| `jersey` | `string` | yes | — |
| `position` | `string` | yes | — |
| `rosterstatus` | `string` | no | domain=Active, Inactive |
| `games_played_current_season_flag` | `boolean` | no | domain=False, True |
| `team_id` | `integer` | yes | min=0 |
| `team_name` | `string` | yes | — |
| `team_abbreviation` | `string` | yes | — |
| `team_code` | `string` | yes | — |
| `team_city` | `string` | yes | — |
| `playercode` | `string` | yes | — |
| `from_year` | `integer` | yes | min=1940<br>max=2100 |
| `to_year` | `integer` | yes | min=1940<br>max=2100 |
| `dleague_flag` | `boolean` | no | domain=False, True |
| `nba_flag` | `boolean` | no | domain=False, True |
| `games_played_flag` | `boolean` | no | domain=False, True |
| `draft_year` | `integer` | yes | min=1940<br>max=2100 |
| `draft_round` | `string` | yes | — |
| `draft_number` | `string` | yes | — |
| `greatest_75_flag` | `boolean` | no | domain=False, True |
| `height_inches` | `float` | yes | — |
| `height_cm` | `float` | yes | — |

## `core.fact_game_summary` / `fact_game_summary.csv`

Scheduling and status attributes keyed by game.

| Column | Type | Nullable | Rule |
|---|---|---:|---|
| `game_date_est` | `date` | no | — |
| `game_sequence` | `integer` | yes | min=0 |
| `game_id` | `integer` | no | min=1<br>primary key |
| `game_status_id` | `integer` | no | min=0 |
| `game_status_text` | `string` | yes | — |
| `gamecode` | `string` | no | — |
| `home_team_id` | `integer` | no | min=1 |
| `visitor_team_id` | `integer` | no | min=1 |
| `season_year` | `integer` | no | min=1940<br>max=2100 |
| `live_period` | `integer` | no | min=0 |
| `live_pc_time` | `string` | yes | — |
| `natl_tv_broadcaster_abbreviation` | `string` | yes | — |
| `live_period_time_bcast` | `string` | yes | — |
| `wh_status` | `integer` | no | min=0 |

## `core.fact_other_stats` / `fact_other_stats.csv`

Supplementary team-level metrics for the subset of games that exposes them.

| Column | Type | Nullable | Rule |
|---|---|---:|---|
| `game_id` | `integer` | no | min=1<br>primary key |
| `league_id` | `integer` | no | min=0 |
| `team_id_home` | `integer` | no | min=1 |
| `team_abbreviation_home` | `string` | no | — |
| `team_city_home` | `string` | no | — |
| `pts_paint_home` | `float` | yes | — |
| `pts_2nd_chance_home` | `float` | yes | — |
| `pts_fb_home` | `float` | yes | — |
| `largest_lead_home` | `float` | yes | — |
| `lead_changes` | `float` | yes | — |
| `times_tied` | `float` | yes | — |
| `team_turnovers_home` | `float` | yes | — |
| `total_turnovers_home` | `float` | yes | — |
| `team_rebounds_home` | `float` | yes | — |
| `pts_off_to_home` | `float` | yes | — |
| `team_id_away` | `integer` | no | min=1 |
| `team_abbreviation_away` | `string` | no | — |
| `team_city_away` | `string` | no | — |
| `pts_paint_away` | `float` | yes | — |
| `pts_2nd_chance_away` | `float` | yes | — |
| `pts_fb_away` | `float` | yes | — |
| `largest_lead_away` | `float` | yes | — |
| `team_turnovers_away` | `float` | yes | — |
| `total_turnovers_away` | `float` | yes | — |
| `team_rebounds_away` | `float` | yes | — |
| `pts_off_to_away` | `float` | yes | — |
