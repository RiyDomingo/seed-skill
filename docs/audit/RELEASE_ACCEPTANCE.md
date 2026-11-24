# SEED 2.0 release acceptance

**`COMPLETE`** for the approved OpenAI platform scope. The software
candidate is `9679f8b9508f553df3f6cc7ca5a3f81f43d904ed` on
`development/seed-2.0`.

| Gate | Evidence | Decision |
| --- | --- | --- |
| Platform scope | The compatibility matrix covers ChatGPT, ChatGPT Work and Codex. | Claude Code `OUT_OF_SCOPE` |
| P1R | Original eleven skills ran natively in each supported host. The baseline regression count was 190 and all nine CI jobs passed. | `P1R_ACCEPTED` |
| P2 | Private SQLite workspaces, typed revision history, guarded exchange, non-destructive migration and verified recovery. Synthetic records made a round trip through the three supported hosts. | Accepted |
| P3–P6 | Investor qualification and CRM, approved local email and calendar exports, reconciled finance, sourced research, disclosure, readiness and due diligence. | Accepted |
| P7 | Seven end-to-end venture types, independent checks, 229 regressions, all twenty skills in each supported host, and nine hosted CI jobs. | Accepted |
| P8 | Candidate packages, exact source and SHA256 checks, automated installer, onboarding, security and developer guidance, examples and evidence. | Accepted |

The [candidate CI run](https://github.com/RiyDomingo/seed-skill/actions/runs/45454811087)
passed all nine combinations of Linux, macOS and Windows with Python 3.12,
3.13 and 3.14. The local suite passed 229 tests. A base candidate tested
the twenty skills in each host. The calendar update changed only the
Investor Outreach ZIP. The updated package was reinstalled and exercised
in each host. A second Work turn read the existing SQLite workspace and
found the same approved calendar audit record.

The release ZIP includes the twenty individual upload ZIPs and their
manifest. Distribution archive SHA256
`d1144085f0e8123b2f194c14c5b93eb667d6cb66dac7e729f018e1da059ec2b9`.
Verify individual ZIPs against the checkout with
`python3 scripts/release.py verify PATH`. Follow the
[installation guide](../INSTALLATION.md) for private installation.

Operational verification used synthetic inputs. Review narrative draft
claims before sharing. Email and calendar qualification used exact
approvals, local EML/ICS and an audit record for the handoff. External
connector permissions and approval apply to each deployment and action.
The release candidate and evidence are available locally. The tested
source and reports reside on the development branch.

[Requirements](../REQUIREMENTS.md) · [Operational evidence](P7_QUALIFICATION.md) ·
[P1R evidence](P1R_QUALIFICATION.md) · [User guide](../USER_GUIDE.md)
