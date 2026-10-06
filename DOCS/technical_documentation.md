# Technical implementation — NBA ETL, SQL and English BI edition

Current reviewer route: [reviewer guide](reviewer_guide.md) and [English release verification](english_release_verification.md). I retain dated I1–I4 evidence as history; the current English snapshot is [`../evidence/NBA-English-2026-09-29/insight_snapshot.json`](../evidence/NBA-English-2026-09-29/insight_snapshot.json).

## 1. Runtime and dependency policy

I target Python 3.12 and pin the reproducible runtime in `.python-version`, `pyproject.toml`, `requirements.lock` and `requirements-dev.lock`. The production command is `python -m nba_pipeline`; the two scripts under `CODE/` remain compatibility wrappers.

Stable exit codes:

| Code | Meaning |
|---:|---|
| 0 | successful operation |
| 2 | input, schema or data-contract failure |
| 4 | runtime or infrastructure failure |
| 130 | interrupted by the operator |

I configure UTF-8 explicitly for files and console output, including Windows terminals that previously failed on emoji output.

The versioned pbi-tools extraction contains generated visual-directory names that can exceed the legacy Windows path limit. A Windows checkout must use `core.longpaths=true`; the root README provides a one-shot clone command and the repository-local setting. `.gitattributes` also fixes LF for CSV inputs and byte-compared generated artifacts so checksums and generator validation remain stable across Windows and Linux.

## 2. Contract-driven ETL

`src/nba_pipeline/contracts.py` defines the exact header, order, type, nullability, domain, range, primary key and output name for all six inputs. `contracts/schema_v1.0.0.json` is generated from that source and committed for review.

Important transformations are explicit:

- `season_year = season_id % 10000`, so NBA season code `21946` becomes `1946`, not a 1970 timestamp;
- `draft_year=Undrafted` becomes a documented null;
- height strings such as `6-6` produce `78` inches and `198.12` cm;
- booleans use an allow-list instead of implicit truthiness;
- I do not replace every missing value with zero;
- unsupported conversions produce a row-level reason, and a 100% loss of a populated column fails the run.

I keep only the first occurrence of a duplicate primary key and write each later occurrence to the matching rejects file. A completed run is immutable and includes:

```text
data/*.csv
rejects/*_rejected.csv
manifest.json
input_manifest.json
reconciliation.json
contract_snapshot.json
run.log.jsonl
```

The manifest records versions, duration, peak RSS, row counts, byte sizes and SHA-256 checksums. The reconciliation proves `input = accepted + rejected` per source.

## 3. Referential model

The current-team CSV contains 30 records but the historical facts expose 53 additional identifiers. I retain the facts and append explicit `is_historical_unmapped=true` dimension rows using only labels observed in the source. This brings all four cross-table orphan checks to zero without inventing foundation years, states or franchise lineage.

The pipeline validates:

- game summary → game;
- other statistics → game;
- player profile → player;
- every observed team identifier → team dimension.

## 4. SQL Server

`scripts/generate_model_artifacts.py` generates `CODE/SQL/10_core_schema.sql` and the data dictionary from the same contract. `CODE/SQL/script.sql` is the SQLCMD entry point:

1. `00_create_database.sql` creates the configured database when absent;
2. `10_core_schema.sql` creates schemas, canonical tables, audit tables, keys and indexes idempotently;
3. the Python loader clears and inserts canonical tables in one transaction;
4. `20_analytics_views.sql` creates `analytics.dim_season`, `analytics.vw_bridge_team_season` and every dashboard view;
5. `30_reconciliation.sql` independently checks row counts and integrity.

The former SQL, which deleted unmatched facts before adding constraints, remains under `DOCS/archive/legacy_sql_pre_i3.sql` as historical evidence and is not executed.

The loader obtains every connection value from environment variables, validates the database identifier, audits loaded rows and then issues `SELECT TOP (0)` against every Power BI object and expected column. It fails and rolls back when counts or integrity do not reconcile.

## 5. Power BI

The semantic model reads 15 objects and 65 referenced columns from the `analytics` schema at `.\SQLEXPRESS/NBA_Project`. I use this generic local named instance so the English template matches the documented SQL Server Express setup; CI overrides the loader connection with its isolated container endpoint. I validate that each TMDL object exists in SQL and that every referenced column can be selected. The PBIT is DirectQuery, contains no credentials or embedded warehouse, and is not a web app.

I restructured the report into six pages:

| Page | Analytical role |
|---|---|
| Overview | scope and navigation |
| 01 Historical Performance | long-run win rate, scoring evolution and franchise age |
| 02 Home Advantage & Consistency | home/away, shooting/turnovers and variability |
| 03 Player Profiles & Offense | historical physical profile and Top-12 offensive context |
| 04 Historical Peak vs. 2013–2022 | historical streaks versus the recent-window rate |
| 05 Method & Evidence | data, model, quality, traceability and reviewer deliverables |

The data/model update is repeatable through `scripts/update_powerbi_project_i4.py`; the visual layer is repeatable through `scripts/update_powerbi_storytelling.py`, which applies `scripts/localize_powerbi_en.py`. The latter provides the six-link native navigation, English authored text and display names, chart semantics and visual-level offensive Top 12. The SQL recent-ranking view now uses `SUM(wins)/SUM(games_played)`, matching the historical definition; the earlier 64.20% averaged-season figure is historical and **not** the current 2013–2022 result. I compile `NBA_Analytics_EN.pbit` from the extracted project with pbi-tools Core 1.2.0 and validate it with `scripts/validate_visual_storytelling.py`. The separate Spanish PBIT remains for provenance. The English report has no dedicated phone layout.

## 6. Test strategy

The versioned test factory creates a small, deterministic and clearly synthetic six-table fixture. Unit and integration tests cover conversions, duplicate quarantine, header failure, 100%-loss failure, immutability, manifest checks and model alignment. The current local English-candidate run passed 13 tests and reports 89.92% branch-aware core ETL coverage; the older I1–I4 run had 11 tests.

CI also processes the six real committed CSV files, loads their outputs into an ephemeral SQL Server 2022 container, runs independent SQL reconciliation and uploads lightweight evidence. Synthetic fixture results are never presented as the real portfolio volume.

## 7. Desktop evidence boundary

Power BI Desktop refresh is a Windows, stateful step. I tested the English candidate through an isolated `NBA_EN_QA_20260929` copy: only the database name differs from the pinned source PBIT in 15 partitions. All six pages rendered; the Top 12 and navigation actions were observed, while the English screenshots and any native mobile layout remain outside this desktop QA. The [dated English verification](english_release_verification.md) separates tested interactions from untested tooltips/keyboard behavior. I do not treat compilation alone as refreshed-screen evidence or a Spanish screenshot as evidence for the English edition.
