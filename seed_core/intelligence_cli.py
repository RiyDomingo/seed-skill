"""CLI bindings for shared, sourced intelligence workflows."""

from pathlib import Path

from . import intelligence as research
from .fundraising import ref
from .schema import canonical, require
from .transfer import read_file


def register(commands):
    category = commands.add_parser("research", help="market, competition, patents and funding intelligence")
    actions = category.add_subparsers(required=True, dest="action")
    ingest = actions.add_parser("ingest")
    ingest.add_argument("file", type=Path)
    ingest.add_argument("--classification", default="internal")
    actions.add_parser("competitors").add_argument("on")
    for name in ("grants", "accelerators"):
        screen = actions.add_parser(name)
        screen.add_argument("on")
        screen.add_argument("file", type=Path)
    patents = actions.add_parser("patents")
    patents.add_argument("on")
    patents.add_argument("--query")
    market = actions.add_parser("market")
    market.add_argument("file", type=Path)
    market.add_argument("--save-key")
    market.add_argument("--assumption-id")
    market.add_argument("--expected", type=int)


def execute(ws, args):
    match args.action:
        case "ingest":
            return research.ingest(ws, read_file(args.file), args.classification)
        case "competitors":
            return research.compare_competitors(ws, args.on)
        case "grants" | "accelerators":
            programme = "grant" if args.action == "grants" else "accelerator"
            return research.opportunities(ws, args.on, programme, read_file(args.file))
        case "patents":
            return research.patent_landscape(ws, args.on, args.query)
        case "market":
            doc = read_file(args.file)
            result = research.market_size(doc)
            if not args.save_key:
                return result
            require(args.assumption_id, "Saving requires a pinned input assumption")
            a = ws.get(args.assumption_id)
            require(a and a["kind"] == "assumption" and canonical(a["data"]["value"]) == canonical(doc),
                    "Market assumptions do not match the supplied input")
            require(result["currency"] == ws.metadata()["config"]["currency"], "Market and venture currency differ")
            return ws.put("market", args.save_key, {"name": args.save_key, **result}, expected=args.expected,
                          classification=a["classification"], provenance="calculated",
                          links=[ref(a, "assumption")])
