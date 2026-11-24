# SEED 2.0

SEED helps founders research markets, build fundraising materials, prepare for
investor conversations, and track outreach. The supported platforms are ChatGPT, ChatGPT Work and OpenAI Codex.
The platform includes twenty skills, a private SQLite venture workspace,
an evidence and assumption registry, and deterministic 36- and 60-month
financial models. Check the development status for operational acceptance.

## Skills

| Skill | Local workflow |
| --- | --- |
| seed-scout | Compare sourced competitors, features and evidence quality |
| seed-market | Calculate and document TAM, SAM and SOM |
| seed-model | Build venture forecasts, scenarios and cash reconciliations |
| seed-plan | Build a business plan from existing venture records |
| seed-deck | Generate and lint a self-contained HTML deck |
| seed-investors | Rank sourced investor records and research EDGAR issuers |
| seed-closer | Draft outreach and calendar files and review the local pipeline |
| seed-coach | Rehearse pitch questions and prepare investor agendas |
| seed-terms | Model post-money SAFE and priced round dilution and screen clauses |
| seed-dataroom | Inventory due diligence files and review disclosure candidates |
| seed-updates | Draft monthly updates from operating metrics |
| seed-network | Map evidence-backed introductions and possible pathways |
| seed-crm | Maintain the private fundraising pipeline and outreach history |
| seed-capital | Compare reserve gaps, financing dates and instrument effects |
| seed-grants | Identify, verify and screen non-dilutive opportunities |
| seed-accelerators | Screen programmes by fit, rules, economics and founder time |
| seed-patents | Group prior-art leads, families and reported legal status |
| seed-readiness | Assess evidence for technical and investment readiness |
| seed-audit | Trace and reconcile cross-document claims and figures |
| seed-committee | Run a structured investment committee assessment |

## Quick start

Use Python 3.12 through 3.14. From the checkout, create an empty private directory outside
the repository and install the project skills there. A temporary directory is
suitable for this synthetic exercise.

```sh
seed_demo="$(mktemp -d)"
python3 scripts/skills.py install codex --project "$seed_demo"
cd "$seed_demo"
python3 .agents/skills/seed-model/scripts/seed_workspace.py --workspace . init \
  --name "Synthetic venture" --currency USD --jurisdiction US
python3 .agents/skills/seed-model/scripts/seed_workspace.py --workspace . validate
```

Open a fresh Codex session in the demo directory and invoke `$seed-model`.
For a reproducible synthetic run across seven venture types, use the
[developer guide](docs/DEVELOPER.md). Keep real venture workspaces outside
this checkout and review the [privacy and security guide](docs/SECURITY.md).

[Installation](docs/INSTALLATION.md) · [Private workspaces](docs/WORKSPACE.md) ·
[Phase status](docs/DEVELOPMENT_STATUS.md) ·
[Development roadmap](docs/DEVELOPMENT_ROADMAP.md) ·
[Changelog](CHANGELOG.md)

## Licence

SEED 2.0 is based on the [original Seed skill pack](https://github.com/Jakeschincariol/seed-skill)
by Jake Schincariol. See the [MIT licence](LICENSE).
