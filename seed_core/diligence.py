"""Evidence-based material audits, readiness and controlled diligence inventories."""

from decimal import Decimal, InvalidOperation
from html import escape
import re

from .fundraising import ref
from .schema import LEVELS, canonical, date_value, require, string
from .workspace import Workspace

AUDIENCES = ("public", "initial", "qualified", "nda", "restricted")
AUDIENCE_LEVEL = {"public": 0, "initial": 1, "qualified": 1, "nda": 2, "restricted": 3}
SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL")
RUBRIC = {
    "technology": ("concept", "prototype", "computational_verification", "experimental_validation", "commercial_deployment"),
    "manufacturing": ("process_concept", "workshop_samples", "pilot_line", "process_validation", "production"),
    "commercial": ("customer_hypothesis", "discovery", "customer_pilot", "paid_deployment", "repeat_sales"),
    "regulatory": ("route_hypothesis", "pathway_assessment", "regulatory_plan", "compliance_testing", "certification"),
    "intellectual_property": ("ip_inventory", "ownership_review", "prior_art_review", "ip_strategy", "enforceable_rights"),
    "team": ("roles_defined", "founder_commitment", "core_team", "execution_record", "delivery_capacity"),
    "financial": ("cost_hypothesis", "cost_estimates", "reconciled_forecast", "verified_actuals", "financial_controls"),
    "investment": ("capital_hypothesis", "investment_materials", "use_of_funds", "reviewed_data_room", "diligence_completed"),
}
PERSPECTIVES = {"vc_partner", "technical_diligence", "financial_analysis", "commercialisation", "risk_governance"}
RECOMMENDATIONS = {"INVEST", "INVEST SUBJECT TO CONDITIONS", "MONITOR", "DECLINE", "INSUFFICIENT EVIDENCE"}


def retrieve_value(data, path):
    require(isinstance(path, list) and 1 <= len(path) <= 24, "Invalid assertion path")
    for part in path:
        if isinstance(data, dict) and isinstance(part, str) and part in data:
            data = data[part]
        elif isinstance(data, list) and type(part) is int and 0 <= part < len(data):
            data = data[part]
        else:
            raise KeyError("Assertion path does not exist")
    return data


def same_value(reported, recorded, numeric):
    if not numeric:
        return canonical(reported) == canonical(recorded)
    try:
        a, b = Decimal(str(reported)), Decimal(str(recorded))
        return a.is_finite() and b.is_finite() and a == b
    except InvalidOperation:
        return False


def audit(workspace, on, ids=None):
    date_value(on, "audit date")
    with workspace.connect() as cx:
        cx.execute("BEGIN")
        return audit_on(cx, on, ids)


def audit_on(cx, on, ids=None):
    findings = []
    assertions = {}

    def add(rule, severity, record, detail):
        findings.append({"rule": rule, "severity": severity, "record": ref(record), "detail": detail})

    rows = Workspace.list_on(cx)
    if ids is not None:
        wanted = set(ids)
        rows = [row for row in rows if row["id"] in wanted]
        require(len(rows) == len(wanted), "Audit references an unknown record")
    for record in rows:
        data = record["data"]
        trace = Workspace.trace_on(cx, record["id"], on)
        for finding in trace["findings"]:
            high = finding["type"] in {"conflicting_evidence", "disputed", "stale_dependency"}
            add(finding["type"], "HIGH" if high else "MEDIUM", record, finding)
        audience = data.get("audience")
        if audience is not None and (not isinstance(audience, str) or audience not in AUDIENCE_LEVEL or
                LEVELS.index(record["classification"]) > AUDIENCE_LEVEL[audience]):
            add("disclosure", "CRITICAL", record, "Material visibility exceeds its classification.")
        refs = {(item["id"], item["revision"]) for item in record["links"]}
        if record["kind"] == "claim" and record["provenance"] in {"hypothesis", "unknown"}:
            add("unsupported_claim", "HIGH", record, "A hypothesis or unknown is still unresolved.")
        if record["kind"] == "financial_model" and "forecast" in data:
            from .finance import validate_rows
            try:
                scenarios = data["forecast"]["scenarios"]
                require(isinstance(scenarios, dict) and "base" in scenarios, "Missing forecast scenarios")
                for scenario in scenarios.values():
                    summary = scenario["summary"]
                    require(isinstance(scenario["months"], list) and len(scenario["months"]) in {36, 60},
                            "Invalid forecast horizon")
                    validate_rows(scenario["months"], Decimal(summary["opening_cash"]),
                                  Decimal(summary["opening_net_working_capital"]))
                    if sum(Decimal(row["revenue"]) for row in scenario["months"]) != Decimal(summary["total_revenue"]):
                        raise ValueError("Revenue sum differs")
            except (ValueError, TypeError, KeyError, ArithmeticError, AttributeError):
                add("financial_reconciliation", "CRITICAL", record, "Forecast rows and totals disagree.")
        declared = data.get("assertions", [])
        if not isinstance(declared, list):
            add("invalid_assertions", "HIGH", record, "Expected assertion objects.")
            continue
        for claim in declared:
            try:
                result = validate_assertion(cx, claim, refs)
            except (ValueError, TypeError, KeyError):
                add("untraceable_assertion", "HIGH", record, "Assertion lacks a valid pinned reference or value path.")
                continue
            key, unit, equal = result
            if not equal:
                add("contradicts_input", "CRITICAL", record, {"key": key, "unit": unit})
            previous = assertions.get(key)
            if previous and (unit != previous[0] or
                             not same_value(claim["value"], previous[1], claim.get("numeric") is True)):
                add("cross_document_conflict", "CRITICAL", record,
                    {"key": key, "other_record": previous[2], "unit": unit})
            assertions[key] = (unit, claim["value"], record["id"])
    return {"findings": sorted(findings, key=lambda x: SEVERITIES.index(x["severity"])),
            "blocking": sum(x["severity"] in {"HIGH", "CRITICAL"} for x in findings),
            "reviewed_records": len(rows)}


def validate_assertion(cx, assertion, references):
    require(isinstance(assertion, dict), "Invalid assertion")
    key = string(assertion["key"], "assertion key").casefold()
    unit = string(assertion["unit"], "assertion unit")
    source = (assertion["source_id"], assertion["revision"])
    require(isinstance(source[0], str) and type(source[1]) is int, "Invalid assertion reference")
    require(source in references, "Assertion input must be pinned")
    record = Workspace.get_on(cx, *source)
    require(record and record["provenance"] != "unknown", "Source provenance unknown")
    recorded = retrieve_value(record["data"], assertion["path"])
    recorded_unit = (retrieve_value(record["data"], assertion["unit_path"])
                     if "unit_path" in assertion else record["data"].get("unit"))
    if recorded_unit is not None:
        require(unit == recorded_unit, "Assertion unit disagrees with its pinned input")
    return key, unit, same_value(assertion["value"], recorded, assertion.get("numeric") is True)


def readiness(workspace, doc, on):
    date_value(on, "readiness date")
    require(isinstance(doc, dict), "Readiness input must be an object")
    dimensions = doc.get("dimensions")
    require(isinstance(dimensions, dict) and dimensions.keys() <= RUBRIC.keys(), "Unknown readiness dimension")
    requirements = doc.get("minimum_levels", dict.fromkeys(RUBRIC, 3))
    require(isinstance(requirements, dict) and requirements.keys() == RUBRIC.keys()
            and all(type(v) is int and 1 <= v <= 5 for v in requirements.values()), "Invalid readiness thresholds")
    output = {}
    pins = []
    for name, stages in RUBRIC.items():
        dimension = dimensions.get(name, {})
        require(isinstance(dimension, dict), "Invalid assessed dimension")
        proposed = dimension.get("level", 0)
        references = dimension.get("evidence", [])
        require(type(proposed) is int and 0 <= proposed <= 5 and isinstance(references, list)
                and all(isinstance(rid, str) for rid in references),
                "Readiness levels are 0 through 5 and need evidence IDs")
        support = []
        for rid in references:
            record = workspace.get(rid)
            require(record and record["kind"] in {"evidence", "claim"}, "Invalid readiness evidence")
            validation = record["data"].get("validation_type")
            trace = workspace.trace(record["id"], on)
            has_source = any(r["kind"] == "source" for r in trace["records"])
            if validation in stages and record["status"] in {"reviewed", "approved"} and not trace["findings"] and has_source:
                support.append(stages.index(validation) + 1)
                pins.append(ref(record))
        supported = min(proposed, max(support, default=0))
        output[name] = {"requested": proposed, "supported": supported, "minimum": requirements[name],
                        "stage": stages[supported - 1] if supported else "insufficient_evidence"}
    report = audit(workspace, on)
    return {"investment_ready": all(row["supported"] >= row["minimum"] for row in output.values())
            and not report["blocking"], "dimensions": output, "blocking_findings": report["blocking"],
            "links": list({(x["id"], x["revision"]): x for x in pins}.values())}


def dataroom(workspace, audience, on):
    date_value(on, "data room review date")
    require(isinstance(audience, str) and audience in AUDIENCES, "Unknown diligence audience")
    ceiling = AUDIENCES.index(audience)
    items = []
    with workspace.connect() as cx:
        cx.execute("BEGIN")
        rows = Workspace.list_on(cx, "document")
        eligible = {}
        for record in rows:
            data = record["data"]
            stage = data.get("disclosure", "restricted")
            require(isinstance(stage, str) and stage in AUDIENCES, "Invalid document disclosure level")
            if AUDIENCES.index(stage) <= ceiling and LEVELS.index(record["classification"]) <= AUDIENCE_LEVEL[audience]:
                trace = Workspace.trace_on(cx, record["id"], on)
                if all(fits_audience(row, audience) for row in trace["records"]):
                    eligible[record["id"]] = (record, {row["id"] for row in trace["records"]})
        closure = set().union(*(ids for _, ids in eligible.values()))
        assessment = audit_on(cx, on, closure)
        for record, ids in eligible.values():
            data = record["data"]
            findings = [f for f in assessment["findings"] if f["record"]["id"] in ids]
            items.append({"record": ref(record), "name": data["name"], "document_type": data["document_type"],
                          "disclosure": data.get("disclosure", "restricted"), "status": record["status"],
                          "findings": findings, "review_candidate": record["status"] == "approved" and not findings})
    return {"audience": audience, "candidates": items, "candidate_count": len(items),
            "automatic_disclosure": False}


def fits_audience(record, audience):
    default = "restricted" if record["kind"] == "document" else "public"
    stage = record["data"].get("disclosure", default)
    return (isinstance(stage, str) and stage in AUDIENCES and
            AUDIENCES.index(stage) <= AUDIENCES.index(audience) and
            LEVELS.index(record["classification"]) <= AUDIENCE_LEVEL[audience])


def committee(workspace, doc, on):
    date_value(on, "committee date")
    perspectives = doc.get("perspectives") if isinstance(doc, dict) else None
    require(isinstance(perspectives, dict) and perspectives.keys() == PERSPECTIVES,
            "Supply the five review perspectives")
    output, recommendations = {}, set()
    absent = False
    for role, perspective in perspectives.items():
        require(isinstance(perspective, dict), "Each perspective needs a recommendation and evidence")
        rec = perspective.get("recommendation")
        require(isinstance(rec, str) and rec in RECOMMENDATIONS, "Unknown investment decision")
        recommendations.add(rec)
        evidence = perspective.get("evidence", [])
        require(isinstance(evidence, list) and all(isinstance(rid, str) for rid in evidence),
                "Perspective evidence must be a list of identifiers")
        pins = []
        for record_id in evidence:
            record = workspace.get(record_id)
            require(record is not None, "Perspective cites an unknown record")
            if record["status"] in {"reviewed", "approved"} and not workspace.trace(record_id, on)["findings"]:
                pins.append(ref(record))
        absent = absent or not pins
        output[role] = {"recommendation": rec, "reviewed_inputs": pins,
                        **{key: string(perspective.get(key), key, 10000)
                           for key in ("case", "counterargument", "risks", "evidence_to_change")}}
    audit_result = audit(workspace, on)
    if absent or "INSUFFICIENT EVIDENCE" in recommendations:
        verdict = "INSUFFICIENT EVIDENCE"
    elif "DECLINE" in recommendations:
        verdict = "DECLINE"
    elif audit_result["blocking"] or "MONITOR" in recommendations:
        verdict = "MONITOR"
    elif "INVEST SUBJECT TO CONDITIONS" in recommendations:
        verdict = "INVEST SUBJECT TO CONDITIONS"
    else:
        verdict = "INVEST"
    return {"mode": "structured_perspectives", "decision": verdict, "perspectives": output,
            "blocking_findings": audit_result["blocking"],
            "strongest_case": string(doc.get("strongest_case"), "strongest case", 10000),
            "strongest_counterargument": string(doc.get("strongest_counterargument"), "counterargument", 10000),
            "decision_changing_evidence": string(doc.get("decision_changing_evidence"), "decision-changing evidence", 10000)}


NUMBER_TOKEN = re.compile(r"(?<![\w.])[-+]?(?:[$€£])?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:%|[kKmMbB](?!\w))?")


def verify_material_assertions(cx, section, text, records):
    declared = section.get("assertions", [])
    require(isinstance(declared, list), "Material assertions must be an array")
    values = set()
    refs = {(row["id"], row["revision"]) for row in records}
    for assertion in declared:
        try:
            _key, unit, matches = validate_assertion(cx, assertion, refs)
        except (ValueError, TypeError, KeyError) as error:
            raise ValueError("Material requires exact pinned assertions") from error
        require(matches, "A material value disagrees with its pinned input")
        if assertion.get("numeric") is True:
            values.add((Decimal(str(assertion["value"])), unit))
    for match in NUMBER_TOKEN.finditer(text):
        raw = match.group()
        token = raw.translate(str.maketrans("", "", "$€£%,"))
        factor = {"k": 1000, "m": 1000000, "b": 1000000000}.get(token[-1:].lower(), 1)
        number = Decimal(token[:-1] if factor != 1 else token) * factor
        units = {"$": {"USD", "CAD", "AUD", "NZD"}, "€": {"EUR"}, "£": {"GBP"}, "%": {"%"}}
        expected = next((units[symbol] for symbol in units if symbol in raw), None)
        if expected is None:
            require(any(value == number for value, _ in values), "A material number is missing a traced assertion")
        else:
            require(any((number, unit) in values for unit in expected),
                    "A material number is missing a traced assertion with the displayed unit")


def material(workspace, doc, on, format_name):
    date_value(on, "material review date")
    require(isinstance(doc, dict) and format_name in {"md", "html"}, "Invalid material request")
    title = string(doc.get("title"), "material title", 150)
    category = doc.get("type")
    require(isinstance(category, str) and category in {"plan", "deck", "one_pager", "memo", "update", "appendix"}, "Unknown material type")
    audience = doc.get("audience", "restricted")
    require(isinstance(audience, str) and audience in AUDIENCES, "Unknown material audience")
    sections = doc.get("sections")
    require(isinstance(sections, list) and sections and len(sections) <= 40, "Provide material sections")
    if category == "update":
        require(isinstance(doc.get("risks"), list) and doc["risks"], "Investor updates must include material risks")
    with workspace.connect() as cx:
        cx.execute("BEGIN")
        content, links = review_material(cx, doc, on, category, audience, sections)
    revisions = {link["id"]: link["revision"] for link in links}
    if format_name == "md":
        lines = [f"# {literal_markdown(title)}", "", DRAFT_NOTICE, ""]
        for heading, text, ids in content:
            fence = "`" * (max((len(m.group()) for m in re.finditer(r"`+", text)), default=2) + 1)
            fence = max(fence, "```")
            lines.extend([f"## {literal_markdown(heading)}", "", fence, text, fence, "",
                          "Evidence IDs " + ", ".join(f"{rid}@{revisions[rid]}" for rid in ids), ""])
        rendered = "\n".join(lines)
    else:
        slides = []
        for heading, text, ids in content:
            labels = ", ".join(f"{rid}@{revisions[rid]}" for rid in ids)
            slides.append(f"<section><h2>{escape(heading)}</h2><p>{escape(text)}</p><small>{escape(labels)}</small></section>")
        rendered = ('<!doctype html><html lang="en"><meta charset="utf-8">'
                    f'<title>{escape(title)}</title><style>body{{font:18px system-ui;margin:2rem auto;'
                    'max-width:68rem;color:#153149;padding:0 1rem}section{padding:2rem 0;'
                    'border-top:1px solid #ccc;break-after:page}p{white-space:pre-wrap}small{overflow-wrap:anywhere}'
                    f'</style><h1>{escape(title)}</h1><p>{DRAFT_NOTICE}</p>{"".join(slides)}</html>')
    return rendered, links


DRAFT_NOTICE = "Review draft. Confirm narrative and figures against the pinned evidence before sharing."


def literal_markdown(value):
    return re.sub(r"[^\w\s]", lambda m: f"&#{ord(m.group())};", value).replace("\n", " ").replace("\r", " ")


def review_material(cx, doc, on, category, audience, sections):
    selected = {}
    audited = set()
    content = []
    for section in sections:
        require(isinstance(section, dict), "Invalid material section")
        heading = string(section.get("heading"), "section heading", 150)
        text = string(section.get("text"), "section text", 10000)
        ids = section.get("records")
        require(isinstance(ids, list) and ids and all(isinstance(rid, str) for rid in ids),
                "Every material section needs pinned inputs")
        records = []
        for rid in ids:
            record = Workspace.get_on(cx, rid)
            trace = Workspace.trace_on(cx, rid, on)["records"] if record else []
            require(trace and all(fits_audience(item, audience) for item in trace),
                    "Material uses evidence above the selected disclosure tier")
            require(record["status"] in {"reviewed", "approved"}, "Material inputs need review")
            selected[rid] = record
            audited.update(item["id"] for item in trace)
            records.append(record)
        verify_material_assertions(cx, section, heading + "\n" + text, records)
        content.append((heading, text, ids))
    verify_material_assertions(cx, {"assertions": doc.get("title_assertions", [])},
                               doc["title"], selected.values())
    if category == "update":
        risks = "\n".join(string(risk, "material risk") for risk in doc["risks"])
        verify_material_assertions(cx, {"assertions": doc.get("risk_assertions", [])},
                                   risks, selected.values())
        content.append(("Material risks", risks, sorted(selected)))
    result = audit_on(cx, on, audited)
    require(not result["blocking"], "Unresolved critical or high findings block material export")
    require(not any(f["severity"] == "MEDIUM" for f in result["findings"]),
            "Expired or stale research needs review before material export")
    return content, [ref(selected[rid]) for rid in sorted(selected)]


def dependency_plan(workspace, task):
    description = string(task, "requested workflow").casefold()
    needs = {}
    for key, kinds in {
        "fundraising": ("technical_milestone", "market", "competitor", "financial_model", "document", "investor", "fundraising_opportunity"),
        "outreach": ("contact", "investor", "fundraising_opportunity"),
        "pitch": ("market", "competitor", "financial_model"),
        "diligence": ("document", "technical_milestone", "financial_model"),
        "grant": ("funding_opportunity", "technical_milestone"),
        "finance": ("assumption", "financial_model"),
    }.items():
        if key in description:
            needs.update(dict.fromkeys(kinds))
    available = {r["kind"] for r in workspace.list()}
    workflows = {"market": "seed-market", "financial_model": "seed-model", "investor": "seed-investors",
                 "fundraising_opportunity": "seed-crm", "contact": "seed-investors", "competitor": "seed-scout",
                 "document": "seed-dataroom", "technical_milestone": "seed-readiness",
                 "funding_opportunity": "seed-grants", "assumption": "seed-model"}
    return {"recognized": bool(needs), "required": [
        {"kind": kind, "workflow": workflows[kind], "available": kind in available} for kind in needs]}
