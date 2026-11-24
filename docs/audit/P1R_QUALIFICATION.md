# P1R operational qualification

Evidence collected on 2026-11-24 from the public synthetic Leashly venture and
a separate mock outreach directory. Host and platform results below apply to
the original eleven skills. The final twenty-skill qualification remains a
P7 acceptance requirement.

## Codex

**PASSED for all eleven project skills.** Codex CLI 0.159.3 discovered all eleven
as enabled via app-server `skills/list` after installation under
`.agents/skills`. Starting app-server against the shared runtime previously
failed on SQLite initialization or stalled on the backfill. A fresh
process-specific Codex runtime in a temporary directory resolved discovery
without modifying the existing database. Discovery does not require sign-in.

Authenticated `codex exec` from a temporary project with workspace-write
sandboxing reached the provider. The configured model was rejected with
`model_not_found`. Using `--model gpt-6.1-sol` for the test succeeded.
An explicit `$seed-model` invocation read the installed workflow and created
36 months of JSON and CSV output. A second live invocation requested all
eleven installed skills, read the installed instructions and references, then
ran 17 bundled CLI commands. All 17 exited 0.

| Skill | Observed output |
| --- | --- |
| Scout | Offline competitor comparison and review cache from recorded Apple response fixtures |
| Market | $10,000 TAM with three labeled assumptions in a separate output directory |
| Model | Bundled assumptions and matching 36-month model JSON and CSV |
| Plan | Business plan JSON and Markdown with clean checks |
| Deck | Standalone HTML with clean lint |
| Investors | Imported and ranked six synthetic investors |
| Closer | One EML and matching JSON batch preview for the synthetic contact |
| Coach | Three tailored drill questions in Markdown |
| Terms | 5% ownership at the cap in SAFE JSON |
| Dataroom | Nine local folders and an index reporting 25 missing checklist items |
| Updates | November draft with computed metrics and runway |

The live commands left the staged venture market record unchanged and performed
no contact, approval or invitation. The user install destination was covered
by the installer tests. Live user-scope discovery was not exercised.

To repeat the minimal authenticated Codex case, run from the checkout and use a
model available to the signed-in account.

```sh
seed_demo="$(mktemp -d)"
python3 scripts/skills.py install codex --project "$seed_demo"
codex exec --model gpt-6.1-sol --ephemeral --json --skip-git-repo-check \
  --sandbox workspace-write -C "$seed_demo" \
  '$seed-model Read the installed workflow reference, initialise the bundled synthetic assumptions with model.py, then generate model JSON and CSV locally.'
```

Review the JSON events for the command trace and inspect
`$seed_demo/seed/model.json` and `$seed_demo/seed/model.csv`.

Sources

- [Codex app-server](https://learn.chatgpt.com/docs/app-server)
- [Codex models](https://learn.chatgpt.com/docs/models)
- [Non-interactive Codex operation](https://learn.chatgpt.com/docs/non-interactive-mode)
- [Related upstream SQLite backfill report](https://github.com/openai/codex/issues/52836)

## Claude Code

**Discovery passed. Live model invocation blocked by sign-in.**
An independent reviewer installed the eleven skills into a temporary
`.claude/skills` directory. Claude Code 2.1.259 returned all eleven in both
`skills` and `slash_commands` in its startup event. A synthetic
`/seed-terms` turn returned `Not logged in`. A separate authentication
check with normal access confirmed no active session. Direct invocation of
the installed Python command produced the expected SAFE output. The command
run remains separate from the Claude model result.

After running `claude auth login` and confirming `claude auth status`, use
the following from the SEED checkout. Prefix the smoke prompt below with `/seed-model`.

```sh
seed_demo="$(mktemp -d)"
python3 scripts/skills.py install claude --project "$seed_demo"
cd "$seed_demo"
claude --setting-sources project --strict-mcp-config --no-session-persistence
```

[Claude Code authentication](https://code.claude.com/docs/en/authentication)

## ChatGPT and ChatGPT Work

**PASSED for the eleven P1 skills on both surfaces.** The first browser session
was signed out. A signed-in browser profile exposed the workspace's upload
control. The ZIP pilot was accepted and appeared under Installed. Its detail
page showed the actual workflow, model script and bundled assumptions. The
other ten ZIPs each reported Skill uploaded. No sharing controls were used.

The pilot explicitly selected Financial Modeler from the composer on both
surfaces. Chat and Work each returned 36-month model JSON and CSV with break-even
in month 29 from the bundled assumptions. Then each surface selected all eleven
installed skills and ran against one reviewed synthetic fixture archive.

| Check | Chat | Work |
| --- | --- | --- |
| Installed skills selected | 11 | 11 |
| Bundled CLI commands with exit code 0 | 17 | 17 |
| Downloaded execution JSON and output ZIP | Verified | Verified |
| Installed script hashes match canonical local files | 11 of 11 | 11 of 11 |
| Downloaded outputs matched test expectations | Passed | Passed |

Both archives contained the generated model, market estimate, plan, deck, coach
drill, SAFE result, data-room index and investor update. They also contained
a synthetic EML and a pipeline still marked drafted. The downloaded JSON
execution receipts contain command arguments, exit codes, paths and output
metadata. Independent checks verified the fixture-equivalent financial model,
36 CSV rows, a USD 10,000 TAM and a 5% at-cap SAFE interest. The Chat archive
contains the unchanged staged market file. The Work receipt records matching
before and after hashes for that file.

For another eligible workspace, open **Plugins → Skills → Add skill → Upload
from your computer** and upload a ZIP from `dist/p1r/`. Select the installed
skill with `@` in a fresh Chat or Work composer. Check the selected skill and
attachments before submitting. If the upload option is absent, the workspace
admin can check the skill upload settings.

Smoke prompt for Codex, Claude Code, ChatGPT and Work:

> Use the installed seed-model skill. Read its bundled workflow and use the
> bundled Python script with the synthetic assumptions to initialise a new
> venture model, write its 36-month model JSON and export CSV. Return both
> files and the calculated break-even month. Keep all activity local to the
> test environment and use no connectors.

A pass requires tool or execution evidence of reading the installed reference
and running `model.py`, two freshly generated output files, 36 monthly rows
and break-even in month 29. After Claude authentication, repeat the workflow
for all eleven using the synthetic input and output cases in
`tests/test_packaged_workflows.py`. Keep model logs and outputs local and use
the reported artifacts to check exit codes and generated values.

[ChatGPT skill upload and workspace controls](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)

## Regression and CI evidence

Local regressions cover publishing without replacement or hard-link
requirements, redirected host paths, the ZIP-to-CLI workflow across all eleven
skills, and draft authorization and confidentiality boundaries. GitHub Actions
is configured for macOS, Linux and Windows with Python 3.12, 3.13 and 3.14.
See the authoritative [development status](../DEVELOPMENT_STATUS.md) for the
latest CI run and qualification gate.

The initial hosted ARM macOS jobs did not acquire a runner and were cancelled
before executing any steps. The matrix was rerun with the standard
`macos-26-intel` label. All nine GitHub Actions jobs completed successfully
for Python 3.12, 3.13 and 3.14 on Linux, macOS and Windows.

- [Passing GitHub Actions run](https://github.com/RiyDomingo/seed-skill/actions/runs/45435865850)
- [Related runner queue issue](https://github.com/actions/runner/issues/4833)
- [GitHub-hosted runner labels](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
