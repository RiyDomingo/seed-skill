# Investment Committee workflow

Run `python3 scripts/seed_workspace.py --workspace PATH ...`.

Prepare five perspective reports before synthesis. Use independent
reviewers where the host supports delegated work and the user authorizes it.
Otherwise conduct structured perspective analysis and label it as such.
Pass perspectives keyed vc_partner, technical_diligence, financial_analysis,
commercialisation and risk_governance. Each has recommendation, case,
counterargument, risks, evidence_to_change and evidence IDs. Include
strongest_case, strongest_counterargument and decision_changing_evidence
at the top level. Legitimate outcomes are INVEST, INVEST SUBJECT TO
CONDITIONS, MONITOR, DECLINE and INSUFFICIENT EVIDENCE.

Run `readiness committee INPUT_JSON YYYY-MM-DD`. It checks review status
and conflicting evidence. Returned mode describes the structured
aggregation. Include separate execution receipts if independent reviewers
actually ran. A simulated decision is neither a commitment nor permission
to disclose information.
