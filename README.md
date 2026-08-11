# 🏀 NBA Analytics Platform

> **Current status:** BI portfolio prototype under technical remediation. The repository demonstrates an ETL → SQL Server → Power BI workflow, but it is not yet a production system or a one-command reproducible project.

## 🎯 Analytical objective

Explore historical NBA team performance and answer descriptive questions such as:

- Which franchises have the strongest observed historical win rates?
- How have scoring levels changed over time?
- What home/away differences appear in the available games?
- Which teams show lower historical variability?

The dashboard describes the available sample. It does **not** estimate revenue, return on investment, future playoff probability or causal drivers of success.

## 📦 Verified data scope

| Layer | Verified volume | Role |
|---|---:|---|
| External source folder | approximately 2.31 GB at the time of the portfolio audit | Broader downloadable material; not entirely processed by this repository |
| Versioned ETL subset | 6 CSV files, 30,638,984 bytes (30.64 MB decimal / 29.22 MiB) | Actual input used by `CODE/pipeline.py` |

The previous repository description overstated the processed volume. Dataset availability and processed scope are now reported separately. See [source and download notes](DOCS/raw_data_download.md).

## 🏗️ Current architecture

```text
CODE/data_raw/*_raw.csv
          ↓
CODE/pipeline.py
          ↓
CODE/data_final/*_final.csv
          ↓
CODE/watchdog_ingestion.py
          ↓
SQL Server tables + analytics views
          ↓
Power BI (DirectQuery)
```

The Python pipeline currently produces these canonical files/tables:

| Output | Description |
|---|---|
| `common_player_info_final` | Player biography and roster attributes |
| `game_final` | One wide row per game with home and away statistics |
| `game_summary_final` | Game status and scheduling attributes |
| `other_stats_final` | Additional home/away game metrics |
| `player_final` | Player identity and activity flag |
| `team_final` | Current team attributes |

`CODE/SQL/script.sql` creates tables with those names and a separate `analytics` schema for reporting views. A fully conformed historical star schema remains future work.

## 📊 Power BI evidence

The repository includes:

- `CODE/Dashboard - POWERBI/Analisis_NBA_BestTeam.pbit`: a cleaned Power BI template;
- `CODE/Dashboard - POWERBI/Analisis_NBA_BestTeam/`: the versionable pbi-tools source used to build it;
- six report pages after removing the duplicated conclusion;
- compact dropdown slicers and conclusions limited to observed metrics.

The obsolete screenshots were removed because they still displayed unsupported claims and visual defects. New screenshots must be captured only after the SQL model is reproducible; see `IMAGES/README.md`.

## ▶️ Execution status

1. Review [source and license notes](DOCS/raw_data_download.md).
2. Copy the required six `*_raw.csv` inputs to `CODE/data_raw/`.
3. Configure SQL access using environment variables; start from `CODE/.env.example`.
4. Run `python CODE/pipeline.py` to create CSV outputs.
5. Run `python CODE/watchdog_ingestion.py` only when SQL Server and its ODBC driver are available.
6. Execute `CODE/SQL/script.sql`, open the PBIT and connect it to the local SQL Server model.

These are the intended steps, not a reproducibility guarantee. The current Python ETL still needs the fixes listed under “Known limitations” before a clean run on current pandas can be promised.

## 🔐 Configuration and security

- SQL host, database and authentication are read from environment variables.
- `CODE/.env.example` contains placeholders only.
- Runtime `.env` files and logs are ignored by Git.
- The Git history previously contained a local SQL credential and personal paths. If that credential was ever active, it must be rotated. See [security review](DOCS/security_review.md).

## 👥 Authorship

This repository is a collaborative artifact hosted and maintained by **HeKoXCode**. Existing Git history and embedded notebook attribution identify work by **Percy Ignacio Marzoratti Hill** and **Lucas Roca**. Exact, evidence-based responsibilities are recorded in [CONTRIBUTORS.md](CONTRIBUTORS.md); no unverified authorship is implied.

## ⚠️ Known limitations

- Dependencies are not yet locked and no clean CI sample exists.
- `pipeline.py` needs compatibility and data-quality fixes before it can be called reliable.
- The watchdog waits for a file event and does not perform an initial load automatically.
- The SQL script deletes unmatched historical rows before adding foreign keys.
- Historical franchise changes are not modeled; the current 30-team table cannot cover every historical ID.
- The PBIX expects `analytics.dim_season`, which the current SQL script does not create.
- DirectQuery requires a local SQL Server environment. The PBIT was recognized by Power BI Desktop during S4 verification, but its pages could not be refreshed without that database.

The next technical stage is NBA-I1–I4: repair and test the pipeline, turn audit messages into real validation, align SQL/Power BI objects and redesign the report around fewer questions per page.

## 📁 Repository map

```text
CODE/       ETL, SQL, notebooks, PBIT and versionable Power BI source
DOCS/       data, security and technical documentation
IMAGES/     screenshot publication policy
scripts/    repository validation utilities
```
