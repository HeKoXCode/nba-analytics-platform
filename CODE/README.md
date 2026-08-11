# Execution layer

This folder contains the current ETL, SQL loading helper, exploratory notebooks and Power BI report.

## Actual flow

1. `pipeline.py` reads the six `data_raw/*_raw.csv` inputs.
2. It writes six matching `data_final/*_final.csv` outputs.
3. `watchdog_ingestion.py` can load those CSV files into SQL Server after a file-system event.
4. `SQL/script.sql` creates the six physical tables and the `analytics.*` reporting views.
5. `Dashboard - POWERBI/Analisis_NBA_BestTeam.pbix` connects to the SQL model through DirectQuery.

The output names are `common_player_info_final`, `game_final`, `game_summary_final`, `other_stats_final`, `player_final` and `team_final`. Names such as `fact_game` or `dim_team` describe a target model, not files produced by the current pipeline.

## Configuration

Copy the variable names from `.env.example` into your own environment. The script does not automatically read a `.env` file and no real credentials should be committed.

## Current limitation

This execution layer is not yet guaranteed on a clean machine. Dependency locking, pandas compatibility, initial-load behavior, validation and automated tests belong to NBA-I1/I2.

