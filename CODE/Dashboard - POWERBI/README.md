# Power BI report

`Analisis_NBA_BestTeam.pbit` is a DirectQuery template backed by the local SQL Server model. Its extracted, reviewable source is versioned in `Analisis_NBA_BestTeam/`.

## Current report state

- Six pages: cover, three analysis pages, descriptive findings and a historical Spurs profile.
- The accidental duplicate conclusion page was removed.
- Unsupported claims about revenue, ROI, future playoffs, marketability and guaranteed return were removed.
- Team and decade filters use compact dropdown slicers to avoid truncated tile labels and unnecessary internal scrollbars.
- Findings are descriptive and refer only to the available historical sample.

## Access limitation

The committed PBIT does not bundle a public refreshable database. Interactive refresh requires SQL Server, the required ODBC driver and every object referenced by the semantic model. Power BI Desktop recognized and opened the template during S4 verification, then correctly stopped at database refresh because the local SQL instance was unavailable.

The old screenshots were removed because they represented the pre-S4 report. They must be regenerated after NBA-I3 makes the SQL model reproducible.

## Rebuild

The PBIT was compiled from the extracted project with pbi-tools Core 1.2.0. Run `python scripts/update_powerbi_project_s4.py` before rebuilding to reapply the repeatable text, slicer and page cleanup.

See the root README for the verified project status and known model gaps.
