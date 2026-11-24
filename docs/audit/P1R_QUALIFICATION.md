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
the following from the SEED checkout. Submit the smoke prompt below using
`/seed-model` in place of `$seed-model`.

```sh
seed_demo="$(mktemp -d)"
python3 scripts/skills.py install claude --project "$seed_demo"
cd "$seed_demo"
claude --setting-sources project --strict-mcp-config --no-session-persistence
```

[Claude Code authentication](https://code.claude.com/docs/en/authentication)

## ChatGPT and ChatGPT Work

**Blocked at browser sign-in.** The available ChatGPT web tab opened in a
logged-out session. The installation path needs an eligible workspace and
permission to upload skills. The popup account and workspace eligibility have
yet to be verified. A normal message with an attached ZIP does not establish
skill installation.

1. Sign in to an eligible workspace. Open **Plugins → Skills → Create →
   Upload from your computer**. If **Create** or the upload option is missing,
   have a workspace admin verify that skills and skill uploading are enabled.
2. Select the generated `dist/p1r/seed-model.zip`. Keep access private and
   confirm the scan accepts it and the skill appears as installed.
3. Start a new Chat test and invoke the installed skill using the picker.
   Run the same test in Work if the installed skill is available there.
4. Record the workspace surface, scan result, original skill name, execution
   evidence and downloadable artifacts. Then repeat with the remaining skills
   using the synthetic cases in `tests/test_packaged_workflows.py`.

Smoke prompt for Codex, Claude Code, ChatGPT and Work:

> Use the installed seed-model skill. Read its bundled workflow and use the
> bundled Python script with the synthetic assumptions to initialise a new
> venture model, write its 36-month model JSON and export CSV. Return both
> files and the calculated break-even month. Keep all activity local to the
> test environment and use no connectors.

A pass requires tool or execution evidence of reading the installed reference
and running `model.py`, two freshly generated output files, 36 monthly rows
and break-even in month 29. A text-only result does not establish execution.

[ChatGPT skill upload and workspace controls](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)

## Regression and CI evidence

Local regressions cover publishing without replacement or hard-link
requirements, redirected host paths, the ZIP-to-CLI workflow across all eleven
skills, and draft authorization and confidentiality boundaries. GitHub Actions
is configured for macOS, Linux and Windows with Python 3.12, 3.13 and 3.14.
See the authoritative [development status](../DEVELOPMENT_STATUS.md) for the
latest CI run and qualification gate.
