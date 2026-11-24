# P2 shared venture knowledge architecture

## Storage and identity

Use SQLite as the private per-venture system of record and JSON as a bounded
portable exchange and recovery format. Standalone JSON is simple to inspect
but cannot guarantee transactional multi-record import, referential integrity
or concurrent revision updates. SQLite provides those properties without
a service. Documents remain separate files referenced by safe relative path
and hashed at registration. CSV stays an interchange format for individual
skills.

Each workspace has one random venture ID and a schema version. A stable
entity ID derives from that ID and the normalized kind and natural key.
Revision rows are immutable, timestamped in UTC, classified and hashed with
their pinned links. CAS updates and transactional imports prevent accidental
overwrites. Locked or interrupted transactions roll back.

## Versioned records

The schema includes venture preferences, sources, evidence, claims,
assumptions, calculations, market records, competitors, financial models,
investors, investment firms, contacts, relationships, funding opportunities,
interactions, fundraising opportunities, technical milestones, documents,
decisions and legacy JSON snapshots.

Every record has version, identity, provenance, validation status,
classification and links. Provenance distinguishes verified external,
founder, assumption, estimate, hypothesis, calculated and unknown. External
claim records require reviewed evidence. Evidence pins a source. Links can
record conflicting evidence and pin the exact assumptions used to produce
calculations and documents. Trace reports highlight challenged claims,
expired sources and stale revisions. Updating one input surfaces affected
downstream outputs without editing approved artifacts.

## Migration, isolation and exchange

The migration allowlist inventories original JSON filenames, supports a dry
run and quarantines malformed or linked files with redacted diagnostics.
Original input files are read-only. Repeated imports are idempotent and
mismatched snapshots require a deliberate revision. Legacy filename
association is provenance-unknown. Use explicit pinned links when capturing
fresh outputs.

The portable format checks version, venture ID, checksum, classification,
complete histories, dependency closures and import conflicts. Transfer bytes
are selected explicitly, reviewed by digest and delivered via local output
or manual upload/download to the intended host. Restricted records and raw
legacy snapshots are excluded from exchanges. Complete private backups are
stored within the workspace and restore into a different directory.

Managed workspaces and outputs refuse Git-backed paths. Linked database and
document paths are refused. The tool rejects standard credential fields and
known token patterns. These checks supplement the founder's review of the
contents, recipient and disclosure scope. A checksum detects payload drift
without establishing author identity.

## Dependency map

| Producer | Typical consumers | Original files or shared records |
| --- | --- | --- |
| Scout | Market, plan, deck, coach | Competitor profiles and `competitors.json` |
| Market | Model, plan, deck, coach | Sizing claims, inputs and `market.json` |
| Model | Plan, deck, terms, updates | Assumptions, calculations and `model.json` |
| Plan | Deck, closer, dataroom | `plan.json` and registered plan document |
| Investors | Closer, coach | Investor records and `investors.json` |
| Closer | Coach, updates | `pipeline.json` and draft artifacts |
| Coach | Plan, deck | Practice and meeting evidence |
| Terms | Plan, dataroom | Dilution calculations and term evidence |
| Deck, dataroom, updates | Review, investor preparation | Classified document revisions |

Ship one canonical workspace adapter in every skill package. Its local
commands import or capture upstream data, materialize snapshots when the
original tools need JSON, and register new artifacts. Each original CLI
remains usable from its original entry point.

The [workspace guide](../WORKSPACE.md) describes portable commands. Acceptance
requires offline tests, actual transfer to and back from hosted runtimes,
legacy contract regressions and a verified backup restore.
