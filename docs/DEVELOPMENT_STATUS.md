# Development status

## P0 baseline audit

Complete on 2026-11-24. The four audit reports and roadmap record the baseline,
architecture, test run and release boundaries. Baseline suite passed 181 tests.
P1 must address approval payload and path containment findings before acceptance.

## P1 portable foundation

Implemented and locally verified on 2026-11-24. Platform acceptance is partial.

- All eleven SKILL.md entry points, workflow references and OpenAI metadata
  use the same canonical root folders. The original Python commands and
  legacy workspace contracts remain available.
- `scripts/skills.py` generates scoped installs and one ZIP per skill. The
  installer copies only allowlisted files and preserves existing targets.
- Closer reviews all messages and thread details, validates approval snapshots
  and exports for manual delivery. New approvals are required for old outbox
  drafts. Data-room review skips linked files and refuses a linked index.
- README, installation and workspace instructions, AGENTS.md, changelog,
  ignore rules and the optional EDGAR environment example are in place.
- [P1 verification results](audit/P1_TEST_RESULTS.md) record tests and host
  limits. The full SEED 2.0 release remains outside P1.

## P1R operational qualification

**P1R_ACCEPTED** under the founder's OpenAI-only scope. Claude Code is
`OUT_OF_SCOPE`. Codex, ChatGPT and ChatGPT Work installed and invoked each of
the eleven original skills. The synthetic runs each completed 17 tool calls.
All nine CI jobs passed with 190 tests. See the
[qualification evidence](audit/P1R_QUALIFICATION.md).

**Programme status `COMPLETE`** for the OpenAI scope. The
[requirements matrix](REQUIREMENTS.md) and
[release acceptance report](audit/RELEASE_ACCEPTANCE.md) record each gate.

### Git checkpoints and test runs

- `eb5fb86234c5b983a46626998de33ef3b4de0243` contains the P1 migration,
  P1R safeguards and CI. [The first CI run](https://github.com/RiyDomingo/seed-skill/actions/runs/45431721569)
  exposed Windows CLI path-separator assumptions in six tests.
- `69576581c2f7e2ce5f76ab8009b2a48f1f1003f1` uses native path expectations
  in the affected tests. [The rerun](https://github.com/RiyDomingo/seed-skill/actions/runs/45432132612)
  passed all Linux and Windows jobs. ARM macOS jobs were cancelled before a
  runner started.
- `1a371fa8fadd7e2c204b024e33d4b9b501865425` switched to GitHub's
  `macos-26-intel` label. [The final CI run](https://github.com/RiyDomingo/seed-skill/actions/runs/45435865850)
  passed all nine jobs for Linux, macOS and Windows across Python 3.12,
  3.13 and 3.14. Locally, 190 tests also passed under Python 3.12.7, 3.13.1
  and 3.14.7 on macOS.

## P2 shared venture knowledge

SQLite workspace, revision, provenance and recovery commands are functional.
The legacy adapter integrated materialized inputs with the bundled plan
tool and registered the new JSON and Markdown outputs against pinned
inputs. The current regression suite passed 202 tests locally.

An installed Codex skill imported and traced a public synthetic baseline.
Chat and Work imported it independently, revised separate assumptions, and
returned public bundles. Both replies imported into the original venture
with revision histories intact. The installed Codex package also imported both
replies and verified three records and five revisions. Two stale dependency
findings preserve the original pinned inputs for review.
Full private backups and raw legacy snapshots remained local.

Independent review identified and the implementation corrected secret-bearing
keys and metadata, malformed legacy collections, revision dependency cycles,
JSON type equality, linked or ambiguous paths, oversized recovery and stale
legacy handoffs. See the [P2 specification](specifications/P2_SPECIFICATION.md)
and [workspace guide](WORKSPACE.md).

## P3 fundraising operations

The shared workspace now supports configurable investor fit with separate
coverage and evidence confidence, introduction paths, a persistent CRM,
permanent opt-out and bounce suppression, and approval-bound local EML
export. The meeting brief ties preparation to linked investor and venture
records. The closer supports local reply parsing and an exact approval gate for
ICS files in the shared venture workflow. The CRM does not perform external delivery. Live workflows using
the new skills will be qualified in P7.

The local suite passed 206 tests after P3 implementation.

## P4 financial and capital architecture

The shared model covers 36/60-month forecasts, alternative business streams,
manufacturing capacity and yield, inventory, receivables and payables aging,
cash reconciliation, milestones and funded/unfunded comparisons. CSV and
XLSX consume the validated saved scenarios. Explicit term inputs support
mixed pre/post-money SAFEs, simple-interest notes, allocation, preferences
and ownership adjustments. Legacy model and terms commands remain available.

Independent review identified and the implementation corrected accrual
timing, opening obligations, sensitivity baseline, manufacturing rounding
and duplicate holder issues. Tests include independently calculated figures.
Term results use the supplied agreement conventions and scenario assumptions.

## P5 research and non-dilutive funding

The shared intelligence CLI ingests source observations with pinned
references, builds general competitor comparisons and market scenarios,
and screens grants, accelerators and patent families. Public research uses
host-provided capabilities. Automated verification uses synthetic sources
only and makes no claims about live opportunity status.

The local suite passed 219 tests after P5 implementation.

## P6 readiness and diligence

The shared CLI runs technical and business readiness rubrics, checks
claim and figure consistency, inventories disclosure candidates, and
evaluates five structured committee perspectives. The legacy document
commands remain available. Shared plans, decks and updates export local
review drafts and retain pinned evidence references. Free narrative
requires semantic review before sharing. Pinned evidence and arithmetic
checks cover the structured assertions.

Independent review reproduced insufficient disclosure filtering, draft
approval bypasses, malformed forecasts and review-candidate false
positives. The disclosure and approval paths now fail closed and have
focused regression tests.

## P7 integration and operational qualification

All twenty packages ran their bundled scripts in synthetic integration
tests. Seven scenarios cover SaaS, marketplace, manufacturing, hardware,
biotechnology, medical technology and hybrid hardware/AI. The base suite passed 228 tests on Python 3.12, 3.13 and 3.14.
The current candidate passed 229 local tests and nine hosted CI jobs. All twenty base candidate skills also ran through native installation
and invocation in ChatGPT, Work and Codex. The nine hosted CI jobs passed
for that checkpoint. See [operational qualification](audit/P7_QUALIFICATION.md)
for the host runs, updated calendar checks and same-workspace resume.
[Current CI results](https://github.com/RiyDomingo/seed-skill/actions/runs/45454811087).

## P8 release preparation

The local candidate builder verifies all twenty ZIPs against the exact
canonical source files and writes a SHA256 manifest. The installation,
developer and privacy guides describe first use, verified record exchange,
migration, recovery and external action approval. The current ZIP set
matches the tested candidate checkpoint `9679f8b`. See the
[acceptance report](audit/RELEASE_ACCEPTANCE.md).
