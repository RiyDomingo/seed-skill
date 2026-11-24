import unittest

from seed_core.intelligence import compare_competitors, patent_landscape
from test_grants import created, reviewed


class Patents(unittest.TestCase):
    def test_family_matching_and_status_freshness(self):
        temp, ws = created()
        self.addCleanup(temp.cleanup)
        for country in ("US", "EP"):
            reviewed(ws, "document", country, {"name": "Synthetic metrology scanner", "document_type": "patent",
                     "publication_number": country + " 999000 A1", "jurisdiction": country,
                     "family": "synthetic-1", "assignee": "Example Lab", "legal_status": "published_application",
                     "status_checked_on": "2026-11-01"})
        result = patent_landscape(ws, "2026-11-24", "metrology scanner")
        self.assertEqual(len(result["families"]["synthetic-1"]), 2)
        self.assertEqual({x["current_status"] for x in result["families"]["synthetic-1"]}, {"published_application"})
        stale = patent_landscape(ws, "2027-11-24")
        self.assertEqual({x["current_status"] for x in stale["families"]["synthetic-1"]}, {"unknown"})

    def test_vendor_performance_stays_attributed_even_after_review(self):
        temp, ws = created()
        self.addCleanup(temp.cleanup)
        reviewed(ws, "competitor", "incumbent", {"name": "Synthetic Incumbent", "category": "incumbent",
                 "features": {"accuracy": {"value": "0.2 mm", "basis": "vendor_claim"}}})
        result = compare_competitors(ws, "2026-11-24")
        self.assertFalse(result["profiles"][0]["features"]["accuracy"]["performance_verified"])
