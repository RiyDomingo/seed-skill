# SEED 2.0 requirements and acceptance

| ID | Requirement | Implementation and evidence | Status |
| --- | --- | --- | --- |
| P0 | Baseline audit, MIT and upstream attribution | [Baseline audit](audit/BASELINE_AUDIT.md) and [MIT licence](../LICENSE) | Accepted |
| P1 | Migrate 11 skills and retain original contracts | [Packaged regression](../tests/test_packaged_workflows.py) | Accepted |
| P1R | Native execution and hosted CI for the original eleven | [Original qualification](audit/P1R_QUALIFICATION.md) | `P1R_ACCEPTED` |
| SCOPE | Supported hosts and platform boundaries | [Compatibility matrix](audit/COMPATIBILITY_MATRIX.md) | ChatGPT, ChatGPT Work and Codex supported. Claude Code `OUT_OF_SCOPE`. |
| P2-A | Explicit private workspaces, isolation and atomic writes | [Workspace code](../seed_core/workspace.py) and [workspace tests](../tests/test_workspace.py) | Accepted |
| P2-B | Typed shared schemas, provenance and revision history | [Validation](../seed_core/schema.py) and [P2 specification](specifications/P2_SPECIFICATION.md) | Accepted |
| P2-C | Evidence, freshness, dependencies and uncertainty | [Evidence graph](../seed_core/workspace.py) and [workspace tests](../tests/test_workspace.py) | Accepted |
| P2-D | Non-destructive migration, idempotence and recovery | [Legacy adapter](../seed_core/legacy.py), [backup and restore](../seed_core/recovery.py) and [workspace tests](../tests/test_workspace.py) | Accepted |
| P2-E | Portable shared resources and explicit exchange across hosts | [Typed exchange](../seed_core/transfer.py), [package tests](../tests/test_packaging.py) and [round-trip results](DEVELOPMENT_STATUS.md#p2-shared-venture-knowledge) | Accepted |
| P2-F | Confidentiality filtering, safe paths and integrity | [Workspace tests](../tests/test_workspace.py) and [privacy guide](SECURITY.md) | Accepted |
| P3-A | Sourced investor fit, confidence and introduction paths | [Fundraising engine](../seed_core/fundraising.py), [network tests](../tests/test_network.py) and [synthetic programme](../tests/test_system.py) | Passed |
| P3-B | Persistent CRM, suppression, approved EML and ICS handoff | [Calendar export](../seed-closer/scripts/seed_calendar.py), [CRM tests](../tests/test_crm.py) and [native receipts](audit/P7_QUALIFICATION.md) | Passed |
| P4-A | Deterministic 36/60-month models, cash reconciliation and spreadsheets | [Forecast](../seed_core/finance.py), [exporter](../seed_core/model_export.py) and [financial tests](../tests/test_capital.py) | Passed |
| P4-B | Milestone capital, scenarios, SAFE, notes and dilution | [Instrument math](../seed_core/dilution.py) and [financial tests](../tests/test_capital.py) | Passed |
| P5-A | Competitor evidence, TAM/SAM/SOM and patent landscape | [Research engine](../seed_core/intelligence.py), [patent tests](../tests/test_patents.py) and [synthetic programme](../tests/test_system.py) | Passed |
| P5-B | Grants and accelerator eligibility, economics and status | [Grant tests](../tests/test_grants.py) and [accelerator tests](../tests/test_accelerators.py) | Passed |
| P6-A | Reviewed plans, decks, updates and numeric traceability | [Diligence engine](../seed_core/diligence.py), [audit tests](../tests/test_audit.py) and [host format checks](audit/P7_QUALIFICATION.md) | Passed |
| P6-B | Independent perspectives, technical readiness and disclosure | [Readiness tests](../tests/test_readiness.py), [committee tests](../tests/test_committee.py) and [privacy guide](SECURITY.md) | Passed |
| P7-A | Seven synthetic, end-to-end venture archetypes | [Extracted package integration](../tests/test_system.py) and [operational report](audit/P7_QUALIFICATION.md) | Passed |
| P7-B | All 20 native skills, security and cross-platform tests | [Operational report](audit/P7_QUALIFICATION.md) and [release acceptance](audit/RELEASE_ACCEPTANCE.md) | Passed |
| P8 | Reproducible installation, distribution and evidence | [Candidate builder](../scripts/release.py), [installation](INSTALLATION.md), [user guide](USER_GUIDE.md) and [developer guide](DEVELOPER.md) | Accepted |

[Development status](DEVELOPMENT_STATUS.md) records the tested checkpoints.
The detailed requirements are in [programme scope](specifications/SEED_2.0_REQUIREMENTS.md),
[P2 specification](specifications/P2_SPECIFICATION.md) and
[platform qualification](specifications/PLATFORM_QUALIFICATION.md).
