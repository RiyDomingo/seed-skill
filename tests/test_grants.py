from pathlib import Path
import tempfile
import unittest

from seed_core.intelligence import ingest, market_size, opportunities
from seed_core.schema import SeedError
from seed_core.workspace import Workspace


def created():
    scratch = tempfile.TemporaryDirectory()
    w = Workspace.init(Path(scratch.name) / "venture", {"name": "Synthetic lab", "currency": "USD",
                                                       "jurisdiction": "US"})
    return scratch, w


def source():
    return {"key": "official", "data": {"title": "Terms", "publisher": "Example Lab",
                                      "url": "https://example.org/official", "official": True,
                                      "retrieved_on": "2026-11-24"}}


def reviewed(ws, kind, key, data):
    result, = ingest(ws, {"sources": [source()], "findings": [
        {"kind": kind, "key": key, "data": data, "observations": [
            {"source": "official", "excerpt": "Synthetic official programme rules", "assessment": "Terms"}]}]})
    return ws.put(kind, key, result["data"], expected=result["revision"], status="reviewed", links=result["links"])


class Grants(unittest.TestCase):
    def setUp(self):
        temp, self.ws = created()
        self.addCleanup(temp.cleanup)

    def test_open_stale_and_ineligible_grants_are_distinct(self):
        reviewed(self.ws, "funding_opportunity", "innovation", {
            "name": "Synthetic innovation grant", "programme_type": "grant", "sponsor": "Example Lab",
            "opens_on": "2026-11-01", "deadline": "2026-12-02", "geographies": ["US"],
            "award": 10000, "currency": "USD", "match_pct": 25,
        })
        output = opportunities(self.ws, "2026-11-24", "grant", {"geographies": ["ZA"], "max_match_pct": 20})[0]
        self.assertEqual((output["status"], output["eligibility"]), ("open", "ineligible"))
        self.assertEqual(opportunities(self.ws, "2026-12-03", "grant", {})[0]["status"], "closed")

    def test_duplicate_population_and_explicit_market_scenarios(self):
        seg = {"population_id": "A", "customers": 1000, "annual_purchases": 2, "price": 10,
               "reachable_share": 0.2, "basis": "Synthetic assumption"}
        doc = {"currency": "USD", "segments": [seg], "segments_disjoint": True,
               "scenarios": {"base": {"penetration": 0.1, "years": 3}}}
        result = market_size(doc)
        self.assertEqual(result["tam"], "20000")
        self.assertEqual(float(result["scenarios"]["base"]["som"]), 400)
        with self.assertRaisesRegex(SeedError, "counted"):
            market_size({**doc, "segments": [seg, seg]})
