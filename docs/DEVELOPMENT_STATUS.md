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

The next engineering phase is P2. Start with the private workspace and evidence
registry schemas, then implement validated, non-destructive import and recovery.
Outstanding P1 host checks can use a temporary Codex project and an eligible
ChatGPT workspace with synthetic data.

## P1R operational qualification

**Programme status: INCOMPLETE.** P1R is the active phase. P2 through P8 depend
on acceptance of P1R under the completion mandate.

- Codex project discovery and live invocation passed for the eleven P1
  skills. An isolated runtime resolved the local SQLite startup blocker.
  Live tests used a supported model with the configured account.
- Claude Code standalone discovery passed for all eleven. Live invocation
  requires an authenticated Claude account.
- ChatGPT and Work operational qualification requires an eligible signed-in
  workspace with skill upload and execution access.
- Installer publishing, link handling and outreach approval consistency were
  hardened. The nine-job CI matrix and extracted package execution test are
  present. CI results will be recorded after the authorised development
  branch push.
- Independent reviewers checked P1 confidentiality, execution, test coverage
  and the available requirements. The separately referenced P1R and P2
  prompts did not surface in the repository, available attachments or
  discoverable relevant chat history. Use the original master and completion
  mandate as the known requirements pending those supplementary specifications.

Execute the exact remaining platform checks in
[P1R qualification](audit/P1R_QUALIFICATION.md). After P1R passes, begin the
P2 SQLite workspace, record and revision schemas, legacy import and backup
recovery gates described in the [roadmap](DEVELOPMENT_ROADMAP.md).
