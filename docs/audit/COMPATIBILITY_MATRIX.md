# Platform compatibility

Supported platforms are ChatGPT, ChatGPT Work and OpenAI Codex. The open
Agent Skills specification governs the portable skill folders.

| Surface | Installation | SEED 2.0 operational evidence |
| --- | --- | --- |
| Codex | Repository or user `.agents/skills`. Packages include optional `agents/openai.yaml`. | All 20 installed, discovered and executed in the project harness. |
| ChatGPT | Plugins → Skills → Add skill → Upload from your computer. | All 20 uploaded privately, selected and invoked with bundled Python scripts. |
| ChatGPT Work | Select the installed skills in the Work composer where the workspace permits it. | All 20 selected and invoked with bundled Python scripts. |
| Agent Skills | Folder matches the skill name and includes the YAML metadata, scripts and references. | All 20 validated and exercised as extracted archives. |
| Claude Code | OUT_OF_SCOPE | No acceptance checks apply. |

OpenAI workspace permissions govern installed skills and connectors. Venture
records are exchanged explicitly. A local project and hosted skill environment
may have different filesystem lifetimes and visibility.

- [Current qualification](P7_QUALIFICATION.md)
- [P1R qualification](P1R_QUALIFICATION.md)
- [Agent Skills specification](https://agentskills.io/specification)
- [OpenAI skill authoring and Codex discovery](https://learn.chatgpt.com/docs/build-skills)
- [Skills in ChatGPT](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)
- [ChatGPT Work](https://learn.chatgpt.com/docs/get-started-with-work)
- [OpenAI apps and permissions](https://help.openai.com/en/articles/11487775-connected-apps-in-chatgpt)
- [MCP specification](https://modelcontextprotocol.io/specification/latest)
