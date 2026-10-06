# Power BI report — English edition

I use [`NBA_Analytics_EN.pbit`](NBA_Analytics_EN.pbit) for the current English technical review. The adjacent [`Analisis_NBA_BestTeam/`](Analisis_NBA_BestTeam/) directory is the versionable pbi-tools source from which I compile it. [`Analisis_NBA_BestTeam.pbit`](Analisis_NBA_BestTeam.pbit) is the preceding Spanish edition, retained for provenance; do not use its older fixed 2013–2022 result as the English baseline.

## Reader route

| Page | Question / purpose |
|---|---|
| Overview | What data, workflow and four-step story am I reviewing? |
| 01 Historical Performance | Who leads the historical win-rate ranking, and how did scoring change by decade? |
| 02 Home Advantage & Consistency | How do home/away and season variability differ in the sample? |
| 03 Player Profiles & Offense | What do the available historical profiles and offensive context show? |
| 04 Historical Peak vs. 2013–2022 | Does the longest streak identify the recent-window win-rate leader? |
| 05 Method & Evidence | How can I inspect the data contract, SQL model, quality checks and lineage? |

The six-link native bar is usable in the report; in **Power BI Desktop edit mode**, select a button and press **Ctrl+Enter** to follow its action. The fixed orange findings describe the full baseline sample even when you select teams in exploratory visuals. The page-03 offense visual shows the eligible Top 12; a team outside it may leave only that chart empty. The report has **no dedicated phone layout**. Use desktop for interactive evaluation; English media exports remain a separate release step.

## Open and reconcile

1. Run the Python ETL and SQL loader from the [root README](../../README.md#reproduce-the-etl) against a **dedicated** local `NBA_Project` on `.\SQLEXPRESS`. The loader replaces canonical contents in its configured database; never aim it at a shared database.
2. Open `NBA_Analytics_EN.pbit` in Windows Power BI Desktop and choose Windows authentication. The template contains no data or credentials. A machine with another instance/database can change the connection in Desktop, but that is a reviewer-local variant, not the committed source.
3. Let DirectQuery render all six pages. Compare fixed figures with the [English snapshot](../../evidence/NBA-English-2026-09-29/insight_snapshot.json) and run [`../SQL/30_reconciliation.sql`](../SQL/30_reconciliation.sql) for independent counts. The isolated English QA selected 15 objects and 65 columns; see [verification](../../DOCS/english_release_verification.md).
4. Be aware that Power BI's automatic menus, aggregate labels and decimal formatting may follow the language of **your Desktop installation**. The report's authored questions, chart titles and conclusions are English.

## Rebuild the versionable report

From the repository root, with Python 3.12 and the pinned developer dependencies installed:

```powershell
python scripts\update_powerbi_project_i4.py
python scripts\update_powerbi_storytelling.py
$env:DOTNET_ROLL_FORWARD = "Major"
tools\pbi-tools\bin\pbi-tools.core.exe compile `
  "CODE\Dashboard - POWERBI\Analisis_NBA_BestTeam" `
  -outPath "CODE\Dashboard - POWERBI\NBA_Analytics_EN.pbit" `
  -format PBIT -overwrite
python scripts\validate_i1_i4.py
python scripts\validate_visual_storytelling.py
```

The storytelling script applies the English localization stage, the checked Top-12 filter and a nonblank page-03 team slicer. A second generator pass produced identical source files; recompilation may still change package metadata and its whole-file SHA-256. The **reviewed English template** is pinned by [artifact manifest](../../evidence/NBA-English-2026-09-29/artifact_manifest.json); its SHA-256 is `F9E5EE6E91CD43E5479A4B483A18211D0DE1997C09A3F7E776FCA317A6049518`. If you recompile, validate the new package and Desktop render before calling it equivalent. For a no-install review, use the [native English PDF](../../DOCS/media/technical/nba_english_report_native_hq.pdf) and [current gallery](../../IMAGES/powerbi_english/README.md).
