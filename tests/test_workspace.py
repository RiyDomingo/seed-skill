import copy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from _load import FIX, symlink
from seed_core import legacy, recovery, transfer
from seed_core.schema import SeedError, digest, parse_json
from seed_core.workspace import Conflict, Workspace

PROFILE = {"name": "Synthetic materials venture", "currency": "USD", "jurisdiction": "US"}


def link(record, role):
    return {"id": record["id"], "revision": record["revision"], "role": role}


class KnowledgeBase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ws = Workspace.init(self.root / "venture", PROFILE)

    def test_isolation_and_normalized_identity(self):
        source = self.ws.put("competitor", "  Æther Systems ", {"name": "Æther"})
        self.assertEqual(source, self.ws.put("competitor", "æther systems", {"name": "Æther"}))
        other = Workspace.init(self.root / "parallel", PROFILE)
        self.assertNotEqual(source["id"], other.put("competitor", "æther systems", {"name": "Æther"})["id"])
        self.assertIsNone(other.get(source["id"]))
        checkout = self.root / "public"
        (checkout / ".git").mkdir(parents=True)
        with self.assertRaisesRegex(SeedError, "outside Git"):
            Workspace.init(checkout / "venture", PROFILE)

    def test_revision_history_and_concurrency(self):
        v1 = self.ws.put("decision", "priority", {"summary": "First"})

        def update(text):
            try:
                return self.ws.put("decision", "priority", {"summary": text}, expected=1)["revision"]
            except Conflict:
                return "conflict"

        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(update, ["Second", "Third"]))
        self.assertCountEqual(results, [2, "conflict"])
        self.assertEqual(self.ws.get(v1["id"], 1), v1)
        self.assertEqual(self.ws.validate()["revisions"], 3)

    def test_verified_evidence_conflicts_and_stale_transitive_outputs(self):
        source = self.ws.put("source", "paper", {"title": "Synthetic study", "publisher": "Example Lab",
                             "url": "https://example.org/synthetic", "retrieved_on": "2026-10-01",
                             "max_age_days": 7})
        ev1 = self.ws.put("evidence", "observed", {"excerpt": "Observed 3 units in the pilot",
                          "assessment": "Small sample"}, status="reviewed", links=[link(source, "source")])
        ev2 = self.ws.put("evidence", "competing", {"excerpt": "Observed 2 units with a changed method",
                          "assessment": "Method difference"}, links=[link(source, "source")])
        claim = self.ws.put("claim", "pilot", {"statement": "Pilot observed 3 units"},
                            status="reviewed", provenance="verified_external",
                            links=[link(ev1, "evidence"), link(ev2, "contradicts")])
        a1 = self.ws.put("assumption", "price", {"label": "Price", "value": 10, "unit": "USD",
                         "rationale": "Pilot estimate"}, provenance="assumption")
        calc = self.ws.put("calculation", "revenue", {"label": "Revenue", "value": 100, "unit": "USD",
                           "method": "price times ten"}, provenance="calculated", links=[link(a1, "assumption")])
        deck = self.ws.put("document", "deck", {"name": "Synthetic pitch", "document_type": "pitch deck"},
                           status="approved", links=[link(claim, "dependency"), link(calc, "calculation")])
        self.ws.put("assumption", "price", {**a1["data"], "value": 11}, expected=1, provenance="assumption")
        self.assertEqual({x["id"] for x in self.ws.affected(a1["id"])}, {deck["id"], calc["id"]})
        self.assertEqual(self.ws.get(deck["id"]), deck)
        self.assertEqual({f["type"] for f in self.ws.trace(deck["id"], "2026-11-01")["findings"]},
                         {"conflicting_evidence", "stale_source", "stale_dependency"})

    def test_schema_and_files_fail_closed(self):
        values = [
            ("evidence", {"excerpt": "x", "assessment": "review"}, {}),
            ("claim", {"statement": "x"}, {"provenance": "verified_external", "status": "reviewed"}),
            ("document", {"name": "x", "document_type": "note", "document_ref": "notes/../secret"}, {}),
            ("decision", {"summary": "x", "password": "synthetic"}, {}),
            ("decision", {"summary": "x", "confidence": 1.1}, {}),
        ]
        for kind, data, options in values:
            with self.subTest(kind=kind, data=data), self.assertRaises(SeedError):
                self.ws.put(kind, "bad", data, **options)
        marker = "-----BEGIN " + "PRIVATE KEY-----"
        with self.assertRaisesRegex(SeedError, "Credential"):
            self.ws.put("decision", marker, {"summary": "Unsafe key"}, classification="public")
        with self.assertRaisesRegex(SeedError, "Credential"):
            Workspace.init(self.root / "unsafe", {**PROFILE, "name": marker})
        with self.assertRaisesRegex(SeedError, "Duplicate"):
            parse_json(b'{"confidentiality":1,"confidentiality":2}')
        with self.assertRaises(SeedError):
            parse_json(b'[NaN]')
        target = self.root / "linked"
        symlink(self, self.ws.root, target, directory=True)
        with self.assertRaisesRegex(SeedError, "Linked"):
            Workspace(target)

    def test_explicit_exchange_and_conflict_rejection(self):
        source = self.ws.put("source", "report", {"title": "Public report", "publisher": "Example Lab",
                             "url": "https://example.org/report", "retrieved_on": "2026-10-01"},
                             classification="public")
        evidence = self.ws.put("evidence", "excerpt", {"excerpt": "Measured 3 units", "assessment": "Pilot"},
                               classification="public", links=[link(source, "source")])
        self.ws.put("decision", "secret", {"summary": "Private financing preference"},
                    classification="restricted")
        with self.assertRaisesRegex(SeedError, "less confidential"):
            self.ws.put("source", "bad", source["data"], classification="public",
                        links=[link(self.ws.list("decision")[0], "dependency")])
        packet = transfer.snapshot(self.ws, ids=[evidence["id"]])
        self.assertEqual(len(packet["payload"]["records"]), 2)
        self.assertNotIn("Private financing", str(packet))
        self.assertNotIn(PROFILE["name"], str(packet))
        path = self.root / "exchange.json"
        with self.assertRaisesRegex(SeedError, "approval"):
            transfer.export(self.ws, path, "stale approval", ids=[evidence["id"]])
        transfer.export(self.ws, path, packet["sha256"], ids=[evidence["id"]])
        receiver = self.root / "receiver"
        self.assertEqual(transfer.import_bundle(receiver, transfer.read_file(path), packet["sha256"],
                                                create=True, config=PROFILE)["imported_revisions"], 2)
        peer = Workspace(receiver)
        self.assertEqual(peer.get(evidence["id"]), evidence)
        self.assertEqual(transfer.import_bundle(receiver, packet, packet["sha256"])["already_present"], 2)
        peer.put("source", "report", {**source["data"], "title": "Peer edit"}, expected=1,
                 classification="public")
        self.ws.put("source", "report", {**source["data"], "title": "Local edit"}, expected=1,
                    classification="public")
        newer = transfer.snapshot(self.ws)
        with self.assertRaises(Conflict):
            transfer.import_bundle(receiver, newer, newer["sha256"])
        self.assertEqual(peer.get(source["id"])["data"]["title"], "Peer edit")
        bad_checksum = copy.deepcopy(packet)
        bad_checksum["payload"]["maximum"] = "confidential"
        with self.assertRaisesRegex(SeedError, "checksum"):
            transfer.validate_bundle(bad_checksum)

    def test_workspace_transfer_rejects_missing_revisions_and_other_venture(self):
        record = self.ws.put("decision", "public", {"summary": "Public test decision"},
                             classification="public")
        another = Workspace.init(self.root / "second", PROFILE)
        packet = transfer.snapshot(self.ws)
        with self.assertRaises(Conflict):
            transfer.import_bundle(another.root, packet, packet["sha256"])
        packet["payload"]["records"][0]["revision"] = 2
        revision = packet["payload"]["records"][0]
        revision["digest"] = digest({k: v for k, v in revision.items() if k != "digest"})
        packet["sha256"] = digest(packet["payload"])
        with self.assertRaisesRegex(SeedError, "Non-contiguous"):
            transfer.validate_bundle(packet)
        self.assertEqual(self.ws.get(record["id"]), record)

    def test_legacy_dry_run_quarantine_idempotency_materialize_and_restore(self):
        original = self.root / "legacy"
        shutil.copytree(Path(FIX) / "seed-plan/leashly", original)
        (original / "pipeline.json").write_text("invalid deliberately")
        (original / "investors.json").write_text('{"investors":"invalid collection"}')
        original_bytes = {p.name: p.read_bytes() for p in original.iterdir()}
        self.assertIn("quarantine", {r["status"] for r in legacy.migrate(self.ws, original)})
        self.assertEqual(self.ws.list("legacy"), [])
        legacy.migrate(self.ws, original, dry_run=False)
        self.assertEqual(len(self.ws.list("legacy")), 5)
        before = self.ws.validate()
        legacy.migrate(self.ws, original, dry_run=False)
        self.assertEqual(self.ws.validate(), before)
        self.assertEqual({p.name: p.read_bytes() for p in original.iterdir()}, original_bytes)
        target = self.root / "seed"
        files = legacy.materialize(self.ws, target)
        self.assertNotIn("pipeline.json", files)
        self.assertNotIn("investors.json", files)
        self.assertEqual(parse_json((target / "model.json").read_bytes()),
                         parse_json(original_bytes["model.json"]))
        saved = transfer.backup(self.ws, self.ws.root / "backups" / "restore.json")
        bundle = transfer.read_file(saved)
        restore = self.root / "restore"
        transfer.import_bundle(restore, bundle, bundle["sha256"], create=True)
        self.assertEqual(Workspace(restore).validate(), before)
        self.assertEqual(Workspace(restore).list(history=True), self.ws.list(history=True))
        (original / "plan.json").write_bytes(original_bytes["plan.json"] + b" ")
        with self.assertRaises(Conflict):
            legacy.migrate(self.ws, original, dry_run=False)
        self.assertEqual(self.ws.validate(), before)

    def test_sqlite_backup_round_trip_and_zero_overwrite(self):
        self.ws.put("decision", "private", {"summary": "Data recovery test"}, classification="restricted")
        backup = recovery.make_backup(self.ws, "portable.sqlite3")
        path = Path(backup["file"])
        with self.assertRaisesRegex(SeedError, "checksum"):
            recovery.restore_backup(self.root / "not-created", path, "incorrect")
        target = self.root / "native-restored"
        result = recovery.restore_backup(target, path, backup["sha256"])
        self.assertEqual(result, self.ws.validate())
        self.assertEqual(Workspace(target).list(history=True), self.ws.list(history=True))
        with self.assertRaises(FileExistsError):
            recovery.restore_backup(target, path, backup["sha256"])

    def test_materialization_refuses_stale_output_and_can_select_current_inputs(self):
        original = self.root / "legacy"
        shutil.copytree(Path(FIX) / "seed-plan/leashly", original)
        legacy.migrate(self.ws, original, dry_run=False)
        market = next(record for record in self.ws.list("legacy") if record["key"] == "market.json")
        latest = {**market["data"], "document": {**market["data"]["document"], "tam": 99}}
        self.ws.put("legacy", "market.json", latest, expected=1, classification="restricted")
        target = self.root / "exported"
        with self.assertRaisesRegex(SeedError, "Stale legacy dependency"):
            legacy.materialize(self.ws, target)
        self.assertFalse(target.exists())
        self.assertEqual(legacy.materialize(self.ws, target, names=["market.json"]), ["market.json"])
        self.assertEqual(parse_json((target / "market.json").read_bytes())["tam"], 99)

    def test_revision_distinguishes_boolean_and_numeric_data(self):
        first = self.ws.put("assumption", "pilot", {"label": "Pilot", "value": True,
                            "unit": "count", "rationale": "Test type handling"})
        second = self.ws.put("assumption", "pilot", {**first["data"], "value": 1}, expected=1)
        self.assertEqual(second["revision"], 2)
        self.assertIs(type(second["data"]["value"]), int)

    def test_atomic_record_write(self):
        with patch.object(Workspace, "insert_links", side_effect=RuntimeError("interrupted")):
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                self.ws.put("decision", "interrupt", {"summary": "Partial"})
        self.assertFalse(self.ws.list("decision"))
        self.assertEqual(self.ws.validate()["revisions"], 1)
