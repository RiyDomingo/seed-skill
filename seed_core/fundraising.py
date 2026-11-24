"""Deterministic investor qualification, relationship mapping and fundraising state."""

from collections import deque
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from email.headerregistry import Address
from email.message import EmailMessage
from email.policy import SMTP
import re

from .schema import date_value, digest, require, string
from .transfer import write_new
from .workspace import Conflict, Workspace, identity

WEIGHTS = {"sector": 25, "stage": 20, "cheque": 15, "portfolio": 15,
           "recency": 10, "geography": 10, "introduction": 5}
NEXT = {
    "discovered": {"research_required", "qualified"},
    "research_required": {"qualified"},
    "qualified": {"priority_target", "introduction_requested", "outreach_drafted"},
    "priority_target": {"introduction_requested", "outreach_drafted"},
    "introduction_requested": {"outreach_drafted", "responded", "meeting_scheduled"},
    "outreach_drafted": {"outreach_approved"},
    "outreach_approved": {"contacted", "outreach_drafted"},
    "contacted": {"responded"},
    "responded": {"meeting_scheduled", "outreach_drafted"},
    "meeting_scheduled": {"meeting_completed", "responded"},
    "meeting_completed": {"due_diligence", "term_sheet"},
    "due_diligence": {"term_sheet"},
    "term_sheet": {"committed", "due_diligence"},
    "committed": {"closed"},
    "closed": set(), "passed": set(), "deferred": {"research_required", "qualified"},
    "opted_out": set(),
}
STOPPED = {"closed", "passed", "opted_out"}


def ref(record, role="dependency"):
    return {"id": record["id"], "revision": record["revision"], "role": role}


def proportion(value):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        number = Decimal("NaN")
    require(number.is_finite() and 0 <= number <= 1, "Ratings and confidence must be fractions from 0 to 1")
    return number


def qualification(workspace, investor_id, assessment, on):
    on = date_value(on, "qualification date").isoformat()
    investor = workspace.get(investor_id)
    require(investor and investor["kind"] == "investor", "Investor record is required")
    require(isinstance(assessment, dict), "Assessment must be an object")
    raw_weights = assessment.get("weights", WEIGHTS)
    require(isinstance(raw_weights, dict) and raw_weights.keys() == WEIGHTS.keys(), "Use all seven scoring weights")
    try:
        weights = {key: proportion(Decimal(str(value)) / 100) for key, value in raw_weights.items()}
    except InvalidOperation as error:
        raise ValueError("Invalid scoring weights") from error
    require(sum(weights.values()) == 1, "Scoring percentages must sum to 100")
    criteria = assessment.get("criteria", {})
    require(isinstance(criteria, dict) and criteria.keys() <= WEIGHTS.keys(), "Unknown scoring criterion")
    observed = Decimal(0)
    fit = Decimal(0)
    confidence = Decimal(0)
    breakdown = {}
    pins = [ref(investor)]
    for name, weight in weights.items():
        row = criteria.get(name)
        if row is None:
            breakdown[name] = {"rating": None, "confidence": 0.0, "known": False}
            continue
        require(isinstance(row, dict) and "rating" in row, "Each scored criterion needs a rating")
        rating = proportion(row["rating"])
        stated = proportion(row.get("confidence", 0))
        evidence = row.get("evidence", [])
        require(isinstance(evidence, list), "Criterion evidence must be an ID list")
        verified = any(evidence)
        for record_id in evidence:
            record = workspace.get(record_id)
            require(record and record["kind"] in {"evidence", "claim"}, "Invalid criterion evidence")
            audited = workspace.trace(record_id, on)
            if record["status"] not in {"reviewed", "approved"} or audited["findings"]:
                verified = False
            pins.append(ref(record, "evidence" if record["kind"] == "evidence" else "dependency"))
        rated_confidence = stated if verified else Decimal(0)
        observed += weight
        fit += weight * rating
        confidence += weight * rated_confidence
        breakdown[name] = {"rating": float(rating), "confidence": float(rated_confidence),
                           "known": True, "reviewed_evidence": verified}
    fit_score = float(round(100 * fit / observed, 2)) if observed else None
    evidence_score = float(round(100 * confidence, 2))
    return {"investor_id": investor_id, "fit_score": fit_score, "evidence_confidence": evidence_score,
            "coverage": float(round(100 * observed, 2)), "breakdown": breakdown, "checked_on": on,
            "priority_eligible": fit_score is not None and fit_score >= 75 and evidence_score >= 70,
            "links": list({(x["id"], x["revision"], x["role"]): x for x in pins}.values())}


def relationship_paths(workspace, start, destination, max_hops=3, on=None):
    on = on or datetime.now(timezone.utc).date().isoformat()
    date_value(on, 'review date')
    require(type(max_hops) is int and 1 <= max_hops <= 4, "Use one to four introduction hops")
    require(workspace.get(start) and workspace.get(destination) and start != destination,
            "Select distinct existing relationship endpoints")
    graph = {}
    for edge in workspace.list("relationship"):
        data = edge["data"]
        left, right = data.get("from_id"), data.get("to_id")
        if not isinstance(left, str) or not isinstance(right, str) or left == right:
            continue
        endpoint_ids = {link["id"] for link in edge["links"] if link["role"] == "dependency"}
        if {left, right} - endpoint_ids:
            continue
        verified = data.get("relationship_status") == "verified" and edge["status"] in {"reviewed", "approved"}
        verified = verified and any(link["role"] in {"evidence", "source"} for link in edge["links"])
        verified = verified and not workspace.trace(edge["id"], on)["findings"]
        graph.setdefault(left, []).append((right, edge, verified))
        if data.get("bidirectional") is True:
            graph.setdefault(right, []).append((left, edge, verified))
    queue = deque([(start, [start], [], True)])
    paths = []
    inspected = 0
    while queue and len(paths) < 50:
        node, nodes, edges, verified = queue.popleft()
        inspected += 1
        require(inspected <= 10_000, "Relationship graph search is too broad. Use fewer hops.")
        if node == destination:
            paths.append({"nodes": nodes, "relationships": edges, "status": "verified" if verified else "possible"})
        elif len(edges) < max_hops:
            for peer, edge, proof in sorted(graph.get(node, []), key=lambda row: (not row[2], row[0])):
                if peer not in nodes:
                    queue.append((peer, nodes + [peer], edges + [ref(edge)], verified and proof))
    return sorted(paths, key=lambda p: (p["status"] != "verified", len(p["relationships"]), p["nodes"]))


def get_kind(cx, record_id, kind):
    record = Workspace.get_on(cx, record_id)
    require(record is not None and record["kind"] == kind, f"Expected {kind} record")
    return record


def crm_open(workspace, investor_id, round_key, name, contact_id=None):
    round_key = string(round_key, "round key", 80)
    with workspace.connect() as cx:
        cx.execute("BEGIN IMMEDIATE")
        investor = get_kind(cx, investor_id, "investor")
        pins = [ref(investor)]
        if contact_id:
            contact = get_kind(cx, contact_id, "contact")
            require(contact["data"].get("investor_id") == investor_id, "Contact belongs to a different investor")
            pins.append(ref(contact))
        return workspace.put_on(cx, "fundraising_opportunity", f"{investor_id}:{round_key}",
                                {"name": name, "stage": "discovered", "investor_id": investor_id,
                                 "contact_id": contact_id}, classification="confidential",
                                provenance="founder", links=pins)


def crm_advance(workspace, opportunity_id, expected, stage, on, note, *, next_action=None, follow_up=None):
    date_value(on, "interaction date")
    if follow_up:
        require(date_value(follow_up, "follow-up") >= date_value(on, "interaction date"),
                "Follow-up cannot precede the recorded interaction")
    summary = string(note, "transition note")
    with workspace.connect() as cx:
        cx.execute("BEGIN IMMEDIATE")
        old = get_kind(cx, opportunity_id, "fundraising_opportunity")
        data = dict(old["data"])
        current = data["stage"]
        require(current in NEXT and stage in NEXT, "Unknown fundraising stage")
        require(stage in NEXT[current] or current not in STOPPED and stage in {"passed", "deferred", "opted_out"},
                "Invalid pipeline transition")
        if stage == "outreach_approved":
            approved = [r for r in Workspace.list_on(cx, "interaction")
                        if r["data"].get("opportunity_id") == opportunity_id and r["status"] == "approved"
                        and r["data"].get("action") == "manual_delivery"
                        and r["data"].get("approval_on") == on]
            require(approved, "No exact current-day outreach approval is recorded")
            approved_draft(cx, approved[-1])
            check_outreach_context(cx, approved[-1], on)
            require(not suppressed(cx, approved[-1]["data"]["payload"]["to"]), "Contact is suppressed")
        if stage == "contacted":
            require(any(r["data"].get("opportunity_id") == opportunity_id
                        and r["data"].get("action") == "delivery_recorded"
                        for r in Workspace.list_on(cx, "interaction")),
                    "Contacted requires a founder-confirmed delivery record")
        if stage == "opted_out" and data.get("contact_id"):
            contact = get_kind(cx, data["contact_id"], "contact")
            suppress_on(cx, contact["data"].get("email"), on, "opted_out")
        data.update(stage=stage, next_action=next_action, follow_up=follow_up)
        record = workspace.put_on(cx, "fundraising_opportunity", old["key"], data, expected=expected,
                                  classification="confidential", provenance="founder", links=old["links"])
        workspace.put_on(cx, "interaction", f"stage:{opportunity_id}:{record['revision']}",
                         {"summary": summary, "occurred_on": on, "stage": stage, "opportunity_id": opportunity_id},
                         classification="confidential", provenance="founder", links=[ref(record)])
        return record


def pipeline(workspace, on):
    today = date_value(on, "pipeline date")
    with workspace.connect() as cx:
        cx.execute("BEGIN")
        rows = workspace.list_on(cx, "fundraising_opportunity")
        counts = {stage: 0 for stage in NEXT}
        due = []
        for row in rows:
            data = row["data"]
            stage = data["stage"]
            require(stage in NEXT, "Unknown fundraising stage in workspace")
            counts[stage] += 1
            contact = Workspace.get_on(cx, data["contact_id"]) if data.get("contact_id") else None
            email = contact["data"].get("email") if contact else None
            if email and suppressed(cx, email):
                continue
            if data.get("follow_up") and stage not in STOPPED and date_value(data["follow_up"], "follow up") <= today:
                due.append(row)
        return {"counts": counts, "due": due, "total": len(rows)}


def address(value):
    candidate = string(value, "business email address", 254)
    require(re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", candidate)
            and ".." not in candidate, "Invalid business email address")
    return candidate.casefold()


def suppressed(cx, email):
    key = "suppression:" + digest(address(email))
    vid = Workspace.meta_on(cx)["venture_id"]
    return Workspace.get_on(cx, identity(vid, "interaction", key))


def suppress_on(cx, email, on, reason):
    date_value(on, "suppression date")
    require(reason in {"opted_out", "bounce"}, "Unknown suppression reason")
    key = "suppression:" + digest(address(email))
    found = suppressed(cx, email)
    if found:
        return found
    return Workspace.put_on(cx, "interaction", key, {"summary": "Permanent outreach suppression",
                            "occurred_on": on, "reason": reason}, classification="restricted",
                            provenance="founder")


def suppress(workspace, email, on, reason):
    with workspace.connect() as cx:
        cx.execute("BEGIN IMMEDIATE")
        return suppress_on(cx, email, on, reason)


def draft(workspace, opportunity_id, message, on):
    date_value(on, "draft date")
    require(isinstance(message, dict) and set(message) == {"subject", "body", "sender", "verified_fact_ids"},
            "Draft needs sender, subject, body and verified fact IDs")
    subject = string(message["subject"], "subject", 160)
    require("\n" not in subject and "\r" not in subject, "Subject cannot contain line breaks")
    body = string(message["body"], "body", 12000)
    require("opt out" in body.casefold() or "unsubscribe" in body.casefold(),
            "Include a plain opt-out instruction")
    sender = address(message["sender"])
    facts = message["verified_fact_ids"]
    require(isinstance(facts, list) and bool(facts), "Pin verified facts for personalization")
    with workspace.connect() as cx:
        cx.execute("BEGIN IMMEDIATE")
        opportunity = get_kind(cx, opportunity_id, "fundraising_opportunity")
        require(opportunity["data"]["stage"] in {"qualified", "priority_target", "introduction_requested",
                                                "outreach_drafted", "responded"}, "Opportunity must be eligible")
        contact = get_kind(cx, opportunity["data"].get("contact_id"), "contact")
        require(contact["data"].get("public_business") is True and contact["status"] in {"reviewed", "approved"}
                and any(link["role"] in {"source", "evidence"} for link in contact["links"]),
                "Use a reviewed public business address")
        to = address(contact["data"].get("email"))
        require(not suppressed(cx, to), "Contact is suppressed")
        require(not Workspace.trace_on(cx, contact["id"], on)["findings"],
                "Business contact evidence is stale or disputed")
        pins = [ref(opportunity), ref(contact)]
        for claim_id in dict.fromkeys(facts):
            claim = get_kind(cx, claim_id, "claim")
            require(claim["status"] in {"reviewed", "approved"} and claim["provenance"] == "verified_external",
                    "Outreach personalization must use reviewed verified claims")
            require(not Workspace.trace_on(cx, claim_id, on)["findings"], "Personalization evidence is stale or disputed")
            pins.append(ref(claim))
        payload = {"to": to, "sender": sender, "subject": subject, "body": body, "purpose": "manual_delivery"}
        checksum = digest(payload)
        key = "outreach:" + digest({"opportunity": opportunity_id, "payload": checksum})
        require(not any(r["data"].get("payload_sha256") == checksum
                        for r in Workspace.list_on(cx, "interaction")), "Duplicate outreach draft")
        return Workspace.put_on(cx, "interaction", key, {"summary": "Drafted outreach", "occurred_on": on,
                                "opportunity_id": opportunity_id, "payload": payload, "payload_sha256": checksum,
                                "action": "manual_delivery"}, classification="restricted",
                                provenance="founder", links=pins)


def check_outreach_context(cx, record, on):
    opportunity = get_kind(cx, record["data"]["opportunity_id"], "fundraising_opportunity")
    require(opportunity["data"]["stage"] in {"qualified", "priority_target", "introduction_requested",
                                            "outreach_drafted", "outreach_approved", "responded"},
            "Opportunity is no longer eligible for outreach")
    data = record["data"]
    payload = data.get("payload")
    require(record["key"].startswith("outreach:") and record["classification"] == "restricted"
            and record["provenance"] == "founder" and data.get("action") == "manual_delivery"
            and isinstance(payload, dict) and set(payload) == {"to", "sender", "subject", "body", "purpose"}
            and payload["purpose"] == "manual_delivery", "Invalid outreach draft")
    subject, body = string(payload["subject"], "subject", 160), string(payload["body"], "body", 12000)
    require("\n" not in subject and "\r" not in subject
            and ("opt out" in body.casefold() or "unsubscribe" in body.casefold()),
            "Outreach requires a single-line subject and opt-out instructions")
    address(payload["sender"])
    contact = get_kind(cx, opportunity["data"].get("contact_id"), "contact")
    require(address(contact["data"].get("email")) == payload["to"], "Outreach recipient changed")
    require(contact["data"].get("public_business") is True and contact["status"] in {"reviewed", "approved"}
            and any(link["role"] in {"source", "evidence"} for link in contact["links"]),
            "Use a reviewed public business address")
    pins = {(link["id"], link["role"]) for link in record["links"]}
    required = {(opportunity["id"], "dependency"), (contact["id"], "dependency")}
    require(required <= pins and pins - required, "Outreach lacks pinned recipient or verified facts")
    for link in record["links"]:
        if link["id"] != opportunity["id"]:
            latest = Workspace.get_on(cx, link["id"])
            require(latest["revision"] == link["revision"], "A pinned outreach input has changed")
            if latest["id"] != contact["id"]:
                require(latest["kind"] == "claim" and latest["status"] in {"reviewed", "approved"}
                        and latest["provenance"] == "verified_external", "Unverified personalization")
            require(not Workspace.trace_on(cx, latest["id"], on)["findings"],
                    "Outreach evidence is stale or disputed")


def approved_draft(cx, row):
    data = row["data"]
    require(row["status"] == "approved" and row["revision"] == 2
            and data.get("action") == "manual_delivery", "An exact current-day approval is required")
    previous = Workspace.get_on(cx, row["id"], 1)
    require(previous and previous["status"] == "draft" and previous["links"] == row["links"]
            and previous["data"] == {key: value for key, value in data.items()
                                     if key not in {"approval_on", "approver"}}
            and isinstance(data.get("approver"), str) and data["approver"].strip(),
            "Approval must apply to the original draft")


def approve(workspace, draft_id, digest_confirmation, approver, on, daily_cap=10):
    date_value(on, "approval date")
    approver = string(approver, "approver", 150)
    require(type(daily_cap) is int and 1 <= daily_cap <= 20, "Daily approval limit must be from one to twenty")
    with workspace.connect() as cx:
        cx.execute("BEGIN IMMEDIATE")
        row = get_kind(cx, draft_id, "interaction")
        data = row["data"]
        require(row["status"] == "draft" and data.get("action") == "manual_delivery", "No draft to approve")
        require(data["payload_sha256"] == digest_confirmation == digest(data["payload"]),
                "Approval does not match the draft")
        require(not suppressed(cx, data["payload"]["to"]), "Contact is suppressed")
        require(on >= data["occurred_on"], "Approval precedes drafting")
        check_outreach_context(cx, row, on)
        reviewed = [r for r in Workspace.list_on(cx, "interaction") if r["status"] == "approved"
                    and r["data"].get("approval_on") == on and r["data"].get("action") == "manual_delivery"]
        require(len(reviewed) < daily_cap, "Daily approval cap reached")
        return Workspace.put_on(cx, "interaction", row["key"], {**data, "approval_on": on, "approver": approver},
                                classification="restricted", provenance="founder", status="approved",
                                expected=row["revision"], links=row["links"])


def export_eml(workspace, draft_id, confirmation, path, on):
    date_value(on, "handoff date")
    with workspace.connect() as cx:
        cx.execute("BEGIN IMMEDIATE")
        record = get_kind(cx, draft_id, "interaction")
        data = record["data"]
        approved_draft(cx, record)
        require(data.get("approval_on") == on, "An exact current-day approval is required")
        venture_id = Workspace.meta_on(cx)["venture_id"]
        require(not Workspace.get_on(cx, identity(venture_id, "interaction", "delivery:" + draft_id)),
                "Outreach delivery is already recorded")
        payload = data["payload"]
        require(confirmation == data["payload_sha256"] == digest(payload), "Wrong approved payload")
        require(not suppressed(cx, payload["to"]), "Contact is suppressed")
        check_outreach_context(cx, record, on)
        msg = EmailMessage(policy=SMTP)
        msg["To"] = Address(addr_spec=payload["to"])
        msg["From"] = Address(addr_spec=payload["sender"])
        msg["Subject"] = payload["subject"]
        msg.set_content(payload["body"])
        return write_new(path, msg.as_bytes())


def record_delivery(workspace, draft_id, confirmation, on, receipt):
    date_value(on, "delivery date")
    receipt = string(receipt, "founder-confirmed delivery reference", 300)
    with workspace.connect() as cx:
        cx.execute("BEGIN IMMEDIATE")
        parent = get_kind(cx, draft_id, "interaction")
        data = parent["data"]
        approved_draft(cx, parent)
        require(data["approval_on"] <= on, "Record delivery of an approved payload")
        require(confirmation == data["payload_sha256"] == digest(data["payload"]), "Wrong approved payload")
        return Workspace.put_on(cx, "interaction", "delivery:" + draft_id,
                                {"summary": "Founder confirmed external delivery", "occurred_on": on,
                                 "action": "delivery_recorded", "opportunity_id": data["opportunity_id"],
                                 "receipt": receipt}, classification="restricted", provenance="founder",
                                links=[ref(parent)])


def meeting_brief(workspace, opportunity_id, on):
    opportunity = workspace.get(opportunity_id)
    require(opportunity and opportunity["kind"] == "fundraising_opportunity", "Opportunity is missing")
    investor = workspace.get(opportunity["data"]["investor_id"])
    require(investor is not None, "Investor profile is missing")
    evidence = workspace.trace(investor["id"], on)
    return {"investor": investor, "opportunity": opportunity, "evidence_findings": evidence["findings"],
            "questions_to_confirm": [key for key in ("mandate", "stage", "cheque", "recent_investments")
                                     if not investor["data"].get(key)],
            "venture_evidence": [ref(r) for r in workspace.list()
                                 if r["kind"] in {"market", "financial_model", "technical_milestone"}
                                 and r["status"] in {"reviewed", "approved"}]}
