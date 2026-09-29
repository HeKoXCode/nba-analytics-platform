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
- Current published size: **6,377,099 bytes**.
- Current published SHA-256: `BFB581E8D43A404A6C87AE1BFB8FD59304911F38503431C9BDE928652996A368`.
- Pages: **6**, ordered from `Inicio` through `05 · Método y evidencia`.
- Converted filters: **4** built-in dropdown slicers.

The S4 cleanup is preserved inside the current artifact and the later storytelling redesign. I compiled the PBIT with pbi-tools Core 1.2.0 while Power BI Desktop 2.157.1354.0 was installed. The current SQL model is complete: a local SQL Server 2022 Express load on 10/09/2026 selected all 15 Power BI objects and 65 columns and reconciled integrity to zero. See the current [`NBA-I1 to NBA-I4 verification`](i1_i4_verification.md) and [`visual-storytelling redesign`](visual_storytelling_redesign.md) for the expanded evidence.

## Repeatable validation

Run:

```bash
python scripts/update_powerbi_project_s4.py
python scripts/validate_s1_s4.py
```

The GitHub Actions workflow runs the validation script on pull requests and pushes to `main`. It checks the documented volume, current security posture, attribution, JSON integrity, report pages, slicers, removed claims and compiled PBIT structure.
