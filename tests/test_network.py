from pathlib import Path
import tempfile
import unittest

from seed_core.fundraising import qualification, ref, relationship_paths
from seed_core.workspace import Workspace


class Network(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.ws = Workspace.init(Path(temporary.name) / "venture",
                                 {"name": "Synthetic lab", "currency": "USD", "jurisdiction": "US"})

    def test_possible_affiliation_and_proved_relationship_are_distinct(self):
        founder = self.ws.put("contact", "founder", {"name": "Founder"})
        other = self.ws.put("contact", "alumnus", {"name": "Intermediary"})
        investor = self.ws.put("investor", "firm", {"name": "Synthetic firm"})
        source = self.ws.put("source", "statement", {"title": "Public confirmation", "publisher": "Example",
                             "url": "https://example.org/statement", "retrieved_on": "2026-10-10"})
        for edge, left, right, state, proof in [
            ("affiliation", founder, investor, "possible", []),
            ("known", founder, other, "verified", [ref(source, "source")]),
            ("contact", other, investor, "verified", [ref(source, "source")]),
        ]:
            self.ws.put("relationship", edge, {"description": "Synthetic relationship", "from_id": left["id"],
                        "to_id": right["id"], "relationship_status": state},
                        links=[ref(left), ref(right), *proof], status="reviewed")
        paths = relationship_paths(self.ws, founder["id"], investor["id"])
        self.assertEqual([r["status"] for r in paths], ["verified", "possible"])
        self.assertEqual(paths[0]["nodes"][1], other["id"])

    def test_fit_does_not_conflate_missing_evidence_with_confidence(self):
        investor = self.ws.put("investor", "firm", {"name": "Synthetic firm"})
        result = qualification(self.ws, investor["id"],
                               {"criteria": {"sector": {"rating": 1, "confidence": 1}}}, "2026-11-24")
        self.assertEqual((result["fit_score"], result["coverage"], result["evidence_confidence"]), (100, 25, 0))
        self.assertFalse(result["priority_eligible"])
        self.assertIsNone(result["breakdown"]["cheque"]["rating"])
