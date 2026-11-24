# SEED 2.0 development roadmap

| Phase | Deliverable and exit condition |
| --- | --- |
| P0 | Audit all 11 workflows, record the baseline and run upstream tests. |
| P1 | Migrate all 11 to one canonical Agent Skills source per workflow. Generate host install copies and upload archives, preserve local contracts and test critical confidentiality and approval boundaries. |
| P2 | Add a provider-independent Python core and private multi-venture workspaces. Model claims, sources and assumptions with stable IDs, history and freshness. Implement staged legacy import, dry run, backup and restore. |
| P3 | Add the verified investor model, introduction graph, persistent CRM and scoped outbound adapters with explicit payload approval. |
| P4 | Implement monthly scenario models, physical production economics, capital strategy, dilution contracts and exports from validated results. |
| P5 | Add competitor, market, patents, grants and accelerators with sourced findings and freshness checks. |
| P6 | Add technical readiness, disclosure levels, investment committee perspectives and cross-document auditing. |
| P7 | Validate synthetic venture workflows, migrations, failure cases and cross-skill consistency. |
| P8 | Verify installation in supported hosts and produce release documentation and packages. |

Keep the 11 independent CLIs as legacy adapters during migration. P2 should use
SQLite as the transactional source of truth for records, uniqueness and change
history. Use JSON for schema-versioned interchange and CSV for flat exports.
Keep venture documents in the private filesystem with validated relative references.
Skills remain thin workflows. Research interfaces and action adapters depend on core,
while core has no dependency on an agent host or connector.

P2 acceptance requires non-destructive import, repeatable duplicate handling, history
for verified records, and isolated recovery tests before downstream workflows write
shared data. Each later phase updates the development status with verification and risks.
