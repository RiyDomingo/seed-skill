# P1 verification

## Functional tests

**PASSED**. The following command ran 186 tests on macOS with Python
3.12.7, 3.13.1 and 3.14.7.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

The original functional tests and fixtures remain. Documentation assertions
check the portable entry points and the examples in their workflow references.
New regressions cover full payload preview, draft path containment, thread-bound
approval, linked diligence files, package membership, package integrity, install
locations and refusal to overwrite. Research and correspondence tests are offline.

| Skill | Passed tests | Representative result |
| --- | ---: | --- |
| Scout | 17 | Recorded Apple feeds produce de-duplicated review themes. |
| Market | 7 | TAM/SAM/SOM calculation checks sources and rejects inconsistent ordering. |
| Model | 18 | Monthly balances and unit economics match independently calculated fixture results. |
| Plan | 12 | Synthetic venture builds Markdown and flags mismatches and missing inputs. |
| Deck | 21 | Synthetic plan produces escaped printable HTML and lint results. |
| Investors | 16 | Public-source import, scoring and mock Form D parsing work offline. |
| Closer | 30 | EML to local approval, reply and ICS flow passes. Draft changes and links are refused. |
| Coach | 14 | Investor-specific drill, answer grade and timed agenda use workspace fixtures. |
| Terms | 18 | SAFE and priced-round cases reconcile, including invalid-input refusal. |
| Dataroom | 10 | Fixture checks and candidate lists exclude linked documents. |
| Updates | 11 | Synthetic November update preserves metrics, lowlights and computed runway. |

Shared tests add nine repository checks and three installation and packaging checks.
Each skill's workflow reference includes inputs, commands, output and example.
All packaged Python scripts also return help when executed independently.

## Platform checks

| Check | Status | Observed result |
| --- | --- | --- |
| Agent Skills format | PASSED | OpenAI Skill Creator `quick_validate.py` passed all 11 canonical directories. |
| Project and user installer destinations | PASSED | Temporary Codex project copies succeeded. Mocked-home tests verified user installation. |
| ZIPs | PASSED | All eleven archives have the required single skill directory. Contents match installed files, include the MIT notice and exclude non-allowlisted data. |
| Codex live project discovery | BLOCKED | Codex CLI 0.159.3 initially could not initialize its state database under the restricted home directory. With a temporary SQLite directory, the app-server did not answer the initialization request. |
| Installed synthetic quick start | PASSED | The installed model produced the 36-month JSON and its CSV from bundled assumptions. |
| ChatGPT and ChatGPT Work hosted import | NOT RUN | Official upload steps researched. Account-level upload, scanning and execution were not exercised. |
| Live Apple, SEC and outreach | NOT RUN | Local and mocked fixtures only. No messages or calendar invitations were sent. |
| Linux and Windows | NOT RUN | Local verification ran on macOS. |
