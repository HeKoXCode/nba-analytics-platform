# Execution layer

I keep the executable assets in this folder while the installable Python package lives in `../src/nba_pipeline`.

## Implemented flow

1. I validate exactly six files in `data_raw/` against contract v1.0.0.
2. The ETL writes immutable run directories with canonical data, quarantined rows, JSONL logs, checksums and reconciliation.
3. `SQL/script.sql` creates the database, canonical model, analytical views and independent reconciliation queries.
4. The transactional loader inserts the completed run and verifies the 15 SQL objects consumed by Power BI.
5. The PBIT connects to `NBA_Project` on `localhost,1433` through DirectQuery.

Canonical outputs:

| CSV | SQL table | Key |
|---|---|---|
| `dim_player_profile.csv` | `core.dim_player_profile` | `player_id` |
| `fact_game.csv` | `core.fact_game` | `game_id` |
| `fact_game_summary.csv` | `core.fact_game_summary` | `game_id` |
| `fact_other_stats.csv` | `core.fact_other_stats` | `game_id` |
| `dim_player.csv` | `core.dim_player` | `player_id` |
| `dim_team.csv` | `core.dim_team` | `team_id` |

`pipeline.py` and `watchdog_ingestion.py` are compatibility entry points. For normal use, install the package and run `python -m nba_pipeline ...` as shown in the root README.

## Order of execution

```text
create database → create canonical schema → transform → validate → transactional load
→ constraints/indexes → analytics views → SQL reconciliation → Power BI refresh
```

The watcher performs an initial load by default and creates a distinct run directory for every accepted change. It never overwrites a completed run.

## Configuration

Use `.env.example` only as a list of variable names. Set real values in your shell or secret manager and never commit them.
