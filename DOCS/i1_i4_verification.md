# NBA-I1 to NBA-I4 verification

Verification date: **28/08/2026 (America/Argentina/Buenos_Aires)**

## Real ETL run

- Run ID: `nba-20260829T002154Z-0af8b4ab23`.
- Runtime: Python 3.12.10 and pandas 3.0.5.
- Six LF-normalized inputs: **30,638,984 bytes** and **161,111 rows**.
- Accepted source rows: **160,956**.
- Quarantined duplicate keys: **155** (`56 game`, `89 game_summary`, `10 other_stats`).
- Generated historical-team dimension records: **53**.
- Canonical output rows: **161,009**.
- Duration: **8.677 seconds**; peak RSS is recorded in the manifest.
- Referential checks: **4/4 passed with zero orphans**.

Evidence: [`../evidence/NBA-I1-I4/real-run-lf/manifest.json`](../evidence/NBA-I1-I4/real-run-lf/manifest.json), [`reconciliation.json`](../evidence/NBA-I1-I4/real-run-lf/reconciliation.json) and [`run.log.jsonl`](../evidence/NBA-I1-I4/real-run-lf/run.log.jsonl).

## Automated quality

- `11 passed` locally.
- Core ETL branch-aware coverage: **89.92%**.
- The deterministic fixture covers all six inputs but is labeled synthetic and used only for tests.
- The committed contract and generated DDL/data dictionary pass a byte-for-byte stale-artifact check.
- The real CI run repeats the ETL, loads SQL Server 2022, reconciles counts and validates the 15 Power BI objects.

SQL integration evidence from [GitHub Actions run 33223853500](https://github.com/HeKoXCode/nba-analytics-platform/actions/runs/33223853500):

- status: `passed`;
- 161,009 rows loaded across six canonical tables;
- 65,642 fact games and exactly 131,284 team-game rows;
- 15 Power BI objects and 65 referenced columns selected successfully;
- 1946–2022 coverage, 53 explicit historical-team records and zero null, duplicate or missing team keys;
- committed result: [`sql_reconciliation.json`](../evidence/NBA-I1-I4/ci-sql/sql_reconciliation.json).

## Power BI artifact

- File: `CODE/Dashboard - POWERBI/Analisis_NBA_BestTeam.pbit`.
- Versionable source: adjacent pbi-tools project.
- Compiler: pbi-tools Core 1.2.0 on .NET 10 with major roll-forward.
- Power BI Desktop available during compilation: 2.157.879.0.
- Size: **6,374,566 bytes**.
- SHA-256: `18B49F8F2EE420D470358F08A08504C82EAB2CD34040ADD6A5D96756058478F5`.
- ZIP integrity: compiled successfully with `Report/Layout`, `DataModelSchema` and required package metadata.
- Pages: six, ordered from `Inicio` to `Metodología y cierre`.
- SQL source: only `localhost,1433/NBA_Project`; no personal host is embedded.

Compilation proves that the extracted report and model produce a valid PBIT package. It does not, by itself, prove a successful DirectQuery refresh. The screenshot protocol therefore requires a loaded local SQL instance and an explicit refresh before publication.

## Repeatable commands

```powershell
python scripts\generate_model_artifacts.py --check
python -m ruff check src tests scripts\generate_model_artifacts.py scripts\update_powerbi_project_i4.py
python -m pytest --cov=nba_pipeline --cov-report=term-missing
python -m nba_pipeline validate-model --run-dir .artifacts\nba-i1-i4-real-lf-20260828
python scripts\validate_i1_i4.py
```
