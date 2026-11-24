# Workflows and connectors

## Start a venture

Create an isolated directory with the [installation guide](INSTALLATION.md).
Use an installed skill in a fresh ChatGPT, Work or Codex session. Select
the same private workspace for each local command. Set the reporting
currency and jurisdiction at initialization.

Start with sourced observations for markets, competitors, investors and
funding. Enter explicit assumptions for calculations. Review the inputs
and their provenance before composing investment materials. Run the audit
after a new input revision. Files refer to the revisions they used.

| Workflow | Example request | Review before using the result |
| --- | --- | --- |
| Market and financing | Estimate the serviceable market and build a 60-month hardware forecast. | Segment overlap, evidence dates, price basis, runway, financing conditions |
| Fundraising | Find potential lead investors and show who needs follow-up this week. | Thesis sources, confidence, recent activity, relationship evidence, suppression |
| Non-dilutive funding | Screen current grants for my jurisdiction and budget. | Official deadline, eligible expenses, match, award timing |
| Diligence | Audit the pitch against the engineering and financial records. | Experimental versus computational evidence, unsupported narrative, disclosure stage |
| Investment committee | Assess the strongest investment case and what could change the decision. | Five perspective findings, dissent and missing evidence |

The [developer guide](DEVELOPER.md) covers the seven synthetic scenarios.
Run `python3 scripts/qualification.py /tmp/seed-qualification.zip` from
the software checkout to create a public synthetic input ZIP and command
manifest for exactly twenty workflows.

## Connectors and hosted files

Use account-approved research tools to locate primary sources. Use a
configured connector to read records only for the requested venture.
Copy the source title, publisher, URL or safe document reference,
retrieval date, excerpt and limitations into the evidence registry.
A connector is optional for local calculations and drafting.

For a hosted run, use the [workspace exchange commands](WORKSPACE.md)
to export a digest-approved selection. In ChatGPT Work, leave an
approved synthetic or venture-specific exchange file in its intended
workflow only when you have permission to retain the contents there.
Download any new bundle and import it explicitly on the receiving
side. Keep the protected SQLite backup on the local side.

For email and calendar, preview the exact recipients, subject, content,
attachments, time and time zone. Record the founder's approval before
requesting a specific connector write. Use the local EML or ICS export
and manual delivery when there is no approved write capability.
Use the installed Investor Outreach skill's `scripts/seed_calendar.py`
to preview an invitation for a CRM opportunity and record the exact
approval before local ICS export. Use confirmed delivery or scheduling
outcomes to update the CRM.
See [security and privacy](SECURITY.md).

## Troubleshooting

- If an installed skill is missing, verify it is visible in the host's
  discovery location and start a fresh session.
- If the host cannot run the bundled Python script, run the selected
  command locally and exchange the approved JSON inputs or outputs.
- If an import refuses a bundle, check the digest, venture ID,
  dependency closure and whether both environments revised the same
  record. Review conflicts independently before preparing a new transfer.
- If a readiness claim is unsupported, locate the pinned evidence and
  validate its date, study type and disclosure stage before revising
  the claim.
