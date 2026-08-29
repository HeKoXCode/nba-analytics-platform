# Dashboard screenshot protocol

I retired the pre-remediation screenshots because they showed unsupported claims, a duplicate page and truncated slicers. I will publish replacements only after a complete DirectQuery refresh against the canonical SQL model.

For each of the six pages, the capture must:

1. use the same 1320 × 760 page view and browser/desktop zoom;
2. keep the mouse cursor outside the report canvas;
3. show no loading spinner, error banner or selection outline;
4. use the real six-CSV run, never the synthetic test fixture;
5. record refresh date, `65,642` unique games and `1946–2022` coverage in the accompanying evidence;
6. reconcile visible totals with `CODE/SQL/30_reconciliation.sql`.

Until those conditions are met, the compiled PBIT and extracted source are the published report evidence and this folder intentionally contains no dashboard PNGs.
