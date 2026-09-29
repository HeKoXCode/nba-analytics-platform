# Dashboard screenshot protocol

The extracted report and compiled PBIT contain the approved six-page story. I publish PNG evidence only after a complete DirectQuery refresh against the canonical SQL model and a visible desktop review.

The approved capture order is:

1. `Inicio`;
2. `01 · Panorama histórico`;
3. `02 · Ventaja y estabilidad`;
4. `03 · Perfil y ofensiva`;
5. `04 · Pico y actualidad`;
6. `05 · Método y evidencia`.

For each of the six pages, the capture must:

1. preserve the native 1320-pixel-wide page and its 750/760-pixel page height at a consistent desktop zoom;
2. keep the mouse cursor outside the report canvas;
3. show no loading spinner, error banner or selection outline;
4. use the real six-CSV run, never the synthetic test fixture;
5. record refresh date, `65,642` unique games and `1946–2022` coverage in the accompanying evidence;
6. reconcile visible totals with `CODE/SQL/30_reconciliation.sql` and `evidence/NBA-Visual-Storytelling/insight_snapshot.json`;
7. preserve the question → evidence → headline sequence and show no more than three analytical charts on any page.

The public portfolio gallery is in `powerbi_storytelling/` and intentionally contains four representative views rather than six near-duplicate screenshots:

1. `01_inicio_storytelling.png`;
2. `02_panorama_historico.png`;
3. `03_perfil_ofensiva.png`;
4. `04_metodo_evidencia.png`.

The compiled PBIT, extracted source and machine-readable insight snapshot remain the primary reproducibility evidence.
