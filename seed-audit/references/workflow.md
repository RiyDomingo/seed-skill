# Venture Evidence Audit workflow

Run `python3 scripts/seed_workspace.py --workspace PATH ...`.

Run `readiness audit YYYY-MM-DD` with optional repeated --id filters.
Assert figures on materials with key, unit, value, numeric, source_id,
revision and path into the source data. The source revision must also be
pinned by that material. An assertion key names the same measure, period
and scenario across materials. Review discrepancies, missing provenance,
financial identities and visibility violations. Findings carry severity
and record references. Blocking findings prevent investment-ready status.
Use manual verification of external source availability and scientific claims.
