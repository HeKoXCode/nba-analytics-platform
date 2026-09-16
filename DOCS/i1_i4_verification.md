# NBA-I1 to NBA-I4 verification

Verification date: **10/09/2026 (America/Argentina/Buenos_Aires)**

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

The same load was repeated against local SQL Server 2022 Express on 10/09/2026. It selected the same 15 objects and 65 columns, retained 65,642 games, limited comparison views to 30 current franchises and reconciled all integrity checks to zero. Evidence: [`local-sql-express/sql_reconciliation.json`](../evidence/NBA-I1-I4/local-sql-express/sql_reconciliation.json).

## Power BI artifact

- File: `CODE/Dashboard - POWERBI/Analisis_NBA_BestTeam.pbit`.
- Versionable source: adjacent pbi-tools project.
- Compiler: pbi-tools Core 1.2.0 on .NET 10 with major roll-forward.
- Power BI Desktop installed during compilation: 2.157.1354.0.
- Size: **6,372,749 bytes**.
- SHA-256: `16AA1CD74E54334D3D481A780AEEA153D3825231F22C70576623070B436F010F`.
- ZIP integrity: compiled successfully with `Report/Layout`, `DataModelSchema` and required package metadata.
- Pages: six, ordered from `Inicio` to `Metodología y cierre`.
- SQL source: only `.\SQLEXPRESS/NBA_Project`; no personal host or credential is embedded.

Compilation proves that the extracted report and model produce a valid PBIT package. On **15/09/2026**, the compiled report was opened in Power BI Desktop against the local `.\SQLEXPRESS` instance: the native `SELECT` used by the age-versus-current view was accepted, all six pages rendered, and the streak visual returned the expected ranked values (Lakers 33, Warriors 25, Rockets 22, Spurs 20, Hawks 19). This is local Windows evidence of a successful DirectQuery session; it does not claim a hosted Power BI refresh or a 22 GB synthetic dataset.

## Repeatable commands

```powershell
python scripts\generate_model_artifacts.py --check
python -m ruff check src tests scripts\generate_model_artifacts.py scripts\update_powerbi_project_i4.py
python -m pytest --cov=nba_pipeline --cov-report=term-missing
python -m nba_pipeline validate-model --run-dir .artifacts\nba-i1-i4-real-lf-20260828
python scripts\validate_i1_i4.py
```
