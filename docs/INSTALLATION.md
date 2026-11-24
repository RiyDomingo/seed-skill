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
python3 scripts/skills.py package --output dist
```

This creates one ZIP per skill, each with a single top-level skill directory.
On an eligible ChatGPT account, open **Plugins → Skills → Create → Upload
from your computer**. Upload the desired ZIP and check the scan result. Work
availability depends on the surface and workspace. If the environment can't
run Python or access your private records, run the CLI locally and provide
only the inputs or outputs approved for that workspace.

The archive layout was tested locally. Hosted upload, scanning, discovery and
script execution were not run. Confirm the UI accepts the package before
relying on it. No hosted installation or sharing is required for local use.

[ChatGPT skills and admin controls](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)
· [ChatGPT Work](https://learn.chatgpt.com/docs/get-started-with-work)
· [OpenAI support guidance on skill ZIPs](https://community.openai.com/t/codex-created-a-skill-can-i-get-chatgpt-to-use-it/1408796/8)

## Claude Code and other Agent Skills clients

```sh
python3 scripts/skills.py install claude --project /absolute/path/to/private-venture
python3 scripts/skills.py install claude --user
python3 scripts/skills.py install manual --destination /absolute/path/to/skills
```

Claude project and user installations use `.claude/skills` and
`~/.claude/skills`. Start Claude Code in the venture directory and select
`/seed-market` or another installed skill. The original marketplace manifests
are retained. The standalone installation path is the P1 installation route.

For another Agent Skills host, copy or install the whole skill folder into
its discovery location. Preserve its directory name and supporting files.
For standalone execution, call the packaged Python script by its absolute
path from the venture directory. See each skill's workflow reference for
commands, inputs, outputs and examples.

[Claude Code skill discovery](https://code.claude.com/docs/en/skills) ·
[Agent Skills specification](https://agentskills.io/specification)

## Private workspaces and optional integrations

Keep a separate local directory per venture, outside this public checkout.
Start there so the legacy scripts resolve `./seed` correctly. Most commands
also accept `--dir` to select the private seed directory.
Use each command's help to check flags. Back up the entire private directory
before upgrading or batch changes. To restore, copy the backup to a new
private directory and validate outputs before resuming. Use one writer per
venture in P1.

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

P1 keeps the legacy `seed/` JSON files and CLI layout. Copy private data to an
independent working directory before first use with P1. Older batch IDs need
to be regenerated with `batch`. No data migration is required in P1.
The versioned evidence registry and migration tools are planned for P2.

```sh
python3 -m unittest discover -s tests -v
```

If a command reports a missing input, resolve the input path or run the
upstream workflow shown in the skill reference. For nonzero lint or check
results, review the diagnostics before distributing generated documents.
