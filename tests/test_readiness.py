from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from seed_core import diligence
from seed_core.fundraising import ref
from seed_core.workspace import Workspace

ON = "2026-11-24"


class ReadinessFixture(unittest.TestCase):
    def setUp(self):
        scratch = TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.ws = Workspace.init(Path(scratch.name) / "venture", {
            "name": "Synthetic test lab", "currency": "USD", "jurisdiction": "US"})
        self.source = self.ws.put("source", "public study", {"title": "Synthetic study",
            "publisher": "Example Lab", "url": "https://example.org/study", "retrieved_on": ON},
            classification="public", provenance="verified_external", status="reviewed")

    def supported(self, key, stage):
        return self.ws.put("evidence", key, {"excerpt": "Synthetic validation",
            "assessment": "Reviewed", "validation_type": stage}, links=[ref(self.source, "source")],
            classification="public", status="reviewed", provenance="verified_external")


class Readiness(ReadinessFixture):
    def test_computational_and_experimental_validation_are_distinct(self):
        evidence = self.supported("simulation", "computational_verification")
        self.ws.put("evidence", "proposed experiment", {"excerpt": "Unreviewed",
            "assessment": "Draft", "validation_type": "experimental_validation"},
            links=[ref(self.source, "source")])
        doc = {"dimensions": {"technology": {"level": 4, "evidence": [evidence["id"]]}}}
        report = diligence.readiness(self.ws, doc, ON)
        self.assertFalse(report["investment_ready"])
        self.assertEqual(report["dimensions"]["technology"]["supported"], 3)
        self.assertEqual(report["dimensions"]["technology"]["stage"], "computational_verification")
        self.ws.put("source", "public study", {**self.source["data"], "title": "Synthetic revision"},
                    expected=1, classification="public", provenance="verified_external", status="reviewed")
        self.assertEqual(diligence.readiness(self.ws, doc, ON)["dimensions"]["technology"]["supported"], 0)

    def test_review_candidates_exclude_private_document_metadata(self):
        public = self.ws.put("document", "term overview", {"name": "Synthetic term overview",
            "document_type": "term summary", "disclosure": "initial"}, status="approved")
        self.ws.put("document", "private diligence", {"name": "Synthetic restricted document",
            "document_type": "review", "disclosure": "restricted"}, status="approved",
            classification="restricted")
        output = diligence.dataroom(self.ws, "initial", ON)
        self.assertEqual([x["record"]["id"] for x in output["candidates"]], [public["id"]])
        self.assertTrue(output["candidates"][0]["review_candidate"])
        self.assertFalse(output["automatic_disclosure"])
