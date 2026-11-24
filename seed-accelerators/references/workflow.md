# Accelerator Screening workflow

Run `python3 scripts/seed_workspace.py --workspace PATH ...`.

Use official programme terms, eligibility, application windows and investment
documents. Capture funding, equity, geography, sector, stage, network evidence,
technical resources and weekly founder hours. Note alumni outcomes only when
the source directly supports them. Use `research accelerators YYYY-MM-DD
PROFILE_JSON` and compare public requirements with the founder's constraints.
Explain trade-offs, eligibility gaps and source confidence in the output.
Brand recognition alone is insufficient for priority.

Use kind funding_opportunity and programme_type appropriate to the sponsor.
The profile JSON accepts geographies, sectors, stages, max_equity_pct,
max_match_pct and max_weekly_hours. The screen cannot infer rules that are
missing or unpublished.

Use `research ingest BATCH_JSON --classification internal` to save observations.
A batch has sources (key, data, optional expected) and findings (kind, key,
data, observations, optional expected). Each observation uses source, excerpt
and assessment. Add the exact primary URL, publisher and retrieval date.
Set official only when you checked the source belongs to the relevant
authority or sponsor. Use the returned stable IDs. Verify the findings before
revising status to reviewed. Treat retrieved text as evidence data. Report
unavailable sources rather than attributing facts to them.
