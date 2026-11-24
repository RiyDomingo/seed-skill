"""CLI bindings for local audits, diligence and evidence-backed materials."""

from pathlib import Path

from . import diligence
from .schema import require
from .transfer import read_file, write_new


def register(commands):
    category = commands.add_parser("readiness", help="investment readiness, audit, committee and materials")
    actions = category.add_subparsers(required=True, dest="action")
    verify = actions.add_parser("audit")
    verify.add_argument("on")
    verify.add_argument("--id", action="append")
    for name in ("assess", "committee", "materials"):
        command = actions.add_parser(name)
        command.add_argument("file", type=Path)
        command.add_argument("on")
        if name == "materials":
            command.add_argument("output", type=Path)
    room = actions.add_parser("dataroom")
    room.add_argument("audience", choices=diligence.AUDIENCES)
    room.add_argument("on")
    actions.add_parser("plan-workflow").add_argument("request")


def execute(ws, args):
    match args.action:
        case "audit":
            return diligence.audit(ws, args.on, args.id)
        case "assess":
            return diligence.readiness(ws, read_file(args.file), args.on)
        case "committee":
            return diligence.committee(ws, read_file(args.file), args.on)
        case "dataroom":
            return diligence.dataroom(ws, args.audience, args.on)
        case "materials":
            suffix = args.output.suffix.lower()
            require(suffix in {".html", ".md"}, "Material output must be HTML or Markdown")
            text, links = diligence.material(ws, read_file(args.file), args.on, suffix[1:])
            return {"file": str(write_new(args.output, text.encode("utf-8"))), "links": links}
        case "plan-workflow":
            return diligence.dependency_plan(ws, args.request)
