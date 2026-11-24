# SEED 2.0 baseline audit

2026-11-24. The clean starting checkout was `main` at
`fde88957238bd3bc28e80e1fe0b252a64507b108` (90 tracked files). Fetch and
push remotes were `origin` at RiyDomingo/seed-skill and `upstream` at
Jakeschincariol/seed-skill. The fork contains one commit at baseline.
Development moved to `development/seed-2.0`.

The baseline pairs each of 11 root skills with an independent Python standard-library
CLI. The tools exchange unversioned JSON under `seed/`. Templates and sample
inputs live beside their scripts. Tests exercise CLI entry points and library
functions. Fixtures include Apple feeds, EDGAR search results and XML, venture
JSON, a calendar event, SAFE text, and mocked reply data. No build, CI,
runtime dependency manifest, cloud store, or automated connector is present.

| Component | Disposition | Inputs, outputs and principal findings |
| --- | --- | --- |
| Scout | ADAPT | Apple iTunes search, lookup and review feeds or offline fixtures → reviews and competitors JSON. Keyword counts are reproducible but sampling and theme labels cannot establish product performance. Keep Apple as an optional adapter. |
| Market | REFACTOR | CLI quantities and source labels → TAM/SAM/SOM JSON. Decimal arithmetic and ordering checks are tested. Source labels are self-reported and segments lack overlap controls. |
| Model | REFACTOR | Assumptions JSON → 36-month marketplace forecasts and CSV. Decimal calculations have hand-computed fixtures. The revenue model and cash assumptions are narrow and lack a balance sheet and manufacturing economics. |
| Plan | ADAPT | Config and founder prose plus model, market and competitors JSON → plan JSON and Markdown. Checks can match unrelated numbers with the same magnitude. Flagged materials can still be rendered. |
| Deck | ADAPT | Plan and upstream JSON → standalone HTML and lint. Escaping and numeric checks have tests. Lint is heuristic and build writes despite lint issues. |
| Investors | REFACTOR | Curated CSV/JSON and optional EDGAR XML → ranked investors and issuer leads. Scores blend inferred fit with missing evidence. Form D reporting alone does not establish investor participation. |
| Closer | REFACTOR | Config, investor records, template and reply exports → pipeline, EML and ICS. Local CLI performs no external delivery. Legacy instructions trust connector names and preview only one complete message before batch approval. |
| Coach | ADAPT | Question bank plus optional workspace and ICS → drills, heuristic grading and agendas. Generic fallback works. Hardcoded Eastern-time assumptions and keyword grading limit portability and accuracy. |
| Terms | REFACTOR | Shares, cap table, post-money SAFE parameters and plain text → dilution model and keyword findings. Fraction arithmetic is tested for supported conventions. Agreement interpretation, pre-money instruments and individual provisions need distinct models. |
| Dataroom | REFACTOR | Local file paths and timestamps → checklist, index and disclosure candidates. Filename heuristics do not determine sensitivity and file links can leave the room. |
| Updates | ADAPT | Metrics and optional config → Markdown drafts. Runway and MoM are deterministic with fixtures. Reported metrics have no shared provenance schema. |
| Tests and fixtures | RETAIN | Standard-library unittest, app and SEC network simulations, CLI and cross-file fixtures. Replace assertions that hardcode promotional text and Claude path syntax. |
| Claude manifests | ADAPT | Keep existing root manifest and attribution for historical plugin users. Verify supported local copy locations independently. |
| README and licence | ADAPT / RETAIN | Rewrite the README around portable installation and legacy limitations. Preserve the MIT licence and author attribution verbatim. |

The main pipeline is scout/market/model → plan → deck, and investors → closer → coach.
Updates and terms consume their own data. Tools are portable Python, while the
instructions assume a Claude skill directory variable and in some cases named
Gmail/Calendar tools. Investor EDGAR lookup has a separate user-agent setting.
