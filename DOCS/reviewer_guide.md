# NBA Analytics — five-minute reviewer guide

I built this case study to show how I turn six historical NBA CSVs into an auditable analytical product. The central question is **whether a team that leads across the full sample also leads in a recent ten-season window**. The answer changes with the period: San Antonio Spurs lead the historical win-rate ranking at **59.53%** (2,427/4,077); Golden State Warriors lead seasons **2013–2022** at **66.53%** (656/986). Neither figure predicts future games.

## Two decisions I made

1. **Protect the data contract instead of dropping inconvenient facts.** The source contains 30 current-team records but 53 additional observed historical IDs. I retain accepted game facts, add clearly flagged historical-team references and quarantine 155 duplicate source keys. The canonical run retains 65,642 unique games with zero cross-table orphans.
2. **Make the comparisons share a denominator.** The previous recent ranking averaged team-season rates, whereas the historical ranking used wins/games. I changed the recent view to `SUM(wins) / SUM(games_played)`, verified the 2013–2022 result in isolated SQL and updated the report's fixed finding. This is an analytical correction, not a language-only translation.

The report also shows a **3.58 PPG** home/away difference in the eligible team-season means (104.69 vs. 101.11) and a **33-game** longest observed Lakers streak. These are descriptive findings for the committed sample; they do not establish a causal home-court effect, a complete league history or a forecast. The [machine-readable snapshot](../evidence/NBA-English-2026-09-29/insight_snapshot.json) gives the exact periods and denominator notes.

## Choose your review depth

| Time / setup | Where to start | What you can verify |
|---|---|---|
| ~5 minutes; no install | [Native English PDF](media/technical/nba_english_report_native_hq.pdf), [current gallery](../IMAGES/powerbi_english/README.md), this guide and [result snapshot](../evidence/NBA-English-2026-09-29/insight_snapshot.json) | Question, contribution, six report pages and measured results. |
| Technical review; no database | [ETL source](../src/nba_pipeline/), [tests](../tests/), [SQL views](../CODE/SQL/20_analytics_views.sql), [contract](../contracts/schema_v1.0.0.json), [Power BI source](../CODE/Dashboard%20-%20POWERBI/Analisis_NBA_BestTeam/) | Transformation rules, duplicate handling, denominators, visual definitions and model lineage. |
| Full reproduction; Windows + SQL Server + Power BI | [root run instructions](../README.md#reproduce-the-etl), [Power BI guide](../CODE/Dashboard%20-%20POWERBI/README.md), [English PBIT](../CODE/Dashboard%20-%20POWERBI/NBA_Analytics_EN.pbit) | Rerun six inputs, load your own database, reconcile 15 objects/65 columns and inspect all six live pages. |

The PBIT contains **DirectQuery definitions, not embedded data or credentials**. For the interactive report, use Windows Power BI Desktop and a local SQL Server instance with the documented `NBA_Project` database; the PBIT is not a hosted web app. Its six pages are designed for desktop, without a dedicated phone layout. The English PDF and PNGs provide a no-install review route; the Spanish PBIT and gallery remain historical edition evidence.

## Authorship and source limits

The published account is **HeKoXCode**. Git history attributes the later ETL, SQL and dashboard remediation commits to **Percy Ignacio Marzoratti Hill**; `CODE/Preguntas.ipynb` identifies **Lucas Roca** as the original notebook author. I preserve that provenance in [CONTRIBUTORS.md](../CONTRIBUTORS.md) rather than assigning inherited work to myself. The CSVs are a historical sample with rights and redistribution terms to check before reuse; this repository does not claim official NBA completeness or grant a data license.
