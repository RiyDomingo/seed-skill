"""Seven synthetic venture workflows using the shared runtime in extracted packages."""

from decimal import Decimal
import json
from pathlib import Path
from subprocess import run
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from scripts.skills import FILES, publish
from seed_core import diligence, fundraising
from seed_core.schema import canonical
from seed_core.workspace import Workspace


ON = "2026-11-24"
DEVICE = {"id": "device", "kind": "manufacturing", "volume": 20, "price": 1000,
          "capacity": 25, "utilisation": 0.9, "yield": 0.9, "material_cost": 210,
          "labour_cost": 40, "rework_cost": 12, "inventory_months": 1}
CASES = {
    "saas": [{"id": "software", "kind": "recurring", "monthly_new": 30,
              "price": 50, "unit_cost": 12, "churn": 0.03}],
    "marketplace": [{"id": "order", "kind": "transaction", "volume": 200,
                     "price": 80, "take_rate": 0.14, "unit_cost": 2}],
    "manufacturing": [{**DEVICE, "id": "component", "volume": 90, "capacity": 110,
                       "price": 1900, "material_cost": 450}],
    "hardware": [DEVICE],
    "biotechnology": [{"id": "license", "kind": "licensing", "volume": 0,
                       "price": 1000000}],
    "medical_technology": [{**DEVICE, "id": "instrument", "volume": 0, "price": 13000}],
    "hybrid": [DEVICE, {"id": "analysis", "kind": "recurring", "monthly_new": 10,
                        "price": 80, "unit_cost": 25, "churn": 0.01}],
}


class SystemIntegration(unittest.TestCase):
    def test_installed_workflows_for_seven_venture_types(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            bundles = publish(root / "bundles", sorted(FILES), archive=True)
            installed = root / "installed"
            for archive in bundles:
                with ZipFile(archive) as bundle:
                    self.assertIsNone(bundle.testzip())
                    bundle.extractall(installed)
            self.assertEqual(len(bundles), 20)

            for index, (archetype, streams) in enumerate(CASES.items()):
                with self.subTest(archetype=archetype):
                    self.exercise(installed, root / archetype, archetype, streams, index)

    def exercise(self, installed, root, archetype, streams, index):
        root.mkdir()
        venture = root / "venture"
        def command(skill, *args, fail=False):
            result = run([sys.executable, str(installed / f"seed-{skill}/scripts/seed_workspace.py"),
                          "--workspace", str(venture), *map(str, args)], cwd=root,
                         capture_output=True, text=True, encoding="utf-8", timeout=30)
            if fail:
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                return result.stderr
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(result.stdout)

        def document(name, data):
            path = root / (name + ".json")
            path.write_bytes(canonical(data))
            return path

        ref = fundraising.ref
        title = "Synthetic " + archetype
        command("readiness", "init", "--name", title, "--currency", "USD", "--jurisdiction", "US")
        ws = Workspace(venture)
        source = ws.put("source", "example", {"title": "Synthetic registry", "publisher": "Example",
            "url": "https://example.org/synthetic", "retrieved_on": ON, "max_age_days": 60, "official": True},
            classification="public", provenance="verified_external", status="reviewed")
        evidence = ws.put("evidence", "example", {"excerpt": "Synthetic trial demonstrates a prototype.",
            "assessment": "Fixture only", "validation_type": "prototype"}, classification="public",
            links=[ref(source, "source")], provenance="verified_external", status="reviewed")
        claim = ws.put("claim", "prototype", {"statement": "A synthetic prototype has been reviewed."},
            classification="public", provenance="verified_external", status="reviewed", links=[ref(evidence, "evidence")])
        market_input = {"currency": "USD", "segments_disjoint": True, "segments": [
            {"population_id": archetype, "customers": 1000 + 100 * index, "annual_purchases": 2,
             "price": 50, "reachable_share": 0.2, "basis": "Synthetic assumption"}],
            "scenarios": {"base": {"penetration": 0.1, "years": 3}}}
        model_input = {"name": title, "currency": "USD", "archetype": archetype, "streams": streams,
            "start": "2027-01", "months": 60 if index % 2 else 36, "opening_cash": 100000,
            "minimum_cash_reserve": 20000, "monthly_costs": {"payroll": 8000, "rd": 4000},
            "working_capital": {"receivable_days": 31, "payable_days": 30},
            "milestones": {"pilot": 3},
            "financing": [{"id": "award", "kind": "grant", "month": 2, "amount": 50000, "requires": ["pilot"]}],
            "one_offs": [{"kind": "capex", "month": 3, "amount": 2800}],
            "scenarios": {"downside": {"financing_delay_months": 2, "volume": 0.7}, "upside": {"volume": 1.2}}}

        outputs = {}
        for name, data, area, action in (("market", market_input, "research", "market"),
                                         ("model", model_input, "finance", "forecast")):
            pinned = ws.put("assumption", name, {"label": name, "value": data, "rationale": "Synthetic input",
                "unit": "scenario"}, classification="public", provenance="assumption", status="reviewed")
            saved = command(name, area, action, document(name, data), "--save-key", name,
                            "--assumption-id", pinned["id"])
            outputs[name] = ws.put(saved["kind"], name, saved["data"], expected=1, links=saved["links"],
                                   classification="public", status="reviewed", provenance="calculated")
        model, market = outputs["model"], outputs["market"]
        self.assertEqual(Decimal(market["data"]["tam"]), (1000 + 100 * index) * 100)
        month = model["data"]["forecast"]["scenarios"]["base"]["months"][0]
        self.assertEqual(Decimal(month["revenue"]), [1500, 2240, 169290, 20000, 0, 0, 20800][index])
        command("model", "finance", "spreadsheet", model["id"], "base", root / "forecast.xlsx")
        with ZipFile(root / "forecast.xlsx") as book:
            self.assertIsNone(book.testzip())
        cap = command("capital", "finance", "capital", root / "model.json")
        self.assertEqual(Decimal(cap["scenarios"]["base"]["unfunded"]["funding_inflow"]), 0)
        terms = command("terms", "finance", "round", document("round", {
            "holders": {"Synthetic founder": 1000000}, "pre_money": 4000000, "new_money": 1000000,
            "instruments": [{"name": "Synthetic SAFE", "kind": "safe", "amount": 100000,
                             "cap": 3000000, "cap_basis": "post_money"}]}))
        self.assertAlmostEqual(sum(float(x["post_ownership_pct"]) for x in terms["holders"]), 100, places=6)

        provenance = {"links": [ref(evidence, "evidence")], "classification": "public", "status": "reviewed"}
        ws.put("competitor", "example", {"name": "Synthetic incumbent", "category": "incumbent",
            "features": {"coverage": {"value": "Reported", "basis": "vendor_claim"}}}, **provenance)
        comp = command("scout", "research", "competitors", ON)
        self.assertFalse(comp["profiles"][0]["features"]["coverage"]["performance_verified"])
        for programme, skill in (("grant", "grants"), ("accelerator", "accelerators")):
            ws.put("funding_opportunity", programme, {"name": "Synthetic " + programme,
                "programme_type": programme, "sponsor": "Example", "opens_on": ON,
                "deadline": "2026-12-30", "geographies": ["US"]}, **provenance)
            result = command(skill, "research", skill, ON, document("screen", {"geographies": ["US"]}))
            self.assertEqual(result[0]["status"], "open")
        ws.put("document", "patent", {"name": "Synthetic publication", "document_type": "patent",
            "publication_number": "EXAMPLE-1", "jurisdiction": "US", "family": "synthetic-family",
            "assignee": "Example", "legal_status": "unknown"}, **provenance)
        self.assertEqual(list(command("patents", "research", "patents", ON)["families"]), ["synthetic-family"])

        investor = ws.put("investor", "example fund", {"name": "Synthetic Fund"}, **provenance)
        contact = ws.put("contact", "investor@example.org", {"name": "Synthetic contact",
            "email": "investor@example.org", "public_business": True, "investor_id": investor["id"]},
            classification="public", status="reviewed", links=[ref(source, "source")])
        ws.put("relationship", "synthetic introduction", {"description": "Known connection",
            "from_id": contact["id"], "to_id": investor["id"], "relationship_status": "verified"},
            status="reviewed", links=[ref(contact), ref(investor), ref(evidence, "evidence")])
        scores = document("scores", {"criteria": {name: {"rating": 1, "confidence": 0.9,
            "evidence": [evidence["id"]]} for name in fundraising.WEIGHTS}})
        self.assertTrue(command("investors", "fundraising", "qualify", investor["id"], scores, ON)["priority_eligible"])
        paths = command("network", "fundraising", "paths", contact["id"], investor["id"], "--on", ON)
        self.assertEqual(paths[0]["status"], "verified")
        raise_record = command("crm", "fundraising", "open", investor["id"], "seed", "Synthetic round",
                               "--contact", contact["id"])
        oid = raise_record["id"]
        command("crm", "fundraising", "advance", oid, "qualified", ON, "Synthetic review", "--expected", 1)
        brief = command("coach", "fundraising", "meeting-brief", oid, ON)
        self.assertEqual(brief["investor"]["id"], investor["id"])
        draft = command("closer", "fundraising", "draft", oid, document("email", {
            "sender": "founder@example.org", "subject": "Synthetic outreach",
            "body": "A synthetic prototype has been reviewed. Reply to opt out.",
            "verified_fact_ids": [claim["id"]]}), ON)
        draft_id, confirmation = draft["id"], draft["data"]["payload_sha256"]
        eml = root / "message.eml"
        self.assertIn("approval", command("closer", "fundraising", "eml", draft_id, confirmation, eml, ON, fail=True))
        command("closer", "fundraising", "approve", draft_id, confirmation, "Synthetic signer", ON)
        command("closer", "fundraising", "eml", draft_id, confirmation, eml, ON)
        self.assertIn(b"To: investor@example.org", eml.read_bytes())

        ws.put("document", "overview", {"name": "Synthetic overview", "document_type": "summary",
            "disclosure": "initial"}, status="approved", links=[ref(model), ref(market), ref(claim)])
        ws.put("document", "restricted", {"name": "Synthetic restricted lab record", "document_type": "technical",
            "disclosure": "nda"}, status="approved", classification="restricted")
        room = command("dataroom", "readiness", "dataroom", "initial", ON)
        self.assertEqual([x["name"] for x in room["candidates"]], ["Synthetic overview"])
        ready = command("readiness", "readiness", "assess", document("readiness", {
            "dimensions": {"technology": {"level": 4, "evidence": [evidence["id"]]}}}), ON)
        self.assertEqual(ready["dimensions"]["technology"]["supported"], 2)
        self.assertFalse(ready["investment_ready"])

        assert_market = {"key": "tam", "source_id": market["id"], "revision": market["revision"],
                         "path": ["tam"], "unit_path": ["currency"], "unit": "USD",
                         "numeric": True, "value": market["data"]["tam"]}
        sections = [{"heading": "Synthetic market", "text": f"Annual TAM is ${int(Decimal(market['data']['tam'])):,}.",
                     "records": [market["id"], model["id"], claim["id"]], "assertions": [assert_market]}]
        for skill, category, suffix in (("plan", "plan", "md"), ("deck", "deck", "html"), ("updates", "update", "md")):
            exported = command(skill, "readiness", "materials", document(category, {"title": title,
                "type": category, "audience": "public", "sections": sections,
                "risks": ["Adoption remains an assumption."]}), ON, root / f"{category}.{suffix}")
            self.assertEqual(len(exported["links"]), 3)
            self.assertIn(market["id"], (root / f"{category}.{suffix}").read_text(encoding="utf-8"))
        self.assertEqual(command("audit", "readiness", "audit", ON)["blocking"], 0)
        verdict = command("committee", "readiness", "committee", document("panel", {
            "perspectives": {role: {"case": "Synthetic prototype", "counterargument": "Demand is unknown",
                "recommendation": "MONITOR", "risks": "Adoption risk", "evidence_to_change": "Pilot outcome",
                "evidence": [claim["id"]]} for role in diligence.PERSPECTIVES},
            "strongest_case": "Prototype", "strongest_counterargument": "Market assumption",
            "decision_changing_evidence": "Pilot outcome"}), ON)
        self.assertEqual(verdict["decision"], "MONITOR")
        preview = command("market", "preview-export", "--id", market["id"])
        exchange = root / "public.seed-exchange.json"
        command("market", "export", exchange, "--id", market["id"], "--confirm", preview["sha256"])
        self.assertNotIn(b"example.org", exchange.read_bytes())
        ws.validate()
