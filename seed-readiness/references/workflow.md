# Venture Readiness workflow

Run `python3 scripts/seed_workspace.py --workspace PATH ...`.

Run `readiness assess ASSESSMENT_JSON YYYY-MM-DD`. The dimensions object
uses technology, manufacturing, commercial, regulatory, intellectual_property,
team, financial and investment. Each value gives level from 0 to 5 and
evidence IDs. Set minimum_levels for all eight if the default level 3
does not match this venture. Evidence needs a reviewed validation_type
for the relevant rubric stage. Obtain the rubric from the bundled code
or project guide. Record computational and experimental work separately.
Evidence gaps or blocking findings prevent a ready result. Use
`readiness plan-workflow REQUEST` to retrieve missing prerequisites.
