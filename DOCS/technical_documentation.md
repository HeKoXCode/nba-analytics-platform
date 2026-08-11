# Technical documentation

## 1. Verified implementation

The repository is a BI architecture prototype composed of:

```text
CSV subset → Python ETL → final CSV files → SQL Server → analytics views → Power BI DirectQuery
```

The broader downloadable folder and the six-file ETL subset are separate scopes. Exact volumes are documented in `raw_data_download.md`.

## 2. Python ETL

`CODE/pipeline.py` currently reads every `*_raw.csv` file in `CODE/data_raw` and writes a correspondingly named `*_final.csv` file to `CODE/data_final`.

Canonical physical outputs:

| Output/table | Current role |
|---|---|
| `common_player_info_final` | Player biography and roster attributes |
| `game_final` | Wide game fact with home/away metrics |
| `game_summary_final` | Scheduling and game-status attributes |
| `other_stats_final` | Additional wide home/away metrics |
| `player_final` | Player identity/current activity |
| `team_final` | Current team attributes |

The current pipeline does **not** produce `fact_game`, `fact_team_game`, `dim_team` or `dim_player` files. Those names previously mixed a target star-schema design with the implemented physical model.

## 3. SQL Server layer

`CODE/SQL/script.sql` creates the six `dbo.*_final` tables and reporting views in the `analytics` schema. The execution order represented by the current code is:

1. create physical tables;
2. load final CSV files through the watchdog helper;
3. apply cleanup and foreign keys;
4. create `analytics.*` views;
5. connect Power BI.

The script is not fully idempotent and deletes unmatched rows to make some foreign keys pass. It also does not create every object referenced by Power BI, including `analytics.dim_season`. These are open NBA-I3 issues.

## 4. Automation

`watchdog_ingestion.py` monitors `CODE/data_raw`, starts the Python pipeline after a matching file event and uploads final CSV files to SQL Server. It does not process the initial folder contents automatically.

SQL configuration comes from environment variables. No server, username or password is intentionally stored in source code.

## 5. Power BI

The cleaned PBIT contains six report pages after S4 cleanup. Its pbi-tools project source is committed beside the template so report text, page structure and visual configuration can be reviewed in Git. Interactive refresh still depends on the local SQL environment.

The obsolete screenshots and original PBIX were retired because they preserved the pre-S4 claims and layout. New screenshots are deferred until NBA-I3 supplies every SQL object expected by the DirectQuery model.

The dashboard must be interpreted descriptively. Historical win rate, scoring and variability do not prove future sporting success, market value, revenue, ROI or playoff qualification.

## 6. Validation status

The historical log records row counts and type/null changes, but many lines ended in unconditional `OK`. It is evidence of an earlier run, not a passing quality contract. NBA-I2 must replace it with explicit rules, thresholds and failures.

## 7. Known remediation roadmap

- **NBA-I1:** repair encoding, pandas compatibility, year conversion, null handling, initial load and dependency locking.
- **NBA-I2:** implement genuine data-quality checks and automated tests.
- **NBA-I3:** align physical tables, star schema, SQL DDL and PBIX dependencies.
- **NBA-I4:** redesign each report page around fewer analytical questions and explicit limitations.
