# 🏀 NBA Analytics Platform

> I built this portfolio project to turn six historical NBA datasets into an auditable ETL, a canonical SQL Server model and a six-page Power BI report. The current release completes the NBA-I1 through NBA-I4 remediation plan.

## 🎯 What you can analyze

The report lets you compare descriptive patterns in the available sample:

- historical win rates and scoring evolution;
- franchise age and observed performance;
- home/away scoring differences;
- shooting efficiency, turnovers and season-to-season variability;
- player physical profiles, offensive context, win streaks and recent performance.

I do not use these results to predict future games, revenue, playoff qualification or investment returns.

## ✅ Verified result

| Check | Result |
|---|---:|
| Versioned inputs | 6 CSV · 30,638,984 LF-normalized bytes |
| Input rows | 161,111 |
| Accepted source rows | 160,956 |
| Quarantined duplicates | 155 |
| Generated historical team references | 53 |
| Canonical output rows | 161,009 |
| Unique games retained | 65,642 |
| Cross-table orphan checks | 0 |
| Core ETL test coverage | 89.92% |

The wider source folder was approximately **2.31 GB** when it was audited. It is not the volume processed here, and this repository does not claim a 22 GB run. Read [the source and scope note](DOCS/raw_data_download.md) for the distinction.

## 🏗️ Architecture

```text
six versioned CSV inputs
        ↓  contract v1.0.0 + typed validation
Python ETL ──→ rejects/ + manifest + SHA-256 + reconciliation
        ↓
canonical CSV model
        ↓  transactional load
SQL Server: core + audit + analytics
        ↓  DirectQuery
Power BI template + versionable pbi-tools source
```

The pipeline does not delete valid fact rows to force foreign keys. It preserves every accepted game and adds explicit historical-team records when the current 30-team dimension has no matching identifier.

## ▶️ Run it

You need Python **3.12**. SQL Server and Power BI Desktop are only required for the BI layer.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock
python -m pip install -e .
python -m nba_pipeline transform `
  --input-dir CODE\data_raw `
  --run-dir .artifacts\my-first-run
```

Each `--run-dir` is immutable. Choose a new directory for every execution. A successful run contains canonical data, rejects, structured logs, the exact contract snapshot and checksummed manifests.

To run the automated suite:

```powershell
python -m pip install -r requirements-dev.lock
python -m pip install -e .
python -m ruff check src tests scripts/generate_model_artifacts.py scripts/update_powerbi_project_i4.py
python -m pytest --cov=nba_pipeline --cov-report=term-missing
```

## 🗄️ Load SQL Server

Copy the variable names from [`CODE/.env.example`](CODE/.env.example) into your own environment and provide a local secret. I do not commit credentials.

```powershell
$env:NBA_SQL_DRIVER = "ODBC Driver 18 for SQL Server"
$env:NBA_SQL_SERVER = "localhost,1433"
$env:NBA_SQL_DATABASE = "NBA_Project"
$env:NBA_SQL_TRUSTED_CONNECTION = "no"
$env:NBA_SQL_USER = "sa"
$env:NBA_SQL_PASSWORD = "<your-local-secret>"

python -m nba_pipeline load-sql `
  --run-dir .artifacts\my-first-run `
  --evidence-dir evidence\my-first-sql-load
```

The loader applies the idempotent schema, loads all canonical tables in one transaction, creates the analytical views and verifies every object and column required by Power BI. CI repeats this against an ephemeral SQL Server 2022 container.

## 📊 Power BI

Open [`Analisis_NBA_BestTeam.pbit`](CODE/Dashboard%20-%20POWERBI/Analisis_NBA_BestTeam.pbit) after loading the local database. I organized the report into:

1. Historia y evolución;
2. Eficiencia y consistencia;
3. Talento y perfil;
4. Rachas y actualidad;
5. Metodología y cierre;
6. plus the cover page.

Every analytical title states its period or sample and unit. The final page records scope, quality decisions, limitations and the last integral validation date. The adjacent `Analisis_NBA_BestTeam/` directory is the reviewable pbi-tools project used to compile the PBIT.

## 🔎 Evidence and documentation

- [NBA-I1–I4 verification](DOCS/i1_i4_verification.md)
- [Technical implementation](DOCS/technical_documentation.md)
- [Canonical data dictionary](DOCS/canonical_data_dictionary.md)
- [Model and ERD](DOCS/data_model.md)
- [Versioned contract](contracts/schema_v1.0.0.json)
- [Real-run evidence](evidence/NBA-I1-I4/real-run-lf/manifest.json)
- [Security review](DOCS/security_review.md)

## ⚠️ Boundaries

- The committed dataset is a historical analytical sample, not an official complete NBA warehouse.
- The 53 generated team records make historical identifiers explicit; they do not invent franchise metadata.
- Duplicate rows remain inspectable in `rejects/`; they are not silently discarded.
- Power BI uses DirectQuery to `localhost,1433`, so you must load SQL Server before refreshing it.
- Source access, redistribution terms and NBA-related rights must be checked before reuse.

## 👥 Authorship

I maintain and publish the current project as **HeKoXCode**. Existing Git history and notebook evidence also identify work by **Percy Ignacio Marzoratti Hill** and **Lucas Roca**. I preserve only responsibilities supported by that evidence in [CONTRIBUTORS.md](CONTRIBUTORS.md).

## 📁 Repository map

```text
src/nba_pipeline/   production ETL, validation, watcher and SQL loader
tests/              deterministic fixture and automated checks
contracts/          generated schema contract
CODE/data_raw/      six versioned source CSV files
CODE/SQL/           database, canonical model, views and reconciliation
CODE/Dashboard.../  PBIT and extracted Power BI project
DOCS/               implementation, model, scope, security and evidence notes
evidence/           lightweight reproducibility evidence; canonical data stays ignored
```
