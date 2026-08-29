# Technical implementation — NBA-I1 to NBA-I4

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

The semantic model reads 15 objects from the `analytics` schema at `localhost,1433/NBA_Project`. I validate that each TMDL object exists in SQL and that every referenced column can be selected.

I restructured the report into six pages:

| Page | Analytical role |
|---|---|
| Inicio | scope and navigation |
| Historia y evolución | historical performance, scoring evolution and franchise age |
| Eficiencia y consistencia | home/away, shooting/turnovers and variability |
| Talento y perfil | physical profile and offensive context |
| Rachas y actualidad | historical streaks and 2013–2022 performance |
| Metodología y cierre | source volume, decisions, reproducibility and limitations |

The update is repeatable through `scripts/update_powerbi_project_i4.py`. The PBIT is compiled from the extracted project with pbi-tools Core 1.2.0. Chart titles identify period/sample and unit; unsupported claims about ROI, marketability and guaranteed future performance remain excluded.

## 6. Test strategy

The versioned test factory creates a small, deterministic and clearly synthetic six-table fixture. Unit and integration tests cover conversions, duplicate quarantine, header failure, 100%-loss failure, immutability, manifest checks and model alignment. The core ETL currently reports 89.92% branch-aware coverage.

CI also processes the six real committed CSV files, loads their outputs into an ephemeral SQL Server 2022 container, runs independent SQL reconciliation and uploads lightweight evidence. Synthetic fixture results are never presented as the real portfolio volume.

## 7. Remaining operational boundary

Power BI Desktop refresh is a Windows, stateful step. The repository supplies a compiled PBIT, the complete SQL model, a CI-proven database load and a screenshot protocol. A screenshot may be published only after Power BI refreshes against a locally loaded SQL instance; a successful compile alone is not described as a refreshed report.
