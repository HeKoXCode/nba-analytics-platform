/* Canonical analytics model aligned with the committed Power BI TMDL source. */
SET NOCOUNT ON;
SET XACT_ABORT ON;
GO

CREATE OR ALTER VIEW analytics.vw_team_game AS
SELECT g.game_id, g.game_date, g.season_year AS season_id, g.season_stage,
       g.team_id_home AS team_id, g.team_id_away AS opponent_team_id,
       CAST(1 AS BIT) AS is_home,
       CASE WHEN g.wl_home = N'W' THEN 1 WHEN g.wl_home = N'L' THEN 0 END AS is_win,
       g.pts_home AS pts, g.pts_away AS opponent_pts, g.fg_pct_home AS fg_pct,
       g.tov_home AS turnovers
FROM core.fact_game AS g
UNION ALL
SELECT g.game_id, g.game_date, g.season_year AS season_id, g.season_stage,
       g.team_id_away AS team_id, g.team_id_home AS opponent_team_id,
       CAST(0 AS BIT) AS is_home,
       CASE WHEN g.wl_away = N'W' THEN 1 WHEN g.wl_away = N'L' THEN 0 END AS is_win,
       g.pts_away AS pts, g.pts_home AS opponent_pts, g.fg_pct_away AS fg_pct,
       g.tov_away AS turnovers
FROM core.fact_game AS g;
GO

CREATE OR ALTER VIEW analytics.dim_season AS
SELECT years.season_year AS season_id, years.season_year,
       (years.season_year / 10) * 10 AS decade,
       CONCAT(years.season_year, N'-', RIGHT(CONVERT(NVARCHAR(4), years.season_year + 1), 2)) AS era
FROM (SELECT DISTINCT season_year FROM core.fact_game) AS years;
GO

CREATE OR ALTER VIEW analytics.vw_bridge_team_season AS
SELECT DISTINCT tg.team_id, (tg.season_id / 10) * 10 AS decade
FROM analytics.vw_team_game AS tg;
GO

CREATE OR ALTER VIEW analytics.vw_team_season_basic AS
SELECT tg.team_id, MIN(tg.season_id) AS first_season, MAX(tg.season_id) AS last_season
FROM analytics.vw_team_game AS tg
GROUP BY tg.team_id;
GO

CREATE OR ALTER VIEW analytics.vw_team_season_metrics AS
SELECT tg.team_id, tg.season_id, COUNT_BIG(*) AS games_played,
       SUM(CASE WHEN tg.is_win = 1 THEN 1 ELSE 0 END) AS wins,
       SUM(CASE WHEN tg.is_win = 0 THEN 1 ELSE 0 END) AS losses,
       CAST(AVG(CAST(tg.is_win AS FLOAT)) AS DECIMAL(24, 12)) AS winrate,
       AVG(CAST(tg.pts AS FLOAT)) AS avg_ppg,
       AVG(CAST(tg.fg_pct AS FLOAT)) AS avg_fg_pct
FROM analytics.vw_team_game AS tg
GROUP BY tg.team_id, tg.season_id;
GO

CREATE OR ALTER VIEW analytics.vw_teams AS
SELECT t.team_id, t.full_name AS team_name, t.abbreviation
FROM core.dim_team AS t;
GO

CREATE OR ALTER VIEW analytics.vw_q1_hist_perf AS
SELECT teams.team_name, metrics.team_id, SUM(metrics.wins) AS total_wins,
       SUM(metrics.games_played) AS total_games,
       CAST(SUM(metrics.wins) * 1.0 / NULLIF(SUM(metrics.games_played), 0) AS DECIMAL(24, 12)) AS winrate_hist,
       AVG(metrics.avg_ppg) AS avg_ppg_hist,
       RANK() OVER (ORDER BY SUM(metrics.wins) * 1.0 / NULLIF(SUM(metrics.games_played), 0) DESC,
                             AVG(metrics.avg_ppg) DESC) AS rank_overall
FROM analytics.vw_team_season_metrics AS metrics
JOIN analytics.vw_teams AS teams ON teams.team_id = metrics.team_id
GROUP BY teams.team_name, metrics.team_id;
GO

CREATE OR ALTER VIEW analytics.vw_q2_age_vs_current AS
WITH reference_season AS (
    SELECT MAX(season_id) AS max_season FROM analytics.vw_team_season_metrics
), recent AS (
    SELECT metrics.team_id, AVG(metrics.winrate) AS winrate_hist,
           AVG(metrics.avg_ppg) AS ppg_hist
    FROM analytics.vw_team_season_metrics AS metrics
    CROSS JOIN reference_season
    WHERE metrics.season_id BETWEEN reference_season.max_season - 2 AND reference_season.max_season
    GROUP BY metrics.team_id
)
SELECT teams.full_name AS team_name, teams.year_founded,
       CASE WHEN teams.year_founded IS NULL THEN NULL
            ELSE reference_season.max_season - teams.year_founded END AS franchise_age,
       recent.winrate_hist, recent.ppg_hist
FROM recent
JOIN core.dim_team AS teams ON teams.team_id = recent.team_id
CROSS JOIN reference_season;
GO

CREATE OR ALTER VIEW analytics.vw_q3_player_context_offense AS
WITH team_performance AS (
    SELECT metrics.team_id, AVG(metrics.avg_ppg) AS avg_ppg,
           AVG(metrics.avg_fg_pct) AS avg_fg_pct
    FROM analytics.vw_team_season_metrics AS metrics
    GROUP BY metrics.team_id
)
SELECT players.player_id, players.full_name AS player_name, teams.team_name,
       performance.avg_ppg AS [Puntos por partido],
       performance.avg_fg_pct AS [Porcentaje de acierto]
FROM core.dim_player AS players
JOIN core.dim_player_profile AS profile ON profile.player_id = players.player_id
LEFT JOIN analytics.vw_teams AS teams ON teams.team_id = profile.team_id
LEFT JOIN team_performance AS performance ON performance.team_id = profile.team_id
WHERE profile.nba_flag = 1;
GO

CREATE OR ALTER VIEW analytics.vw_q4_ppg_by_decade AS
SELECT (tg.season_id / 10) * 10 AS decade, AVG(CAST(tg.pts AS FLOAT)) AS league_ppg
FROM analytics.vw_team_game AS tg
GROUP BY (tg.season_id / 10) * 10;
GO

CREATE OR ALTER VIEW analytics.vw_q5_consistency AS
SELECT teams.team_name,
       CAST(100.0 * STDEV(CAST(metrics.winrate AS FLOAT)) /
            NULLIF(AVG(CAST(metrics.winrate AS FLOAT)), 0) AS DECIMAL(24, 12)) AS var_winrate_pct,
       CAST(100.0 * STDEV(CAST(metrics.avg_ppg AS FLOAT)) /
            NULLIF(AVG(CAST(metrics.avg_ppg AS FLOAT)), 0) AS DECIMAL(24, 12)) AS var_ppg_pct
FROM analytics.vw_team_season_metrics AS metrics
JOIN analytics.vw_teams AS teams ON teams.team_id = metrics.team_id
GROUP BY teams.team_name, metrics.team_id;
GO

CREATE OR ALTER VIEW analytics.vw_q6_home_away_impact AS
SELECT teams.team_name, tg.season_id,
       AVG(CASE WHEN tg.is_home = 1 THEN CAST(tg.is_win AS FLOAT) END) AS winrate_home,
       AVG(CASE WHEN tg.is_home = 0 THEN CAST(tg.is_win AS FLOAT) END) AS winrate_away,
       AVG(CASE WHEN tg.is_home = 1 THEN CAST(tg.pts AS FLOAT) END) AS [Puntos como Local],
       AVG(CASE WHEN tg.is_home = 0 THEN CAST(tg.pts AS FLOAT) END) AS [Puntos como visitante]
FROM analytics.vw_team_game AS tg
JOIN analytics.vw_teams AS teams ON teams.team_id = tg.team_id
GROUP BY teams.team_name, tg.team_id, tg.season_id;
GO

CREATE OR ALTER VIEW analytics.vw_q7_balance_of_def AS
SELECT teams.team_name, tg.season_id,
       AVG(CAST(tg.fg_pct AS FLOAT)) AS [Eficiencia de tiro],
       AVG(CAST(tg.turnovers AS FLOAT)) AS [Balones perdidos],
       AVG(CAST(tg.fg_pct AS FLOAT)) -
           (AVG(CAST(tg.turnovers AS FLOAT)) / 100.0) AS balance_score
FROM analytics.vw_team_game AS tg
JOIN analytics.vw_teams AS teams ON teams.team_id = tg.team_id
GROUP BY teams.team_name, tg.team_id, tg.season_id;
GO

CREATE OR ALTER VIEW analytics.vw_q8_longest_win_streak AS
WITH ordered AS (
    SELECT tg.team_id, tg.game_date, tg.game_id, tg.is_win,
           SUM(CASE WHEN tg.is_win = 0 OR tg.is_win IS NULL THEN 1 ELSE 0 END) OVER (
               PARTITION BY tg.team_id ORDER BY tg.game_date, tg.game_id ROWS UNBOUNDED PRECEDING
           ) AS streak_group
    FROM analytics.vw_team_game AS tg
), streaks AS (
    SELECT team_id, streak_group, COUNT_BIG(*) AS streak_length
    FROM ordered WHERE is_win = 1 GROUP BY team_id, streak_group
)
SELECT teams.team_name, streaks.team_id, MAX(streaks.streak_length) AS longest_win_streak
FROM streaks
JOIN analytics.vw_teams AS teams ON teams.team_id = streaks.team_id
GROUP BY teams.team_name, streaks.team_id;
GO

CREATE OR ALTER VIEW analytics.vw_q9_physical_profile AS
SELECT teams.team_name, COUNT_BIG(*) AS n_players,
       AVG(profile.height_cm) AS avg_height, AVG(profile.weight) AS avg_weight
FROM core.dim_player_profile AS profile
LEFT JOIN analytics.vw_teams AS teams ON teams.team_id = profile.team_id
WHERE profile.nba_flag = 1
GROUP BY teams.team_name, profile.team_id;
GO

CREATE OR ALTER VIEW analytics.vw_q10_recent_top AS
WITH reference_season AS (
    SELECT MAX(season_id) AS max_season FROM analytics.vw_team_season_metrics
), recent AS (
    SELECT metrics.* FROM analytics.vw_team_season_metrics AS metrics
    CROSS JOIN reference_season
    WHERE metrics.season_id BETWEEN reference_season.max_season - 9 AND reference_season.max_season
), aggregated AS (
    SELECT team_id, AVG(winrate) AS winrate_10y, AVG(avg_ppg) AS ppg_10y
    FROM recent GROUP BY team_id
)
SELECT teams.team_name, aggregated.team_id,
       aggregated.winrate_10y AS [Porcentaje de victorias ultimos 10 años],
       aggregated.ppg_10y AS [Puntos por partido ultimos 10 años],
       RANK() OVER (ORDER BY aggregated.winrate_10y DESC, aggregated.ppg_10y DESC) AS rk_recent
FROM aggregated
JOIN analytics.vw_teams AS teams ON teams.team_id = aggregated.team_id;
GO
