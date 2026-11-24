# SEED 2.0

SEED helps founders research markets, build fundraising materials, prepare for
investor conversations, and track outreach. The supported platforms are ChatGPT, ChatGPT Work and OpenAI Codex.
The portable foundation includes
the original eleven workflows and their deterministic Python tools. The current
financial model covers a 36-month marketplace forecast. Expanded venture
models and the evidence registry are scheduled in the roadmap.

## Skills

| Skill | Local workflow |
| --- | --- |
| seed-scout | Compare App Store competitors, reviews and pricing |
| seed-market | Calculate and document TAM, SAM and SOM |
| seed-model | Forecast marketplace economics, cash and runway |
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

## Quick start

Use Python 3.12 through 3.14. From the checkout, create an empty private directory outside
the repository and install the project skills there. A temporary directory is
suitable for this synthetic exercise.

```sh
seed_demo="$(mktemp -d)"
python3 scripts/skills.py install codex --project "$seed_demo"
cd "$seed_demo"
python3 .agents/skills/seed-model/model.py init
python3 .agents/skills/seed-model/model.py run --write
python3 .agents/skills/seed-model/model.py csv
```

The example uses synthetic marketplace assumptions and writes
`seed/model.json` and `seed/model.csv`. In a new Codex session rooted at
the demo directory, ask `$seed-model` to explain the model's runway and
its assumptions. Use a separate directory for each real venture.

[Installation](docs/INSTALLATION.md) · [Private workspaces](docs/WORKSPACE.md) ·
[Phase status](docs/DEVELOPMENT_STATUS.md) ·
[Development roadmap](docs/DEVELOPMENT_ROADMAP.md) ·
[Changelog](CHANGELOG.md)

## Licence

SEED 2.0 is based on the [original Seed skill pack](https://github.com/Jakeschincariol/seed-skill)
by Jake Schincariol. See the [MIT licence](LICENSE).
