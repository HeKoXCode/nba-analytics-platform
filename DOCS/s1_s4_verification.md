# NBA-S1 to NBA-S4 verification

Verification date: **10/09/2026**

## Scope

- **S1 — credibility:** separated the approximately 2.31 GB external source folder from the six committed inputs actually processed (30,638,984 bytes).
- **S2 — security:** moved SQL configuration to environment variables, removed personal paths from the current audit log and documented the credential-history decision.
- **S3 — authorship:** recorded only identities and contributions supported by Git history or embedded notebook attribution.
- **S4 — report cleanup:** removed the duplicate conclusion, unsupported financial/future claims, custom tile slicers and stale screenshots.

## Power BI artifact

- Format: Power BI template (`Analisis_NBA_BestTeam.pbit`).
- Versionable source: adjacent pbi-tools project (`Analisis_NBA_BestTeam/`).
- Size: **6,372,771 bytes**.
- SHA-256: `FDD8498F49F70150D9CB33D20B8080B1A35DD545D91D4C915C7DF2091578F98A`.
- Pages: **6**, ordered from `Inicio` through `Metodología y cierre`.
- Converted filters: **4** built-in dropdown slicers.

The S4 cleanup is preserved inside the current NBA-I4 artifact. I compiled the PBIT with pbi-tools Core 1.2.0 while Power BI Desktop 2.157.1354.0 was installed. The current SQL model is complete: a local SQL Server 2022 Express load on 10/09/2026 selected all 15 Power BI objects and 65 columns and reconciled integrity to zero. See the current [`NBA-I1 to NBA-I4 verification`](i1_i4_verification.md) for the expanded model and connection evidence.

## Repeatable validation

Run:

```bash
python scripts/update_powerbi_project_s4.py
python scripts/validate_s1_s4.py
```

The GitHub Actions workflow runs the validation script on pull requests and pushes to `main`. It checks the documented volume, current security posture, attribution, JSON integrity, report pages, slicers, removed claims and compiled PBIT structure.
