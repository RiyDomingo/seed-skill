"""CLI bindings for evidence-backed fundraising operations."""

from pathlib import Path

from . import fundraising as f
from .transfer import read_file


def register(commands):
    group = commands.add_parser("fundraising", help="investor qualification, CRM, network and local outreach")
    actions = group.add_subparsers(dest="action", required=True)

    def action(name, *args):
        parser = actions.add_parser(name)
        for arg in args:
            parser.add_argument(arg, type=Path if arg in {"file", "output"} else str)
        return parser

    action("qualify", "investor_id", "file", "on")
    paths = action("paths", "start", "destination")
    paths.add_argument("--max-hops", type=int, default=3)
    opening = action("open", "investor_id", "round_key", "name")
    opening.add_argument("--contact")
    advance = action("advance", "opportunity_id", "stage", "on", "note")
    advance.add_argument("--expected", type=int, required=True)
    advance.add_argument("--next-action")
    advance.add_argument("--follow-up")
    action("pipeline", "on")
    suppression = action("suppress", "email", "on")
    suppression.add_argument("reason", choices=("opted_out", "bounce"))
    action("draft", "opportunity_id", "file", "on")
    approval = action("approve", "draft_id", "confirmation", "approver", "on")
    approval.add_argument("--daily-cap", type=int, default=10)
    action("eml", "draft_id", "confirmation", "output", "on")
    action("meeting-brief", "opportunity_id", "on")


def execute(ws, args):
    match args.action:
        case "qualify":
            return f.qualification(ws, args.investor_id, read_file(args.file), args.on)
        case "paths":
            return f.relationship_paths(ws, args.start, args.destination, args.max_hops)
        case "open":
            return f.crm_open(ws, args.investor_id, args.round_key, args.name, args.contact)
        case "advance":
            return f.crm_advance(ws, args.opportunity_id, args.expected, args.stage, args.on,
                                 args.note, next_action=args.next_action, follow_up=args.follow_up)
        case "pipeline":
            return f.pipeline(ws, args.on)
        case "suppress":
            return f.suppress(ws, args.email, args.on, args.reason)
        case "draft":
            return f.draft(ws, args.opportunity_id, read_file(args.file), args.on)
        case "approve":
            return f.approve(ws, args.draft_id, args.confirmation, args.approver, args.on, args.daily_cap)
        case "eml":
            return {"file": str(f.export_eml(ws, args.draft_id, args.confirmation, args.output, args.on))}
        case "meeting-brief":
            return f.meeting_brief(ws, args.opportunity_id, args.on)
