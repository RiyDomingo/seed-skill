from seed_core import diligence

from test_readiness import ON, ReadinessFixture


class Committee(ReadinessFixture):
    def test_conditional_decision_requires_evidence_across_five_perspectives(self):
        proof = self.supported("prototype", "prototype")
        doc = {"perspectives": {
            role: {"recommendation": "INVEST SUBJECT TO CONDITIONS", "evidence": [proof["id"]],
                   "case": "Synthetic case", "counterargument": "Unverified demand",
                   "risks": "Adoption risk", "evidence_to_change": "Independent usage results"}
            for role in diligence.PERSPECTIVES},
            "strongest_case": "Prototype evidence",
            "strongest_counterargument": "Demand is unverified",
            "decision_changing_evidence": "Independent usage evidence"}
        self.assertEqual(diligence.committee(self.ws, doc, ON)["decision"], "INVEST SUBJECT TO CONDITIONS")
        doc["perspectives"]["vc_partner"]["evidence"] = []
        self.assertEqual(diligence.committee(self.ws, doc, ON)["decision"], "INSUFFICIENT EVIDENCE")
