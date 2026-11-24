import unittest

from seed_core.intelligence import opportunities
from test_grants import created, reviewed


class Accelerators(unittest.TestCase):
    def test_programme_equity_and_hours_screen(self):
        temp, ws = created()
        self.addCleanup(temp.cleanup)
        reviewed(ws, "funding_opportunity", "accelerator", {
            "name": "Synthetic Accelerator", "programme_type": "accelerator", "sponsor": "Example Lab",
            "opens_on": "2026-12-01", "deadline": "2027-01-02", "equity_pct": 7, "weekly_hours": 25,
        })
        rows = opportunities(ws, "2026-11-24", "accelerator", {"max_equity_pct": 5, "max_weekly_hours": 20})
        self.assertEqual(rows[0]["status"], "upcoming")
        self.assertEqual(rows[0]["eligibility"], "ineligible")
        self.assertFalse(rows[0]["screen"]["equity_pct"])
        self.assertEqual(opportunities(ws, "2026-11-24", "grant", {}), [])
