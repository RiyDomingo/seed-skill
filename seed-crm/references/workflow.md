# Fundraising CRM workflow

Run `python3 scripts/seed_workspace.py --workspace PATH ...` from the installed skill directory.

Use `fundraising open INVESTOR_ID ROUND_KEY NAME --contact CONTACT_ID`
to create a stable opportunity. `fundraising advance ID STAGE DATE NOTE
--expected REVISION` updates one stage and logs the transition atomically.
Add `--next-action` and `--follow-up YYYY-MM-DD` for a dated action. Use
`fundraising pipeline YYYY-MM-DD` for counts and due opportunities.
`fundraising suppress EMAIL DATE opted_out` or `bounce` blocks later
outreach even through a different opportunity using that address.

Read the current opportunity before updating and treat revision conflicts
as edits to reconcile. Keep outputs private. Record external activity only
when the founder confirms it took place. Never infer a delivery, meeting or
commitment from an earlier draft.

After the founder confirms external delivery, use `fundraising record-delivery
DRAFT_ID SHA256 DATE RECEIPT` before moving to contacted. Record the
confirmed outbound action only. An approval or EML export cannot substitute
for that receipt.
