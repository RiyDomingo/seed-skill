# Platform qualification

Supported hosts are ChatGPT, ChatGPT Work and OpenAI Codex.

For each skill, verify native installation and discovery, then invoke the
actual skill in the host using synthetic inputs. Confirm that the host reads
bundled references, executes the intended Python script, returns a fresh
result and matches its deterministic output contract. Keep execution
receipts, archive checks and version or script digests.

Codex can use a private local workspace. For hosted Chat and Work, install
one ZIP per skill and exchange only an approved bounded JSON payload with the
local workspace. The exchange gate verifies the same venture ID, pinned
revisions, divergence refusal and return of valid artifacts.

P1R evidence for the original eleven is in the
[qualification report](../audit/P1R_QUALIFICATION.md). P7 repeats the live
qualification for all twenty and checks cross-skill workflows. Hosted
availability depends on eligible account and workspace permissions.
