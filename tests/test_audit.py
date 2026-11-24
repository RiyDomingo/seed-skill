from seed_core import diligence
from seed_core.fundraising import ref
from seed_core.schema import SeedError

from test_readiness import ON, ReadinessFixture


class Audit(ReadinessFixture):
    def setUp(self):
        super().setUp()
        self.assumption = self.ws.put("assumption", "price", {"label": "Expected price",
            "value": 10, "unit": "USD", "rationale": "Synthetic assumption"},
            classification="public", status="reviewed", provenance="assumption")
        self.assertion = {"key": "expected price", "value": 10, "unit": "USD",
            "path": ["value"], "numeric": True, "source_id": self.assumption["id"], "revision": 1}

    def test_conflicts_and_insufficient_disclosure_are_critical(self):
        for name, value in (("plan", 10), ("deck", 50)):
            self.ws.put("document", name, {"name": name, "document_type": name, "audience": "public",
                "assertions": [{**self.assertion, "value": value}]},
                links=[ref(self.assumption, "assumption")], status="reviewed")
        findings = diligence.audit(self.ws, ON)["findings"]
        rules = {f["rule"]: f["severity"] for f in findings}
        self.assertEqual(rules, {"cross_document_conflict": "CRITICAL",
                                  "contradicts_input": "CRITICAL", "disclosure": "CRITICAL"})

    def test_materials_check_numbers_units_and_escape_html(self):
        section = {"heading": "Price", "text": "Expected price is $10. <script>unsafe</script>",
                   "records": [self.assumption["id"]], "assertions": [self.assertion]}
        doc = {"title": "Synthetic terms", "type": "plan", "audience": "public", "sections": [section]}
        text, links = diligence.material(self.ws, doc, ON, "html")
        self.assertNotIn("<script>", text)
        self.assertIn("&lt;script&gt;", text)
        self.assertEqual(links, [ref(self.assumption)])
        for bad in ("Different value $15.", "Different unit 10%."):
            with self.subTest(bad=bad), self.assertRaisesRegex(SeedError, "missing a traced assertion"):
                diligence.material(self.ws, {**doc, "sections": [{**section, "text": bad}]}, ON, "md")
        with self.assertRaisesRegex(SeedError, "missing a traced assertion"):
            diligence.material(self.ws, {**doc, "type": "update", "risks": ["A delay of 30 days"]}, ON, "md")

    def test_material_rejects_nda_dependency_in_initial_disclosure(self):
        private = self.ws.put("document", "nda", {"name": "Synthetic report",
            "document_type": "lab study", "disclosure": "nda"}, status="approved")
        overview = self.ws.put("document", "overview", {"name": "Synthetic overview",
            "document_type": "summary", "disclosure": "initial"}, status="approved", links=[ref(private)])
        with self.assertRaisesRegex(SeedError, "disclosure tier"):
            diligence.material(self.ws, {"title": "Synthetic narrative", "type": "plan", "audience": "initial",
                "sections": [{"heading": "Overview", "text": "Reference description",
                              "records": [overview["id"]]}]}, ON, "md")
        self.assertEqual(diligence.dataroom(self.ws, "initial", ON)["candidates"], [])

    def test_data_room_candidates_require_passing_review(self):
        self.ws.put("document", "plan", {"name": "Synthetic plan", "document_type": "plan",
            "audience": "public", "disclosure": "public", "assertions": [{**self.assertion, "value": 100}]},
            classification="public", links=[ref(self.assumption, "assumption")], status="approved")
        candidate, = diligence.dataroom(self.ws, "public", ON)["candidates"]
        self.assertFalse(candidate["review_candidate"])
        self.assertEqual(candidate["findings"][0]["severity"], "CRITICAL")
        model = self.ws.put("financial_model", "malformed", {"name": "Synthetic model",
            "currency": "USD", "forecast": {"scenarios": []}}, status="reviewed")
        issue, = diligence.audit(self.ws, ON, [model["id"]])["findings"]
        self.assertEqual(issue["rule"], "financial_reconciliation")
