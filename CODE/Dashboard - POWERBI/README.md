# Power BI report

I publish `Analisis_NBA_BestTeam.pbit` as the user-facing DirectQuery template and keep its extracted pbi-tools project in `Analisis_NBA_BestTeam/` for review and version control.

## Current structure

- `Inicio`: portfolio case study, verified scope and four-step navigation.
- `01 · Panorama histórico`: one question connecting long-run win rate, scoring evolution and recent performance versus age.
- `02 · Ventaja y estabilidad`: one question connecting home advantage, variability and the shooting/turnover trade-off.
- `03 · Perfil y ofensiva`: a readable Top-12 offensive view connected with the historical player-profile sample.
- `04 · Pico y actualidad`: one question comparing a historical peak with the 2013–2022 window.
- `05 · Método y evidencia`: data, model, quality, traceability and reviewer deliverables.

I use business-labelled dropdown slicers, a restrained blue/orange theme and one evidence-backed headline finding per analytical page. The reproducible baseline behind those findings is versioned in `evidence/NBA-Visual-Storytelling/insight_snapshot.json`.

## Refresh

1. Run the ETL and SQL loader from the root README.
2. Confirm that `NBA_Project` is available at `.\SQLEXPRESS`.
3. Open the PBIT in Power BI Desktop and select Windows authentication.
4. Refresh every page.
5. Compare visible KPIs with `CODE/SQL/30_reconciliation.sql` before capturing evidence.

The PBIT does not contain the database or credentials. A compiled template is not described as refreshed until the DirectQuery model succeeds against a loaded SQL instance.

## Repeatable rebuild

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

The committed artifact hash and compiler evidence are recorded in `DOCS/i1_i4_verification.md`; the design decisions and exact visible takeaways are recorded in `DOCS/visual_storytelling_redesign.md`.
