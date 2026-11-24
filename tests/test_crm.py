from pathlib import Path
import tempfile
import unittest

from seed_core import fundraising as f
from seed_core.schema import SeedError
from seed_core.workspace import Workspace

ON = "2026-11-24"


class CRM(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.ws = Workspace.init(self.root / "venture",
                                 {"name": "Synthetic lab", "currency": "USD", "jurisdiction": "US"})
        investor = self.ws.put("investor", "fund", {"name": "Synthetic Fund", "mandate": "Materials"})
        self.investor_id = investor["id"]
        source = self.ws.put("source", "public mandate", {"title": "Thesis", "publisher": "Synthetic Fund",
                             "url": "https://example.org/thesis", "retrieved_on": ON})
        self.source = source
        ev = self.ws.put("evidence", "thesis", {"excerpt": "Materials at seed", "assessment": "Verified"},
                         links=[f.ref(source, "source")], status="reviewed")
        self.claim = self.ws.put("claim", "mandate", {"statement": "Invests in materials at seed"},
                                 links=[f.ref(ev, "evidence")], status="reviewed", provenance="verified_external")
        self.contact = self.ws.put("contact", "analyst@example.org", {"name": "Synthetic Analyst",
                                   "email": "analyst@example.org", "public_business": True,
                                   "investor_id": investor["id"]}, links=[f.ref(source, "source")], status="reviewed")
        self.message = {"sender": "founder@example.org", "body": "Your thesis covers materials. Reply to opt out.",
                        "subject": "Synthetic message", "verified_fact_ids": [self.claim["id"]]}

    def open_round(self, key):
        row = f.crm_open(self.ws, self.investor_id, key, "Synthetic round", self.contact["id"])
        return f.crm_advance(self.ws, row["id"], 1, "qualified", ON, "Reviewed",
                             follow_up=ON, next_action="Review introduction")

    def test_pipeline_and_duplicate_prevention(self):
        opportunity = self.open_round("seed")
        summary = f.pipeline(self.ws, ON)
        self.assertEqual(summary["counts"]["qualified"], 1)
        self.assertEqual(summary["due"][0]["id"], opportunity["id"])
        self.assertEqual(f.meeting_brief(self.ws, opportunity["id"], ON)["investor"]["id"], self.investor_id)
        msg = f.draft(self.ws, opportunity["id"], self.message, ON)
        with self.assertRaisesRegex(SeedError, "Duplicate"):
            f.draft(self.ws, opportunity["id"], self.message, ON)
        result = self.root / "prepared.eml"
        checksum = msg["data"]["payload_sha256"]
        with self.assertRaisesRegex(SeedError, "approval"):
            f.export_eml(self.ws, msg["id"], checksum, result, ON)
        with self.assertRaisesRegex(SeedError, "does not match"):
            f.approve(self.ws, msg["id"], "wrong", "Founder", ON)
        f.approve(self.ws, msg["id"], checksum, "Founder", ON)
        drafted = f.crm_advance(self.ws, opportunity["id"], 2, "outreach_drafted", ON, "Reviewed")
        f.crm_advance(self.ws, opportunity["id"], drafted["revision"], "outreach_approved", ON, "Approved")
        self.assertEqual(f.export_eml(self.ws, msg["id"], checksum, result, ON), result.resolve())
        self.assertIn(b"To: analyst@example.org", result.read_bytes())
        with self.assertRaisesRegex(SeedError, "founder-confirmed"):
            f.crm_advance(self.ws, opportunity["id"], 4, "contacted", ON, "No receipt")
        f.record_delivery(self.ws, msg["id"], checksum, ON, "Synthetic manual receipt")
        self.assertEqual(f.crm_advance(self.ws, opportunity["id"], 4, "contacted", ON, "Verified")
                         ["data"]["stage"], "contacted")
        self.ws.validate()

    def test_optout_is_permanent_across_rounds(self):
        first = self.open_round("seed")
        msg = f.draft(self.ws, first["id"], self.message, ON)
        checksum = msg["data"]["payload_sha256"]
        f.crm_advance(self.ws, first["id"], 2, "opted_out", ON, "No further contact")
        with self.assertRaisesRegex(SeedError, "suppressed"):
            f.approve(self.ws, msg["id"], checksum, "Founder", ON)
        later = self.open_round("later round")
        with self.assertRaisesRegex(SeedError, "suppressed"):
            f.draft(self.ws, later["id"], {**self.message, "subject": "New opportunity"}, ON)
        self.assertEqual(f.pipeline(self.ws, ON)["counts"]["opted_out"], 1)
        self.assertEqual(f.pipeline(self.ws, ON)["due"], [])

    def test_transitive_evidence_changes_block_approval(self):
        opportunity = self.open_round("seed")
        msg = f.draft(self.ws, opportunity["id"], self.message, ON)
        self.ws.put("source", self.source["key"], {**self.source["data"], "title": "Revised thesis"},
                    expected=1)
        with self.assertRaisesRegex(SeedError, "stale or disputed"):
            f.approve(self.ws, msg["id"], msg["data"]["payload_sha256"], "Founder", ON)

    def test_forged_or_delivered_handoffs_are_refused(self):
        opportunity = self.open_round("seed")
        draft = f.draft(self.ws, opportunity["id"], self.message, ON)
        checksum = draft["data"]["payload_sha256"]
        forged = self.ws.put("interaction", "outreach:synthetic-forged", {
            **draft["data"], "approval_on": ON, "approver": "Synthetic signer"},
            classification="restricted", provenance="founder", status="approved")
        with self.assertRaisesRegex(SeedError, "approval"):
            f.export_eml(self.ws, forged["id"], checksum, self.root / "forged.eml", ON)
        f.approve(self.ws, draft["id"], checksum, "Synthetic signer", ON)
        f.record_delivery(self.ws, draft["id"], checksum, ON, "Synthetic delivery receipt")
        with self.assertRaisesRegex(SeedError, "already recorded"):
            f.export_eml(self.ws, draft["id"], checksum, self.root / "duplicate.eml", ON)
