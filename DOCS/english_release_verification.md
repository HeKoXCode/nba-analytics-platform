# English edition — dated verification record

**Checked:** 2026-10-01; fresh Desktop opening, refresh and six-page render rechecked on **2026-10-06**, Windows Power BI Desktop Store 2.158.1177.0. **Pinned template:** `CODE/Dashboard - POWERBI/NBA_Analytics_EN.pbit`, 6,376,258 bytes, SHA-256 `F9E5EE6E91CD43E5479A4B483A18211D0DE1997C09A3F7E776FCA317A6049518`.

## Reproduction boundary

I loaded the six committed CSVs into a dedicated QA run and SQL Server database `NBA_EN_QA_20260929`; I did **not** point the QA loader at the normal `NBA_Project` database. The QA template was built from the same versionable report source as the pinned template. Its `Report/Layout` is byte-identical; in `DataModelSchema`, only 15 database-name references differ (`NBA_Project` → `NBA_EN_QA_20260929`). The template contains DirectQuery metadata, not data or credentials. You can reproduce it from a short-path checkout using [the root instructions](../README.md#reproduce-the-etl) and [the Power BI build guide](../CODE/Dashboard%20-%20POWERBI/README.md#rebuild-the-versionable-report).

The isolated run measured **161,111 input rows**, **161,009 accepted rows**, **155 duplicate rejects** and **65,642 unique games**. SQL reconciliation selected **15 analytical objects and 65 referenced columns**, with no cross-table orphans or duplicate game keys. It found 30 current teams plus 53 clearly marked observed historical-team references. The [SQL record](../evidence/NBA-English-2026-09-29/sql_reconciliation.json), [result snapshot](../evidence/NBA-English-2026-09-29/insight_snapshot.json) and [artifact manifest](../evidence/NBA-English-2026-09-29/artifact_manifest.json) are separate from screenshots. The local Python run passed **13/13 tests** with **89.92% core ETL coverage**; this is not a claim of total project coverage.

An independent short-path copy reproduced those ETL counts on 2026-10-01. A second storytelling-generator pass left all **1,032 versionable source files byte-identical**. On 2026-10-06 I reran the 13-test suite (89.92% core ETL coverage), generated-artifact `--check`, S1–S4/I1–I4/English validators and the documented scoped Ruff command. I also rechecked the headline SQL results in the isolated database without reloading or modifying the normal database.

## Desktop checklist

| Page | What I checked in the isolated QA copy | Result |
|---|---|---|
| Overview | Opening copy, scope text, baseline counts and six-link native navigation | Rendered and navigable. |
| 01 Historical Performance | Historical leaderboard and decade/scoring context; fixed historical finding | Rendered. Spurs baseline is 2,427/4,077 = 59.53%. |
| 02 Home Advantage & Consistency | Home/away comparison and consistency charts | Rendered. Eligible team-season means are 104.69 home and 101.11 away PPG. |
| 03 Player Profiles & Offense | Profile chart, team selection/reset and offensive Top 12 | Rendered. The synthetic `(En blanco)` team choice was removed by a versioned visual filter. Selecting Boston Celtics, outside the offensive Top 12, empties that chart while the profile still responds; reset restores the baseline. |
| 04 Historical Peak vs. 2013–2022 | Historical streak and recent-window leaderboard | Rendered with exactly 12 recent teams. Lakers' observed streak is 33; Warriors' recent rate is 656/986 = 66.53%. |
| 05 Method & Evidence | Contract, lineage, test and SQL-model cards | Rendered with 13 tests, 89.92% core ETL coverage and 15 objects. |

In Desktop edit mode I followed each native navigation action with **Ctrl+Enter**; all six destinations worked. Ordinary selection and return to baseline were exercised. Authored report text remained English under a Spanish-language Desktop installation. Automatic UI strings, aggregate labels and decimal punctuation may be localized by Power BI itself; those are not translated report copy. Fixed orange findings are full-sample annotations and intentionally do not recalculate with exploratory selections.

The fresh 2026-10-06 QA opening and Desktop refresh completed without a Power Query warning; all six pages rendered with the baseline data. This checks the stated local environment, not every possible Desktop/SQL installation.

## Current media and review scope

- **Verified:** static report and model contracts, isolated SQL results, Python suite, six-page desktop render, navigation, baseline and single-team selection/reset, the Top-12 visual filter and nonblank team slicer.
- **Not interactively proven:** Ctrl-assisted multi-selection, transient hover tooltips and keyboard tab order / screen-reader names. The versioned visual configuration was inspected, but that is not equivalent to a live accessibility test.
- **Not available here:** English-language Power BI Desktop installation. The English-authored copy was checked under Spanish Desktop, and application-generated labels can follow the evaluator's locale.
- **Not implemented:** a native phone layout. The report is a desktop interactive artifact. A later phone-width *crop for social media* would be a static image, not mobile Power BI support.
- **Current media:** [six English report previews](../IMAGES/powerbi_english/README.md), the [six-page native report PDF](media/technical/nba_english_report_native_hq.pdf), and three separately labelled [English editorial documents](media/linkedin/) for professional communication. The editorial documents are not screenshots or additional live report pages.

**Decision:** the recorded checks support desktop technical review of this exact English template, with a no-install PDF route for initial evaluation. This record does not convert untested accessibility interactions into passed tests. Any later report or SQL change requires renewed verification; the media hashes are listed in [the media manifest](media/manifest.json).
