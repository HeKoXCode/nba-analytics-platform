# Power BI storytelling and reproducibility

## Objective

The Power BI report turns the canonical ETL and SQL model into a concise analytical story that a recruiter or technical reviewer can understand, reproduce and challenge. The current artifact is `CODE/Dashboard - POWERBI/Analisis_NBA_BestTeam.pbit`; its editable pbi-tools source is stored in the adjacent `Analisis_NBA_BestTeam/` directory.

## Story architecture

| Step | Reader question | Primary evidence | Headline result |
|---|---|---|---|
| `Inicio` | What problem does the project solve and how is the analysis organized? | Portfolio case-study summary, four-step route and verified scope | 6 versioned CSVs, 161,111 source rows, 65,642 unique games and 11 automated tests |
| `01 · Panorama histórico` | Who sustained the best performance, and how did league scoring evolve? | Historical win rate, PPG by decade and age versus recent performance | Spurs leads at 59.53%; league PPG moves from 76.23 in the 1940s to 112.07 in the 2020s |
| `02 · Ventaja y estabilidad` | How much does home court change performance, and which teams vary less between seasons? | Win-rate CV, home/away PPG and FG% versus turnovers | Home win rate is 61.20% versus 37.36% away; home court adds 3.58 PPG |
| `03 · Perfil y ofensiva` | What do the available player profiles and offensive context show together? | Top-12 offensive context and physical-profile scatter | 3,225 profiles, 199.24 cm and 213.36 lb as franchise-level averages |
| `04 · Pico y actualidad` | Does the historical peak match the best team in the latest ten-season window? | Longest streak and 2013–2022 performance | Lakers owns the 33-game streak; Warriors leads the recent window at 64.20% |
| `05 · Método y evidencia` | Can a reviewer reproduce the result? | Data, model, quality, lineage and review deliverables | 15 analytical objects, zero cross-table orphans, 89.92% core coverage and versioned Power BI source |

The four analytical pages contain one explicit question and one **Hallazgo clave**. The fixed headline result represents the complete baseline dataset; slicers remain available for interactive exploration of the charts.

## Visual system

- Light neutral canvas (`#F3F6FB`) with white analytical panels.
- Blue (`#1D4ED8`) as the primary series, orange (`#F28C28`) for conclusions and sky (`#38BDF8`) for secondary signals.
- Segoe UI hierarchy with page, question and chart/card levels.
- No more than three analytical charts per page.
- Six direct page actions on every canvas, with the active step highlighted in orange.
- Business-facing filter captions: `Franquicia` and `Década de temporada`.
- Redundant KPI groups are kept off-canvas so titles and values never collide with the analytical question.
- The offensive-context visual is sorted and restricted to the Top 12 by PPG for a readable first view.

## Cover design

The cover is a portfolio case study rather than a decorative splash page. It contains:

1. the project title and analytical proposition;
2. the user-selected analytics mark as a visible hero element;
3. four compact story cards for history, context, profile and recent performance;
4. a verified scope strip linking Python ETL, SQL Server and Power BI DirectQuery.

The Henry mark and the legacy bookmark drop-down are not part of the public composition. A native, text-first navigation bar links `Inicio`, the four analytical steps and `Método`; it requires no downloaded icon set and remains editable inside Power BI.

## Semantic decisions

1. Shooting efficiency versus turnovers uses a scatter plot because the measures have different units.
2. Team categories in q1, q2, q3, q5, q6, q7, q8, q9 and q10 come from their analytical view, avoiding a hidden visual join.
3. The offensive Top 12 is enforced by a deterministic SQL `ROW_NUMBER()` over eligible profile teams and then ordered by PPG in the visual.
4. The scoring trend is explicitly ordered by decade ascending.
5. The decorative image inside the scoring plot is removed.
6. The 1946–2022 label refers to `season_id`; the machine-readable snapshot records the maximum calendar date separately.

## Reviewer handoff

The final page presents four review dimensions — data, model, quality and traceability — followed by the concrete deliverables:

- reproducible Python ETL;
- SQL Server model and reconciliation queries;
- compiled PBIT and editable pbi-tools source;
- dependency locks, SHA-256 manifests and result snapshot.

## Rebuild and validation

From the repository root:

```powershell
python scripts\update_powerbi_project_i4.py
python scripts\update_powerbi_storytelling.py
$env:DOTNET_ROLL_FORWARD = "Major"
tools\pbi-tools\pbi-tools.core.exe compile `
  "CODE\Dashboard - POWERBI\Analisis_NBA_BestTeam" `
  -outPath "CODE\Dashboard - POWERBI\Analisis_NBA_BestTeam.pbit" `
  -format PBIT -overwrite
python scripts\validate_i1_i4.py
python scripts\validate_visual_storytelling.py
```

The visual validator parses the extracted report, checks page order, palette, questions, takeaways, public filter labels, key-object overlap, q7 scatter semantics, direct analytical sources, Top-12 reduction, decade sort, snapshot values and package integrity.

Current compiled artifact:

- Size: **6,377,058 bytes**.
- SHA-256: `BFB581E8D43A404A6C87AE1BFB8FD59304911F38503431C9BDE928652996A368`.
- Pages: **6**.
- Explicit analytical questions: **4**.
- ZIP/package integrity: **passed**.

## Desktop review

1. Run the versioned ETL and load the generated model into SQL Server.
2. Confirm the reconciliation queries return zero integrity differences.
3. Open `Analisis_NBA_BestTeam.pbit` and use Windows authentication.
4. Let DirectQuery render all six pages.
5. Compare the baseline results with `evidence/NBA-Visual-Storytelling/insight_snapshot.json`.
6. Capture one clean 1320 × 760 image per page after all visuals finish loading.
