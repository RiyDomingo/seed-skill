# Capital strategy workflow

Run `python3 scripts/seed_workspace.py --workspace PATH finance capital INPUT.json`.
Use the forecast contract documented in the financial model skill. Compare a
case's funded and unfunded runway, earliest shortfall and minimum cash reserve.
A financing instrument can be held until the required milestone. A null
milestone month leaves scheduled financing unreceived. Use scenario delays to
stress timing. Treat grants as financing in this model and disclose any
repayment, matching, eligibility or spend restrictions separately.

Run `finance round`, `finance waterfall` or `finance ownership` for the
supplied term scenarios. Use explicit agreement clauses and counsel for
interpretation. Record schedule, currency, input sources, constraints and
cases in the workspace. The calculations illustrate supplied scenarios and
cannot establish eligibility, investment commitment or legal rights.

Use a financing id and that financing_id on related principal or interest
events. Downside financing delays shift linked service by the same interval.
An unfunded comparison retains obligations on opening debt and omits only
events explicitly linked to the removed financing.
