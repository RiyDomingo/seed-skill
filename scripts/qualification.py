#!/usr/bin/env python3
"""Generate the synthetic qualification packet and checks for the twenty native skills."""

import argparse
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from seed_core.diligence import PERSPECTIVES
from seed_core.fundraising import WEIGHTS, ref
from seed_core.schema import canonical
from seed_core.transfer import snapshot
from seed_core.workspace import Workspace

ON = "2026-11-24"
CONFIG = {"name": "Synthetic instrumentation venture", "currency": "USD", "jurisdiction": "US"}


def qualification(root):
    root.mkdir()
    ws = Workspace.init(root.parent / "synthetic-store", CONFIG)

    def record(kind, key, data, links=()):
        return ws.put(kind, key, data, classification="public", status="reviewed",
                      provenance="founder", links=list(links))

    source = record("source", "synthetic registry", {"title": "Synthetic registry",
        "publisher": "Example laboratory", "url": "https://example.org/synthetic",
        "retrieved_on": ON, "official": True})
    evidence = record("evidence", "prototype", {"excerpt": "The synthetic prototype works in the lab.",
        "assessment": "Synthetic fixture evidence", "validation_type": "prototype"}, [ref(source, "source")])
    claim = ws.put("claim", "prototype", {"statement": "The synthetic prototype works in the lab."},
                   classification="public", status="reviewed", provenance="verified_external",
                   links=[ref(evidence, "evidence")])
    investor = record("investor", "synthetic fund", {"name": "Synthetic fund"}, [ref(evidence, "evidence")])
    contact = record("contact", "synthetic contact", {"name": "Synthetic analyst",
                    "email": "analyst@example.org", "public_business": True, "investor_id": investor["id"]},
                     [ref(source, "source")])
    record("relationship", "synthetic introduction", {"description": "Synthetic connection",
           "from_id": contact["id"], "to_id": investor["id"], "relationship_status": "verified"},
           [ref(contact), ref(investor), ref(evidence, "evidence")])
    record("competitor", "synthetic competitor", {"name": "Synthetic incumbent",
           "category": "incumbent", "features": {"coverage": {"basis": "vendor_claim", "value": "Broad"}}},
           [ref(evidence, "evidence")])
    for kind in ("grant", "accelerator"):
        record("funding_opportunity", kind, {"name": "Synthetic " + kind, "programme_type": kind,
               "sponsor": "Example lab", "opens_on": ON, "deadline": "2026-12-30", "geographies": ["US"]},
               [ref(evidence, "evidence")])
    record("document", "synthetic patent", {"name": "Synthetic publication", "document_type": "patent",
           "disclosure": "public", "family": "synthetic-family", "publication_number": "EXAMPLE-1",
           "jurisdiction": "US", "assignee": "Example lab", "legal_status": "unknown"},
           [ref(evidence, "evidence")])
    files = {
        "config": CONFIG,
        "public.seed-exchange": snapshot(ws),
        "screen": {"geographies": ["US"]},
        "assess": {"dimensions": {"technology": {"level": 4, "evidence": [evidence["id"]]}}},
        "assumptions": {"name": CONFIG["name"], "archetype": "hardware", "currency": "USD",
            "months": 36, "start": "2027-01", "opening_cash": 15000,
            "streams": [{"id": "prototype", "kind": "manufacturing", "volume": 25, "capacity": 50,
                         "price": 1200, "yield": 0.9, "material_cost": 500}]},
        "market": {"currency": "USD", "segments_disjoint": True, "segments": [
            {"population_id": "labs", "customers": 1000, "annual_purchases": 1,
             "price": 1000, "reachable_share": 0.2, "basis": "Synthetic assumption"}],
            "scenarios": {"base": {"penetration": 0.1, "years": 3}}},
        "score": {"criteria": {name: {"rating": 0.9, "confidence": 0.9, "evidence": [evidence["id"]]}
                               for name in WEIGHTS}},
        "round": {"holders": {"Synthetic founder": 1000000}, "pre_money": 4000000, "new_money": 1000000},
        "committee": {
            "perspectives": {role: {"case": "Reviewed prototype", "counterargument": "Unknown demand",
                "recommendation": "MONITOR", "risks": "Adoption", "evidence_to_change": "Pilot demand",
                "evidence": [claim["id"]]} for role in sorted(PERSPECTIVES)},
            "strongest_case": "Prototype", "strongest_counterargument": "Adoption",
            "decision_changing_evidence": "Pilot demand"},
    }
    for kind in ("plan", "deck", "update"):
        files[kind] = {"title": CONFIG["name"], "type": kind, "audience": "public",
                      "sections": [{"heading": "Prototype",
                                    "text": "The synthetic prototype works in the lab.",
                                    "records": [claim["id"]]}],
                      "risks": ["Adoption remains unverified."]}
    for name, data in files.items():
        (root / (name + ".json")).write_bytes(canonical(data))

    calls = {
        "seed-accelerators": ["research", "accelerators", ON, "screen.json"],
        "seed-audit": ["readiness", "audit", ON],
        "seed-capital": ["finance", "capital", "assumptions.json"],
        "seed-closer": ["fundraising", "pipeline", ON],
        "seed-coach": ["readiness", "plan-workflow", "fundraising diligence"],
        "seed-committee": ["readiness", "committee", "committee.json", ON],
        "seed-crm": ["fundraising", "open", investor["id"], "synthetic-seed", "Synthetic round",
                     "--contact", contact["id"]],
        "seed-dataroom": ["readiness", "dataroom", "public", ON],
        "seed-deck": ["readiness", "materials", "deck.json", ON, "synthetic-deck.html"],
        "seed-grants": ["research", "grants", ON, "screen.json"],
        "seed-investors": ["fundraising", "qualify", investor["id"], "score.json", ON],
        "seed-market": ["research", "market", "market.json"],
        "seed-model": ["finance", "forecast", "assumptions.json"],
        "seed-network": ["fundraising", "paths", contact["id"], investor["id"], "--on", ON],
        "seed-patents": ["research", "patents", ON],
        "seed-plan": ["readiness", "materials", "plan.json", ON, "synthetic-plan.md"],
        "seed-readiness": ["readiness", "assess", "assess.json", ON],
        "seed-scout": ["research", "competitors", ON],
        "seed-terms": ["finance", "round", "round.json"],
        "seed-updates": ["readiness", "materials", "update.json", ON, "synthetic-update.md"],
    }
    (root / "commands.json").write_bytes(canonical({
        "bootstrap": ["import", "public.seed-exchange.json", "--create", "--config", "config.json",
                      "--confirm", files["public.seed-exchange"]["sha256"]],
        "calls": calls,
    }))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with TemporaryDirectory() as scratch:
        root = Path(scratch).resolve() / "qualification"
        qualification(root)
        with ZipFile(args.output, "x") as bundle:
            for path in sorted(root.iterdir()):
                bundle.write(path, path.name)


if __name__ == "__main__":
    main()
