# NBA-S1 to NBA-S4 verification

Verification date: **10/08/2026**

## Scope

- **S1 — credibility:** separated the approximately 2.31 GB external source folder from the six committed inputs actually processed (30,638,984 bytes).
- **S2 — security:** moved SQL configuration to environment variables, removed personal paths from the current audit log and documented the credential-history decision.
- **S3 — authorship:** recorded only identities and contributions supported by Git history or embedded notebook attribution.
- **S4 — report cleanup:** removed the duplicate conclusion, unsupported financial/future claims, custom tile slicers and stale screenshots.

## Power BI artifact

- Format: Power BI template (`Analisis_NBA_BestTeam.pbit`).
- Versionable source: adjacent pbi-tools project (`Analisis_NBA_BestTeam/`).
- Size: **6,374,230 bytes**.
- SHA-256: `1D0C1EC57C70E910E3217629926C35615D9D31BEF76DF44E6F166F063265EBBA`.
- Pages: **6**, ordered from `Inicio` through `Conclusión`.
- Converted filters: **4** built-in dropdown slicers.

The PBIT was compiled with pbi-tools Core 1.2.0 and recognized by Power BI Desktop 2.156.951.0. A complete visual refresh could not be performed because the original local SQL Server was unavailable and the current SQL script still lacks model dependencies documented for NBA-I3.

## Repeatable validation

Run:

```bash
python scripts/update_powerbi_project_s4.py
python scripts/validate_s1_s4.py
```

The GitHub Actions workflow runs the validation script on pull requests and pushes to `main`. It checks the documented volume, current security posture, attribution, JSON integrity, report pages, slicers, removed claims and compiled PBIT structure.
