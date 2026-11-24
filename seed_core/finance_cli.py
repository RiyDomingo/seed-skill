"""CLI bindings for forecasts, capital strategy and instrument calculations."""

from pathlib import Path

from . import dilution, finance
from .fundraising import ref
from .model_export import csv_bytes, xlsx_bytes
from .schema import canonical, require
from .transfer import read_file, write_new


def register(commands):
    group = commands.add_parser("finance", help="deterministic financial models, capital and dilution")
    actions = group.add_subparsers(dest="action", required=True)

    def action(name):
        return actions.add_parser(name)

    run = action("forecast")
    run.add_argument("file", type=Path)
    run.add_argument("--save-key")
    run.add_argument("--assumption-id")
    run.add_argument("--expected", type=int)
    for name in ("capital", "round", "waterfall", "ownership"):
        action(name).add_argument("file", type=Path)
    vary = action("sensitivity")
    vary.add_argument("file", type=Path)
    vary.add_argument("factor", choices=finance.MULTIPLIERS)
    vary.add_argument("values", type=Path)
    sheet = action("spreadsheet")
    sheet.add_argument("model_id")
    sheet.add_argument("scenario", choices=("base", "downside", "upside"))
    sheet.add_argument("output", type=Path)


def execute(ws, args):
    if args.action == "spreadsheet":
        model = ws.get(args.model_id)
        require(model and model["kind"] == "financial_model" and "forecast" in model["data"], "Saved model is missing")
        case = model["data"]["forecast"]["scenarios"].get(args.scenario)
        require(case is not None, "Scenario is missing from the model")
        suffix = args.output.suffix.lower()
        require(suffix in {".csv", ".xlsx"}, "Output must be .csv or .xlsx")
        output = (csv_bytes if suffix == ".csv" else xlsx_bytes)(case)
        return {"file": str(write_new(args.output, output)), "model": ref(model)}
    doc = read_file(args.file)
    if args.action == "forecast":
        result = finance.forecast(doc)
        if not args.save_key:
            return result
        require(bool(args.assumption_id), "Pin the stored input assumption before saving")
        assumption = ws.get(args.assumption_id)
        require(assumption and assumption["kind"] == "assumption"
                and canonical(assumption["data"]["value"]) == canonical(doc),
                "Selected assumption does not match the forecast input")
        require(doc["currency"] == ws.metadata()["config"]["currency"], "Model and venture currency differ")
        return ws.put("financial_model", args.save_key,
                      {"name": doc["name"], "currency": doc["currency"], "forecast": result},
                      expected=args.expected, classification=assumption["classification"], provenance="calculated",
                      links=[ref(assumption, "assumption")])
    if args.action == "sensitivity":
        return finance.sensitivity(doc, args.factor, read_file(args.values))
    return {"capital": finance.capital_plan, "round": dilution.priced_round,
            "waterfall": dilution.liquidation, "ownership": dilution.ownership_adjustments}[args.action](doc)
