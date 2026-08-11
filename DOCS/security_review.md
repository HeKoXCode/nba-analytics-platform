# Security review — NBA-S2

Review date: **10/08/2026**

## Findings

- One historical revision of `CODE/watchdog_ingestion.py` contained a local SQL Server credential.
- One historical revision of `CODE/etl_audit_log.txt` contained personal absolute paths.
- The current source reads SQL configuration from environment variables and the tracked log contains repository-relative output paths only.
- `.env`, generated logs and local build/cache files are ignored.

## Required external action

If the previously committed SQL credential was ever valid or reused elsewhere, its owner must rotate it in SQL Server and any dependent service. Removing it from the current branch does not invalidate a credential and does not erase Git history.

## History decision

The history was reviewed but not rewritten during S2. Rewriting public Git history would replace commit identifiers and disrupt existing clones. If secret scanning or credential ownership confirms that history removal is required, perform a coordinated history rewrite only after rotation and explicit approval.
