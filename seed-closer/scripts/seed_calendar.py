#!/usr/bin/env python3
"""Preview and export an approved CRM calendar invitation without sending it."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import re
import sys

SKILL = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(SKILL), str(SKILL.parent)]

from closer import build_ics
from seed_core.fundraising import address, get_kind, ref, suppressed
from seed_core.schema import canonical, date_value, digest, require, string
from seed_core.transfer import read_file, write_new
from seed_core.workspace import Workspace


def instant(value):
    value = string(value, "meeting time", 40)
    require(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?(Z|[+-]\d{2}:\d{2})", value),
            "Meeting time needs an exact ISO 8601 offset")
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def calendar_plan(cx, opportunity_id, event, on):
    day = date_value(on, "review date")
    require(isinstance(event, dict) and set(event) == {"organizer", "start", "end", "title", "description", "location"},
            "Supply organizer, start, end, title, description and location")
    opportunity = get_kind(cx, opportunity_id, "fundraising_opportunity")
    require(opportunity["data"]["stage"] in {"responded", "meeting_scheduled"},
            "Record the investor's response before preparing a calendar invitation")
    contact = get_kind(cx, opportunity["data"].get("contact_id"), "contact")
    require(contact["status"] in {"reviewed", "approved"} and contact["data"].get("public_business") is True
            and any(link["role"] in {"source", "evidence"} for link in contact["links"])
            and not Workspace.trace_on(cx, contact["id"], on)["findings"],
            "Meeting recipient needs a current reviewed business contact")
    to, organizer = address(contact["data"].get("email")), address(event["organizer"])
    require(organizer != to and not suppressed(cx, to), "Meeting recipient is suppressed or invalid")
    start, end = instant(event["start"]), instant(event["end"])
    seconds = (end - start).total_seconds()
    require(datetime.fromisoformat(event["start"]).date() >= day and 600 <= seconds <= 14400,
            "Use a future meeting of ten to 240 minutes")
    payload = {"opportunity": ref(opportunity), "contact": ref(contact), "to": to, "organizer": organizer,
               "start_utc": start.isoformat(), "end_utc": end.isoformat(), "start": event["start"],
               "end": event["end"]}
    for field in ("title", "description", "location"):
        payload[field] = string(event[field], field, 1000)
        require(not any(ord(char) < 32 and char != "\n" for char in payload[field]),
                "Calendar fields cannot contain control characters")
    return payload


def execute(args):
    ws = Workspace(args.workspace)
    event = read_file(args.event)
    with ws.connect() as cx:
        cx.execute("BEGIN IMMEDIATE" if args.action == "export" else "BEGIN")
        payload = calendar_plan(cx, args.opportunity, event, args.on)
        checksum = digest(payload)
        if args.action == "preview":
            return {"payload": payload, "sha256": checksum, "action": "local_invitation_export"}
        require(args.confirm == checksum, "Approval does not match the meeting payload")
        approver = string(args.approver, "approver", 150)
        require(args.output.suffix.lower() == ".ics", "Meeting output must be .ics")
        start = datetime.fromisoformat(payload["start_utc"])
        end = datetime.fromisoformat(payload["end_utc"])
        stamp = datetime.combine(date_value(args.on, "review date"), datetime.min.time(), timezone.utc)
        uid = f"seed-{checksum[:32]}@{payload['organizer'].rsplit('@', 1)[1]}"
        body = build_ics(uid, 0, stamp, start, end, payload["title"], payload["description"],
                         payload["location"], None, (payload["organizer"], payload["organizer"]),
                         (payload["to"], payload["to"]), "UTC").encode("utf-8")
        record = Workspace.put_on(cx, "interaction", "calendar:" + checksum, {
            "summary": "Approved local calendar export", "occurred_on": args.on,
            "action": "calendar_prepared", "approver": approver, "payload_sha256": checksum,
        }, classification="restricted", provenance="founder", status="approved",
           links=[payload["opportunity"], payload["contact"]])
        output = write_new(args.output, body)
        return {"file": str(output), "sha256": checksum, "record": ref(record), "delivery": "unconfirmed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    actions = parser.add_subparsers(required=True, dest="action")
    for action in ("preview", "export"):
        command = actions.add_parser(action)
        command.add_argument("opportunity")
        command.add_argument("event", type=Path)
        command.add_argument("on")
        if action == "export":
            command.add_argument("output", type=Path)
            command.add_argument("--confirm", required=True)
            command.add_argument("--approver", required=True)
    args = parser.parse_args()
    try:
        print(canonical(execute(args)).decode())
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f"{error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
