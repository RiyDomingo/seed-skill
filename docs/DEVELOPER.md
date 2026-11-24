# Developer guide

The twenty root `seed-*` directories are canonical. Put host-agnostic
commands in `seed_core` and expose them through `scripts/seed_workspace.py`.
An installed skill contains its own byte-for-byte copy of that runtime.
Its legacy entry point, where available, preserves the original standalone
command and `seed/` JSON contracts.

Use `scripts/skills.py` to install synthetic project skills. Update its
allowlist when a skill depends on a new file. Keep skill instructions in
`SKILL.md`, host metadata in `agents/openai.yaml` and detailed commands in
`references/workflow.md`. Add explicit input sources and output review
requirements to skill instructions. Never place venture records in skills.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/release.py build dist/review
python3 scripts/release.py verify dist/review
```

`tests/test_system.py` demonstrates all twenty extracted skills in seven
isolated synthetic workspaces. The integration suite covers fund qualification,
a disjoint market scenario, model and balance reconciliation, screened research,
an approval-bound draft, risk review and exported materials. The older packaged
workflow suite exercises the original eleven commands against their legacy
contracts.

The GitHub Actions matrix covers Python 3.12–3.14 on Linux, macOS and Windows.
Record the commit, test count, host receipts and package digests in the
[requirements matrix](REQUIREMENTS.md) and [development status](DEVELOPMENT_STATUS.md).
