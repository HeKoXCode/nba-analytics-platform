/* Independent KPI and integrity evidence consumed by the loader and CI. */
SELECT
    (SELECT COUNT_BIG(*) FROM core.fact_game) AS fact_game_rows,
    (SELECT COUNT_BIG(*) FROM analytics.vw_team_game) AS team_game_rows,
    (SELECT COUNT_BIG(*) FROM core.dim_team) AS dim_team_rows,
    (SELECT COUNT_BIG(*) FROM core.dim_team WHERE is_historical_unmapped = 1) AS unresolved_team_rows,
    (SELECT COUNT_BIG(*) FROM core.dim_player) AS dim_player_rows,
    (SELECT COUNT_BIG(*) FROM core.dim_player_profile) AS dim_player_profile_rows,
    (SELECT COUNT_BIG(*) FROM core.fact_game_summary) AS fact_game_summary_rows,
    (SELECT COUNT_BIG(*) FROM core.fact_other_stats) AS fact_other_stats_rows,
    (SELECT MIN(season_year) FROM core.fact_game) AS first_season,
    (SELECT MAX(season_year) FROM core.fact_game) AS last_season,
    (SELECT COUNT_BIG(*) FROM analytics.dim_season) AS season_rows,
    (SELECT SUM(total_games) FROM analytics.vw_q1_hist_perf) AS q1_total_team_games,
    (SELECT COUNT_BIG(*) FROM core.fact_game WHERE wl_home IS NULL OR wl_away IS NULL) AS games_without_result;
GO

SELECT
    SUM(CASE WHEN games.game_id IS NULL THEN 1 ELSE 0 END) AS null_game_keys,
    COUNT_BIG(*) - COUNT_BIG(DISTINCT games.game_id) AS duplicate_game_keys,
    SUM(CASE WHEN home.team_id IS NULL THEN 1 ELSE 0 END) AS missing_home_team_keys,
    SUM(CASE WHEN away.team_id IS NULL THEN 1 ELSE 0 END) AS missing_away_team_keys
FROM core.fact_game AS games
LEFT JOIN core.dim_team AS home ON home.team_id = games.team_id_home
LEFT JOIN core.dim_team AS away ON away.team_id = games.team_id_away;
GO
