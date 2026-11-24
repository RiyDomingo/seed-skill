# SEED 2.0 requirements and acceptance

| ID | Requirement | Required evidence | Status |
| --- | --- | --- | --- |
| P0 | Baseline audit, preserve MIT and upstream attribution | Recorded SHA and original tests | Accepted |
| P1 | Migrate 11 skills, retain CLI and file contracts | Formats, packages and regressions | Accepted |
| P1R | OpenAI platform qualification | 11 live invocations per host, 190 tests and nine hosted CI jobs | P1R_ACCEPTED |
| SCOPE | Claude Code | No installation, testing or release gate | OUT_OF_SCOPE |
| P2-A | Isolated multi-venture workspace with atomic writes, stable IDs, schema versions, validation, deduplication and revision history | Workspace tests and transactional concurrency | Verified locally, tests/test_workspace.py |
| P2-B | Shared evidence and assumption registries with provenance, freshness, confidence, limitations and reverse references | Evidence tests and cross-skill consumers | Verified locally, schema.py and workspace.py |
| P2-C | Legacy migration, verified backup/recovery and explicit hosted/local data exchange | Round trips, conflict refusal, no implicit synchronisation or unsafe exports | Verified locally and across Chat, Work and Codex, transfer.py and recovery.py |
| P2-D | Legacy adapters and packaged resources | tests/test_packaging.py and tests/test_packaged_workflows.py | Verified locally |
| P3 | Investor qualification, network, persistent CRM and approval-bound outreach | Verified-source scoring, suppression and workflow tests | Pending |
| P4 | 36/60-month venture models, scenarios, capital and dilution | Reconciled outputs, financing and manufacturing tests | Pending |
| P5 | Competitor, market, patents, grants and accelerator intelligence | Sourced records and freshness tests | Pending |
| P6 | Readiness, diligence, committee and independent cross-document audit | Evidence gates, disclosure controls and refusal tests | Pending |
| P7 | Full integration and operational qualification | Seven synthetic venture scenarios, all 20 live skills in Chat, Work and Codex, and full CI | Pending |
| P8 | Release-ready source, packages, docs and onboarding | Reproducible release and final acceptance report | Pending |

The original master brief and completion mandate remain applicable within
the revised platform scope. The acceptance status and evidence links are
maintained in [development status](DEVELOPMENT_STATUS.md).

Detailed requirements are in [programme scope](specifications/SEED_2.0_REQUIREMENTS.md),
[P2 specification](specifications/P2_SPECIFICATION.md) and
[platform qualification](specifications/PLATFORM_QUALIFICATION.md).
