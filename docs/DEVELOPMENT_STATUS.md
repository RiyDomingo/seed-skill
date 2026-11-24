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

**Programme status: INCOMPLETE.** P2 is active. The
[requirements matrix](REQUIREMENTS.md) tracks remaining gates.

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

The remaining programme phases are P2 workspace, evidence and recovery, P3
fundraising operations, P4 financial and capital modelling, P5 research and
non-dilutive funding, P6 investment readiness and auditing, P7 full
integration and P8 release preparation. The nine new skills and the seven
venture-archetype end-to-end scenarios are future phase acceptance work.
