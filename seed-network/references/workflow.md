# Investor Network workflow

Run `python3 scripts/seed_workspace.py --workspace PATH ...` from the installed skill directory.

Create or review `relationship` records with `description`, `from_id`,
`to_id`, `relationship_status` and optional `bidirectional`. Pin both
endpoints with dependency links. Mark a relationship verified only
with reviewed evidence. Shared affiliation alone supports possible.

Run `fundraising paths FOUNDER_ID INVESTOR_ID --max-hops 3`. Output uses
stable IDs, pinned relationship revisions and verified or possible path
status. Ask the founder to validate the proposed intermediary. Keep the
result private. An introduction remains a draft until explicitly approved.

If relationships or verified permissions are missing, state that gap and
report any possible pathways with their basis. A graph edge cannot grant
permission to share either party's contact details.
