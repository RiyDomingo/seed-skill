"""Source-backed research normalization, market sizing and opportunity qualification."""

from collections import defaultdict
from decimal import Decimal

from .finance import number
from .fundraising import ref
from .schema import date_value, digest, key_value, require, string
from .workspace import Workspace

PROGRAMMES = {"grant", "competition", "prize", "accelerator", "incubator"}
COMPETITORS = {"direct", "indirect", "substitute", "incumbent", "emerging"}
PATENT_STATES = {"published_application", "granted", "expired", "abandoned", "unknown"}
RESEARCH_KINDS = {"competitor", "funding_opportunity", "document", "investor", "investment_firm", "contact", "claim"}


def ingest(workspace, packet, classification="internal"):
    require(isinstance(packet, dict) and set(packet) == {"sources", "findings"}, "Use sources and findings arrays")
    require(all(isinstance(packet[k], list) for k in packet) and len(packet["findings"]) <= 100
            and len(packet["sources"]) <= 100, "Research batch is too large or invalid")
    with workspace.connect() as cx:
        cx.execute("BEGIN IMMEDIATE")
        sources = {}
        for item in packet["sources"]:
            require(isinstance(item, dict) and set(item) <= {"key", "data", "expected"}, "Invalid research source")
            key = string(item.get("key"), "source key", 150)
            require(key_value(key) not in sources, "Duplicate source key")
            row = workspace.put_on(cx, "source", key, item.get("data"),
                                   classification=classification, expected=item.get("expected"), provenance="unknown")
            sources[key_value(key)] = row
        findings = []
        for item in packet["findings"]:
            require(isinstance(item, dict) and set(item) <= {"kind", "key", "data", "observations", "expected"},
                    "Invalid finding")
            kind = item.get("kind")
            require(isinstance(kind, str) and kind in RESEARCH_KINDS, "Unsupported research record")
            key = string(item.get("key"), "finding key", 150)
            data = item.get("data")
            require(isinstance(data, dict), "Finding data must be an object")
            validate_finding(kind, data)
            observed = item.get("observations")
            require(isinstance(observed, list) and bool(observed) and len(observed) <= 12,
                    "Supply at least one source observation per finding")
            pins = []
            by_feature = defaultdict(list)
            for observation in observed:
                require(isinstance(observation, dict) and
                        {"source", "excerpt", "assessment"} <= observation.keys() <= {
                            "source", "excerpt", "assessment", "feature"},
                        "Invalid evidence observation")
                src = sources.get(key_value(observation["source"]))
                require(src is not None, "Research observation references a missing source")
                ev_key = "observation:" + digest({"finding": key, "kind": kind, "source": ref(src),
                                                  "excerpt": observation["excerpt"]})
                evidence = workspace.put_on(cx, "evidence", ev_key,
                                            {"excerpt": observation["excerpt"], "assessment": observation["assessment"]},
                                            classification=classification, links=[ref(src, "source")])
                pins.append(ref(evidence, "evidence"))
                if observation.get("feature") is not None:
                    feature = string(observation["feature"], "observation feature")
                    require(kind == "competitor" and feature in data.get("features", {}),
                            "Observation references unknown feature")
                    by_feature[feature].append(evidence["id"])
            if by_feature:
                data = {**data, "features": {key: {**row, "evidence_ids": by_feature.get(key, [])}
                                             for key, row in data["features"].items()}}
            pins = list({(pin["id"], pin["revision"]): pin for pin in pins}.values())
            findings.append(workspace.put_on(cx, kind, key, data, expected=item.get("expected"),
                                             classification=classification, links=pins))
        return findings


def validate_finding(kind, data):
    if kind == "competitor":
        require(data.get("category") in COMPETITORS, "Unknown competitor category")
        features = data.get("features", {})
        require(isinstance(features, dict), "Competitor features must be an object")
        for feature, row in features.items():
            string(feature, "feature")
            require(isinstance(row, dict) and "value" in row
                    and row.get("basis") in {"vendor_claim", "independent", "observed", "unknown"},
                    "Feature values require a basis")
    if kind == "funding_opportunity":
        require(data.get("programme_type") in PROGRAMMES, "Unknown funding programme type")
        require(isinstance(data.get("sponsor"), str) and data["sponsor"].strip(), "Sponsor is required")
        if data.get("opens_on"):
            date_value(data["opens_on"], "opening date")
        if data.get("deadline"):
            date_value(data["deadline"], "deadline")
            require(not data.get("opens_on") or data["opens_on"] <= data["deadline"],
                    "Funding closes before opening")
        for field in ("geographies", "sectors", "stages"):
            values = data.get(field, [])
            require(isinstance(values, list) and all(isinstance(x, str) and x.strip() for x in values),
                    f"Invalid funding {field}")
        for field in ("award", "equity_pct", "match_pct", "weekly_hours"):
            if data.get(field) is not None:
                number(data[field], field, maximum=100 if field.endswith("_pct") else 10**15)
        require(data.get("award") is None or isinstance(data.get("currency"), str),
                "Award value requires a currency")
    if kind == "document":
        require(data.get("document_type") == "patent", "Research document must be a patent record")
        for field in ("publication_number", "jurisdiction", "family", "assignee"):
            string(data.get(field), field, 250)
        require(data.get("legal_status") in PATENT_STATES, "Unknown patent status")
        if data.get("status_checked_on"):
            date_value(data["status_checked_on"], "patent status verification")


def evidence_status(workspace, record, on):
    trace = workspace.trace(record["id"], on)
    sources = [r for r in trace["records"] if r["kind"] == "source"]
    return trace["findings"], sources


def compare_competitors(workspace, on):
    date_value(on, "comparison date")
    entries = []
    columns = set()
    for record in workspace.list("competitor"):
        data = record["data"]
        if data.get("category") not in COMPETITORS:
            continue
        validate_finding("competitor", data)
        findings, sources = evidence_status(workspace, record, on)
        features = {}
        for key, row in data.get("features", {}).items():
            columns.add(key)
            supported = False
            for evidence_id in row.get("evidence_ids", []):
                pinned = next((link for link in record["links"] if link["role"] == "evidence"
                               and link["id"] == evidence_id), None)
                evidence = workspace.get(pinned["id"], pinned["revision"]) if pinned else None
                if evidence:
                    recent, lab_sources = evidence_status(workspace, evidence, on)
                    supported = supported or bool(not recent and evidence["status"] in {"reviewed", "approved"}
                        and any(src["data"].get("source_type") in {"experiment", "independent_test", "certification"}
                                for src in lab_sources))
            features[key] = {"value": row["value"], "basis": row["basis"],
                             "performance_verified": bool(supported and not findings
                                 and record["status"] in {"reviewed", "approved"}
                                 and row["basis"] in {"independent", "observed"})}
        entries.append({"name": data["name"], "category": data["category"], "features": features,
                        "sources": [ref(s, "source") for s in sources], "findings": findings,
                        "record": ref(record)})
    return {"columns": sorted(columns), "profiles": entries}


def normalize_list(values):
    require(isinstance(values, list) and all(isinstance(value, str) for value in values), "Expected screening values")
    return {value.strip().casefold() for value in values if value.strip()}


def opportunities(workspace, on, programme, profile):
    date_value(on, "screening date")
    require(programme in {"grant", "accelerator"} and isinstance(profile, dict), "Invalid programme screen")
    subset = {"grant", "competition", "prize"} if programme == "grant" else {"accelerator", "incubator"}
    output = []
    for record in workspace.list("funding_opportunity"):
        data = record["data"]
        if data["programme_type"] not in subset:
            continue
        validate_finding("funding_opportunity", data)
        findings, sources = evidence_status(workspace, record, on)
        official = any(src["data"].get("official") is True and src["data"].get("url") for src in sources)
        deadline = data.get("deadline")
        opens = data.get("opens_on")
        if deadline and deadline < on:
            status = "closed"
        elif not official or findings or record["status"] not in {"reviewed", "approved"}:
            status = "unverified"
        elif opens and opens > on:
            status = "upcoming"
        elif deadline and (opens or data.get("applications_open") is True):
            status = "open"
        elif data.get("recurring") is True:
            status = "recurring"
        else:
            status = "unverified"
        fit = {}
        for field in ("geographies", "sectors", "stages"):
            mandate, proposed = normalize_list(data.get(field, [])), normalize_list(profile.get(field, []))
            fit[field] = bool(mandate & proposed or "global" in mandate) if mandate and proposed else None
        for field in ("equity_pct", "match_pct", "weekly_hours"):
            limit = profile.get("max_" + field)
            fit[field] = (number(data[field], field) <= number(limit, "screening limit")
                          if limit is not None and data.get(field) is not None else None)
        eligibility = "ineligible" if False in fit.values() else (
            "meets_screened_criteria" if all(x is True for x in fit.values()) else "needs_review")
        output.append({"record": ref(record), "name": data["name"], "programme_type": data["programme_type"],
                       "sponsor": data["sponsor"], "status": status, "official_source": official,
                       "deadline": deadline, "eligibility": eligibility, "screen": fit, "facts": data,
                       "findings": findings, "source_refs": [ref(s, "source") for s in sources]})
    return sorted(output, key=lambda item: (item["status"] != "open", item["eligibility"] == "ineligible",
                                           item["deadline"] or "9999-12-31", item["name"]))


def patent_landscape(workspace, on, query=None):
    today = date_value(on, "patent review date")
    terms = {term.casefold() for term in string(query, "keyword query").split()} if query else set()
    families = defaultdict(list)
    duplicates = []
    seen = set()
    for record in workspace.list("document"):
        data = record["data"]
        if data["document_type"] != "patent":
            continue
        validate_finding("document", data)
        key = (data["jurisdiction"].upper(), "".join(data["publication_number"].upper().split()))
        if key in seen:
            duplicates.append({"publication": key[1], "jurisdiction": key[0], "record": ref(record)})
            continue
        seen.add(key)
        haystack = " ".join(str(data.get(k, "")) for k in ("name", "assignee", "abstract", "cluster")).casefold()
        if not all(term in haystack for term in terms):
            continue
        findings, sources = evidence_status(workspace, record, on)
        checked = data.get("status_checked_on")
        official = any(source["data"].get("official") is True for source in sources)
        age = (today - date_value(checked, "status checked date")).days if checked else None
        current = official and not findings and record["status"] in {"reviewed", "approved"} and age is not None and 0 <= age <= 90
        families[data["family"]].append({"record": ref(record), "title": data["name"],
                                        "publication_number": key[1], "jurisdiction": key[0],
                                        "assignee": data["assignee"], "inventors": data.get("inventors", []),
                                        "cluster": data.get("cluster"),
                                        "reported_status": data["legal_status"],
                                        "current_status": data["legal_status"] if current else "unknown",
                                        "status_checked_on": checked})
    return {"families": dict(sorted(families.items())), "duplicates": duplicates,
            "scope": "Landscape and prior-art leads. Assess legal status and freedom to operate with counsel."}


def market_size(doc):
    require(isinstance(doc, dict), "Market scenario must be an object")
    currency = string(doc.get("currency"), "currency")
    require(len(currency) == 3 and currency.isascii() and currency.isupper() and currency.isalpha(), "Invalid currency")
    segments = doc.get("segments")
    require(isinstance(segments, list) and segments, "Provide disjoint customer segments")
    require(doc.get("segments_disjoint") is True, "Confirm how overlapping segments were reconciled")
    seen = set()
    bottom, serviceable = Decimal(0), Decimal(0)
    rows = []
    for segment in segments:
        require(isinstance(segment, dict), "Invalid market segment")
        key = string(segment.get("population_id"), "segment population ID", 150).casefold()
        require(key not in seen, "Population is counted more than once")
        seen.add(key)
        require(bool(segment.get("basis")), "Each segment needs a source reference or explicit assumption rationale")
        customers = number(segment.get("customers"), "segment customers")
        frequency = number(segment.get("annual_purchases"), "annual purchase frequency")
        price = number(segment.get("price"), "price")
        reachable = number(segment.get("reachable_share", 1), "reachable share", maximum=1)
        potential = customers * frequency * price
        bottom += potential
        serviceable += potential * reachable
        rows.append({"population_id": key, "tam": str(potential), "sam": str(potential * reachable),
                     "basis": segment["basis"], "geography": segment.get("geography")})
    top = doc.get("top_down")
    top_value = None
    if top is not None:
        require(isinstance(top, dict) and bool(top.get("basis")), "Top-down comparator requires its source or rationale")
        top_value = number(top.get("value"), "top-down value", maximum=10**24)
    cases = doc.get("scenarios", {})
    require(isinstance(cases, dict) and cases, "Provide explicit adoption scenarios")
    outputs = {}
    for name, case in cases.items():
        require(isinstance(case, dict), "Invalid penetration scenario")
        share = number(case.get("penetration"), "market penetration", maximum=1)
        growth = number(case.get("growth", 0), "annual market growth", minimum=-1, maximum=1)
        multiplier = number(case.get("price_multiplier", 1), "price multiplier", maximum=10)
        years = case.get("years")
        require(type(years) is int and 1 <= years <= 20, "Use an explicit scenario horizon")
        future = serviceable * (1 + growth) ** years * multiplier
        outputs[name] = {"years": years, "sam": str(future), "som": str(future * share),
                         "penetration": str(share), "growth": str(growth), "price_multiplier": str(multiplier)}
    return {"currency": currency, "tam": str(bottom), "sam": str(serviceable), "segments": rows,
            "top_down": str(top_value) if top_value is not None else None,
            "reconciliation": {"bottom_minus_top": str(bottom - top_value) if top_value is not None else None,
                               "note": doc.get("reconciliation")},
            "scenarios": outputs}
