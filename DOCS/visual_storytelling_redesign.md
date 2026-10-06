# Power BI storytelling — English edition

I use the six-page [`NBA_Analytics_EN.pbit`](../CODE/Dashboard%20-%20POWERBI/NBA_Analytics_EN.pbit) to let a reviewer move from a business question to a checked result, then inspect the method. The fixed findings describe the **full committed sample**; slicers are exploratory and do not recalculate those annotations. The earlier Spanish gallery and PBIT remain historical, not current English visual evidence. See the [reviewer route](reviewer_guide.md) and [dated English QA](english_release_verification.md).

| Page | Reader question | Visual evidence | Fixed full-sample finding |
|---|---|---|---|
| Overview | What is the analytical product and where do I start? | Four-step route, six-source scope and workflow strip | 161,111 input rows; 65,642 retained games; 13 local tests. |
| 01 Historical Performance | Who leads the long-run win-rate ranking, and how did scoring change? | Team rate, scoring by decade, age versus recent performance | Spurs **59.53% across 4,077 games**; 76.23 PPG in 1940s versus 112.07 in 2020s. |
| 02 Home Advantage & Consistency | What do home/away, variability and shooting/turnovers reveal? | Home/away PPG, win-rate CV, FG% versus turnovers | Home **104.69** versus away **101.11 PPG**; 61.20% versus 37.36% are unweighted team-season win-rate means. |
| 03 Player Profiles & Offense | What do the available historical player profiles show beside offense? | SQL-backed eligible offensive Top 12 and historical profile scatter | 3,225 profiles; mean of team averages **199.24 cm / 213.36 lb**. |
| 04 Historical Peak vs. 2013–2022 | Is the all-time streak leader also the recent rate leader? | Longest streak and recent team ranking | Lakers **33-game** streak; Warriors **66.53% (656/986)** for seasons 2013–2022. |
| 05 Method & Evidence | How can I challenge the result? | Data → contract → ETL → SQL → DirectQuery lineage and review deliverables | 15 analytical objects, zero cross-table orphans, 13 tests, 89.92% core ETL coverage. |

The **64.20%** number in the prior Spanish visual documentation was an average of team-season rates, not the same wins/games denominator as the historical ranking. I corrected the SQL view and English fixed result to **66.53%**. This is a change in analytical definition, not a cosmetic translation. The [English snapshot](../evidence/NBA-English-2026-09-29/insight_snapshot.json) is the baseline for exact values and periods; the [old snapshot](../evidence/NBA-Visual-Storytelling/insight_snapshot.json) remains dated historical evidence.

## Visual choices and interaction

- I keep one explicit question and one orange headline per analytical page, with no more than three analytical charts per page.
- I use a neutral canvas, blue data series and orange conclusions. A native six-link navigation bar stays inside the report, without external icon dependencies.
- I use a scatter for FG% versus turnovers because these measures have different units, and order decades chronologically.
- The offensive Top 12 is enforced by the visual filter over a deterministic SQL ranking. The SQL view still serves 30 teams elsewhere. Selecting a team outside the Top 12 can correctly leave that chart empty while the profile visual still has a point.
- A Power BI Desktop installation may localize shell labels, aggregation names and decimal separators. The authored questions, titles and conclusions are English.
- The desktop canvas is the interactive target. There is **no native phone layout** in the current artifact; a cropped social image is not one.

## Rebuild and evidence boundary

Run the commands in the [Power BI README](../CODE/Dashboard%20-%20POWERBI/README.md#rebuild-the-versionable-report). The pinned candidate is **6,376,258 bytes**, SHA-256 `F9E5EE6E91CD43E5479A4B483A18211D0DE1997C09A3F7E776FCA317A6049518`. A second source-generation pass was byte-stable across 1,032 source files; a new compiled ZIP may differ in package metadata. The QA copy connected only to an isolated database and rendered six pages, including the corrected page-03 team slicer. Those checks do **not** establish a published screenshot set, a mobile experience, or an English-language installation of Power BI Desktop. I keep those claims separate in [verification](english_release_verification.md) and the [image protocol](../IMAGES/README.md).
