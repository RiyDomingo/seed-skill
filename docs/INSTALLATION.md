# Install and use the SEED skills

## Codex

Run these commands from the software checkout. Python 3.12 through 3.14 passed the full suite on macOS. Choose project or user scope to avoid duplicate skill names.

```sh
python3 scripts/skills.py install codex --project /absolute/path/to/private-venture
python3 scripts/skills.py install codex --user
```

Project scope creates `.agents/skills` under the selected directory. User scope
writes to `~/.agents/skills`. Run Codex from your private venture directory and
select `$seed-market` or another installed skill. Use a fresh session if an
installed skill is missing. Add `--skill seed-market` to install only that
skill. The installer refuses to overwrite existing copies. To upgrade, move
the old copies out of discovery, then rerun the installer. Keep the old
copies until the new ones load successfully.

[OpenAI authoring and discovery guide](https://learn.chatgpt.com/docs/build-skills)

## ChatGPT and ChatGPT Work

```sh
python3 scripts/skills.py package --output dist/chatgpt
```

This creates twenty ZIPs, one per skill, each with a single top-level skill directory.
On an eligible ChatGPT account, open **Plugins → Skills → Create → Upload
from your computer**. Upload the desired ZIP and check the scan result. Work
availability depends on the surface and workspace. If the environment can't
run Python or access your private records, run the CLI locally and provide
only the inputs or outputs approved for that workspace.

All eleven P1 ZIPs were uploaded privately and invoked on Chat and Work
with synthetic fixtures. For a new install, verify that the skill appears
under Installed and select it in a test chat using `@`. Account settings
and the workspace's upload scan apply to each installation. See the
[operational results](audit/P1R_QUALIFICATION.md).

[ChatGPT skills and admin controls](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)
· [ChatGPT Work](https://learn.chatgpt.com/docs/get-started-with-work)
· [OpenAI support guidance on skill ZIPs](https://community.openai.com/t/codex-created-a-skill-can-i-get-chatgpt-to-use-it/1408796/8)

## Manual installation for local execution

```sh
python3 scripts/skills.py install manual --destination /absolute/path/to/skills
```

Keep the whole skill directory and run its Python entry point from the venture
directory. The standalone installer supports Python execution outside an agent.

## Private workspaces and optional integrations

Keep a separate local directory per venture, outside this public checkout.
Select the private directory explicitly with `--workspace`. The SQLite
registry and exact backup commands are in the [workspace guide](WORKSPACE.md).
Legacy scripts still resolve `./seed` in the current directory and most
accept `--dir` for a different location.

Local drafting requires no connector. Export replies from an approved mailbox
into the documented JSON input and keep the file private. Review every exact
outbound payload. The founder sends mail and invitations manually and records
confirmed outcomes. If an approved legacy draft fails the new payload check,
use `closer.py log --id ID --event denied` to return it to review before handoff.

Live App Store scouting needs network access. Live EDGAR issuer research also
requires an identifying user agent via `--ua`, `SEC_USER_AGENT` or
`sec_user_agent` in private configuration. A filing is a lead about an issuer.
Confirm investor participation from independent public evidence. For unavailable
research endpoints, use existing sourced records or report the gap.

## Upgrade and verify

SEED preserves the legacy `seed/` JSON and CLI layout. Use the
[private workspace guide](WORKSPACE.md) to preview migration, validate a
private destination and restore backups. Regenerate older legacy outreach
batch IDs with `batch` before reviewing each exact payload.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/release.py build dist/review
python3 scripts/release.py verify dist/review
```

If a command reports a missing input, resolve the input path or run the
upstream workflow shown in the skill reference. For nonzero lint or check
results, review the diagnostics before distributing generated documents.
