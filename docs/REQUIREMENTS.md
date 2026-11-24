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
| P3 | Investor qualification, network, persistent CRM and approval-bound outreach | seed_core/fundraising.py, tests/test_network.py and tests/test_crm.py | Implemented and tested locally |
| P4 | 36/60-month venture models, scenarios, capital and dilution | seed_core/finance.py, dilution.py, model_export.py and tests/test_capital.py | Implemented and tested locally |
| P5 | Competitor, market, patents, grants and accelerator intelligence | seed_core/intelligence.py and tests/test_grants.py, test_patents.py, test_accelerators.py | Implemented and tested locally |
| P6 | Readiness, diligence, committee and independent cross-document audit | seed_core/diligence.py and tests/test_audit.py, test_readiness.py, test_committee.py | Implemented and tested locally |
| P7 | Full integration and operational qualification | tests/test_system.py, P1R and current-build qualification receipts, and nine hosted CI jobs | Seven local scenarios, 20 base-candidate invocations per host and nine base-candidate CI jobs passed. Focused calendar requalification tracked in P7 report |
| P8 | Release-ready source, packages, docs and onboarding | scripts/release.py, developer and security guides, release acceptance report | Local candidate verified. Release acceptance pending |

The original master brief and completion mandate remain applicable within
the revised platform scope. The acceptance status and evidence links are
maintained in [development status](DEVELOPMENT_STATUS.md).

See [operational evidence](audit/P7_QUALIFICATION.md) and [release acceptance](audit/RELEASE_ACCEPTANCE.md).

Detailed requirements are in [programme scope](specifications/SEED_2.0_REQUIREMENTS.md),
[P2 specification](specifications/P2_SPECIFICATION.md) and
[platform qualification](specifications/PLATFORM_QUALIFICATION.md).
