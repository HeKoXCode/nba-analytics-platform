# Power BI report

I publish `Analisis_NBA_BestTeam.pbit` as the user-facing DirectQuery template and keep its extracted pbi-tools project in `Analisis_NBA_BestTeam/` for review and version control.

## Current structure

- `Inicio`: scope and navigation.
- `Historia y evolución`: three historical questions.
- `Eficiencia y consistencia`: three efficiency/variability questions.
- `Talento y perfil`: two primary questions plus supporting KPI cards.
- `Rachas y actualidad`: two questions separated from the talent page.
- `Metodología y cierre`: real volume, quality decisions, reproducibility and limits.

I use built-in dropdown slicers and descriptive conclusions only. I do not claim revenue, ROI, future playoffs, marketability or guaranteed returns.

## Refresh

1. Run the ETL and SQL loader from the root README.
2. Confirm that `NBA_Project` is available at `localhost,1433`.
3. Open the PBIT in Power BI Desktop and provide the same local SQL authentication method.
4. Refresh every page.
5. Compare visible KPIs with `CODE/SQL/30_reconciliation.sql` before capturing evidence.

The PBIT does not contain the database or credentials. A compiled template is not described as refreshed until the DirectQuery model succeeds against a loaded SQL instance.

## Repeatable rebuild

```powershell
python scripts\update_powerbi_project_i4.py
$env:DOTNET_ROLL_FORWARD = "Major"
tools\pbi-tools\bin\pbi-tools.core.exe compile `
  "CODE\Dashboard - POWERBI\Analisis_NBA_BestTeam" `
  -outPath "CODE\Dashboard - POWERBI\Analisis_NBA_BestTeam.pbit" `
  -format PBIT -overwrite
python scripts\validate_i1_i4.py
```

The committed artifact hash and compiler evidence are recorded in `DOCS/i1_i4_verification.md`.
