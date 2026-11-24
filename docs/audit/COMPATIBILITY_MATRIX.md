# Compatibility matrix

Official documentation reviewed 2026-11-24.

| Surface | Canonical installation or format | Baseline |
| --- | --- | --- |
| Agent Skills | A folder matching the skill name with YAML `name` and `description` in SKILL.md. Supporting scripts and referenced files travel with it. | Claude-specific field and path references need migration. |
| Codex | Project `.agents/skills` and user `~/.agents/skills`. Optional UI metadata in `agents/openai.yaml`. | No installation command or package validation. |
| ChatGPT | Eligible workspaces can use Plugins → Skills → Create → Upload from your computer. Admin settings and scanning apply. | No upload package. |
| ChatGPT Work | Current OpenAI guidance covers skills in Work, including skills distributed by plugins. Workspace permissions and execution environment control availability. | No Work validation or shared private-files contract. |
| Claude Code | Standalone project `.claude/skills` and user `~/.claude/skills`. | Legacy marketplace and plugin manifests point at root skill directories. |
| MCP and apps | MCP defines client/server capabilities. OpenAI apps and plugins expose product-specific tools subject to account permissions. | Gmail and Calendar tool names are embedded in the legacy instructions. |

Sources

- [Agent Skills specification](https://agentskills.io/specification)
- [OpenAI skill authoring and Codex discovery](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI skills repository](https://github.com/openai/skills)
- [OpenAI AGENTS.md guide](https://developers.openai.com/codex/guides/agents-md/)
- [Skills in ChatGPT](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)
- [ChatGPT Work](https://learn.chatgpt.com/docs/get-started-with-work)
- [OpenAI plugin capabilities](https://help.openai.com/en/articles/20001256-plugins-in-chatgpt)
- [OpenAI connected apps](https://help.openai.com/en/articles/11487775-connected-apps-in-chatgpt)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [MCP specification](https://modelcontextprotocol.io/specification/latest)

See [P1 verification](P1_TEST_RESULTS.md) for observed installation, discovery
and runtime results.
