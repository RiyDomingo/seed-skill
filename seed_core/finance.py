"""Deterministic monthly venture forecasts and milestone capital scenarios."""

from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

from .schema import require, string

D = Decimal
ZERO = D(0)
ONE = D(1)
MODELS = {"saas", "marketplace", "physical_products", "hardware", "manufacturing",
          "biotechnology", "medical_technology", "licensing", "services", "hybrid"}
STREAMS = {"recurring", "transaction", "manufacturing", "licensing", "service"}
DEBT = {"debt", "note", "equipment"}
FINANCING = {"equity", "safe", "note", "grant", "research_contract", "licensing", "debt", "equipment"}
TIMED_COSTS = {"opex", "rd", "capex", "interest", "principal", "depreciation"}
MULTIPLIERS = ("volume", "price", "unit_cost", "fixed_cost")
RANGES = {
    "growth": (-1, 2), "new_growth": (-1, 2), "utilisation": (0, 1),
    "yield": (0, 1), "churn": (0, 1), "take_rate": (0, 1), "tax_rate": (0, 1),
    "volume": (0, 100), "price": (0, 100), "unit_cost": (0, 100), "fixed_cost": (0, 100),
}
FIELDS = ["month", "period", "revenue", "cost_of_goods", "gross_profit", "gross_margin_pct",
          "operating_expense", "research_and_development", "depreciation", "interest", "tax",
          "net_income", "accounts_receivable", "accounts_payable", "inventory",
          "net_working_capital", "working_capital_change", "cash_from_operations", "capital_expenditure",
          "principal_repayment", "financing", "opening_cash", "cash_movement", "closing_cash",
          "opening_debt", "debt_financing", "closing_debt"]


def number(value, label, *, minimum=0, maximum=10**15):
    try:
        parsed = D(str(value))
    except InvalidOperation:
        parsed = D("NaN")
    require(parsed.is_finite() and minimum <= parsed <= maximum, f"Invalid {label}")
    return parsed


def money(value, quantum):
    require(value.is_finite() and abs(value) < D("1e24"), "Forecast exceeds supported numeric range")
    return value.quantize(quantum, rounding=ROUND_HALF_UP)


def scenario_settings(raw):
    require(isinstance(raw, dict), "Scenario settings must be an object")
    require(raw.keys() <= {*MULTIPLIERS, "financing_delay_months"}, "Unknown scenario setting")
    settings = {key: number(raw.get(key, 1), key, minimum=RANGES[key][0],
                            maximum=RANGES[key][1]) for key in MULTIPLIERS}
    delay = raw.get("financing_delay_months", 0)
    require(type(delay) is int and 0 <= delay <= 60, "Invalid financing delay")
    return settings, delay


def month_key(start, offset):
    index = (start.year * 12 + start.month - 1) + offset
    year, month = divmod(index, 12)
    return date(year, month + 1, 1)


def terms_for_plan(doc):
    require(isinstance(doc, dict), "Forecast input must be an object")
    name = string(doc.get("name"), "venture name")
    archetype = doc.get("archetype")
    require(archetype in MODELS, "Unknown business model archetype")
    currency = doc.get("currency")
    require(isinstance(currency, str) and re.fullmatch(r"[A-Z]{3}", currency), "Invalid forecast currency")
    precision = doc.get("minor_digits", 2)
    require(type(precision) is int and 0 <= precision <= 3, "Invalid currency minor digits")
    quantum = ONE.scaleb(-precision)
    require(type(doc.get("months")) is int and doc["months"] in (36, 60), "Forecast must contain 36 or 60 months")
    raw_start = doc.get("start")
    require(isinstance(raw_start, str) and re.fullmatch(r"[0-9]{4}-[0-9]{2}", raw_start), "Start must be YYYY-MM")
    try:
        start = date.fromisoformat(raw_start + "-01")
    except ValueError:
        require(False, "Invalid forecast start month")
    require(2000 <= start.year <= 9900, "Forecast start year outside supported range")
    return name, archetype, currency, quantum, start


def stream_settings(row):
    require(isinstance(row, dict) and row.get("kind") in STREAMS, "Unknown revenue stream")
    name = string(row.get("id"), "stream ID", 80)
    kind = row["kind"]
    data = {"id": name, "kind": kind}
    required = {"price"}
    if kind != "recurring":
        required.add("volume")
    if kind == "manufacturing":
        required.update({"capacity", "yield", "material_cost"})
    require(required <= row.keys(), "Revenue stream is missing required inputs")
    for key in ("price", "volume", "unit_cost", "capacity", "material_cost", "labour_cost",
                "rework_cost", "logistics_cost", "warranty_cost", "opening_inventory",
                "opening_inventory_value", "inventory_months", "opening_customers", "monthly_new",
                "growth", "new_growth", "utilisation", "yield", "churn", "take_rate"):
        low, high = ({"growth": (-1, 2), "new_growth": (-1, 2), "utilisation": (0, 1),
                      "yield": (0, 1), "churn": (0, 1), "take_rate": (0, 1),
                      "inventory_months": (0, 12)}.get(key, (0, 10**12)))
        default = 1 if key in {"utilisation", "yield", "take_rate"} else 0
        data[key] = number(row.get(key, default), key, minimum=low, maximum=high)
    if kind == "manufacturing":
        require(data["yield"] > 0 and data["capacity"] > 0, "Manufacturing needs positive yield and capacity")
        require(data["opening_inventory"] > 0 or data["opening_inventory_value"] == 0,
                "Opening inventory value needs opening units")
    else:
        require(data["opening_inventory"] == 0 and data["opening_inventory_value"] == 0,
                "Only manufacturing streams support opening inventory")
    return data


def schedules(doc, horizon):
    def month(value):
        require(type(value) is int and 1 <= value <= horizon, "Schedule month is outside the forecast")
        return value

    milestones = doc.get("milestones", {})
    require(isinstance(milestones, dict), "Milestones must map IDs to a projected month or null")
    for key, value in milestones.items():
        string(key, "milestone ID")
        if value is not None:
            month(value)
    hires = []
    costs = []
    funds = []
    for key in ("hires", "one_offs", "financing"):
        require(isinstance(doc.get(key, []), list), f"{key} must be a list")
    for hire in doc.get("hires", []):
        require(isinstance(hire, dict), "Invalid hire")
        hires.append((month(hire.get("month")), number(hire.get("monthly_cost"), "hire monthly cost")))
    for item in doc.get("one_offs", []):
        require(isinstance(item, dict) and item.get("kind") in TIMED_COSTS, "Unknown scheduled cost")
        debt_id = item.get("financing_id")
        require(debt_id is None or item["kind"] in {"principal", "interest"},
                "Only debt service can pin financing")
        costs.append((month(item.get("month")), item["kind"], number(item.get("amount"), "scheduled cost"), debt_id))
    known_funds = {}
    for item in doc.get("financing", []):
        require(isinstance(item, dict) and item.get("kind") in FINANCING, "Unknown financing instrument")
        start = month(item.get("month"))
        amount = number(item.get("amount"), "financing amount")
        conditions = item.get("requires", [])
        require(isinstance(conditions, list) and all(isinstance(key, str) and key in milestones
                for key in conditions), "Financing references an unknown milestone")
        eligible = None if any(milestones[key] is None for key in conditions) else max(
            [start] + [milestones[key] for key in conditions])
        fid = item.get("id")
        if fid is not None:
            string(fid, "financing ID", 100)
            require(fid not in known_funds, "Duplicate financing ID")
            known_funds[fid] = (item["kind"], eligible)
        funds.append({"id": fid, "kind": item["kind"], "requested_month": start, "eligible_month": eligible,
                      "amount": amount, "requires": conditions})
    for month_num, _kind, _amount, fid in costs:
        if fid is not None:
            require(isinstance(fid, str) and fid in known_funds and known_funds[fid][0] in DEBT,
                    "Debt service references unknown or non-debt financing")
            allowed_month = known_funds[fid][1]
            require(allowed_month is None or month_num >= allowed_month, "Debt service precedes disbursement")
    return hires, costs, funds


def run_stream(spec, state, month, factors, quantum):
    kind = spec["kind"]
    price = spec["price"] * factors["price"]
    unit_cost = spec["unit_cost"] * factors["unit_cost"]
    demand = spec["volume"] * (ONE if month == 1 else (1 + spec["growth"]) ** (month - 1)) * factors["volume"]
    spent = inventory = ZERO
    physical = {}
    if kind == "recurring":
        customers = state["customers"] * (1 - spec["churn"])
        customers += spec["monthly_new"] * (ONE if month == 1 else (1 + spec["new_growth"]) ** (month - 1)) * factors["volume"]
        state["customers"] = customers
        sold = customers
        cogs = spent = sold * unit_cost
    elif kind == "manufacturing":
        old_units, old_value = state["units"], state["value"]
        requested = max(ZERO, demand * (1 + spec["inventory_months"]) - old_units)
        attempts = min(spec["capacity"] * spec["utilisation"], requested / spec["yield"])
        made = attempts * spec["yield"]
        unit_factory_cost = spec["material_cost"] + spec["labour_cost"]
        production = (attempts * unit_factory_cost + (attempts - made) * spec["rework_cost"]) * factors["unit_cost"]
        available = old_units + made
        sold = min(demand, available)
        production = money(production, quantum)
        manufacturing_cogs = (old_value + production) * sold / available if available else ZERO
        inventory = money(old_value + production - manufacturing_cogs, quantum)
        # Recognize the exact accrual change that reconciles to the rounded inventory.
        manufacturing_cogs = old_value + production - inventory
        variable = money(sold * (unit_cost + (spec["logistics_cost"] + spec["warranty_cost"]) * factors["unit_cost"]), quantum)
        cogs = manufacturing_cogs + variable
        spent = production + variable
        state.update(units=available - sold, value=inventory)
        physical = {"demand_units": str(demand), "attempted_units": str(attempts),
                    "good_units": str(made), "scrap_units": str(attempts - made),
                    "closing_inventory_units": str(available - sold), "unfilled_units": str(demand - sold)}
    else:
        sold = demand
        cogs = spent = sold * unit_cost
    require(abs(sold) < D("1e20"), "Forecast exceeds supported unit range")
    revenue = sold * price * spec["take_rate"]
    return {"id": spec["id"], "units_sold": str(sold.quantize(D("0.000001"))),
            "revenue": money(revenue, quantum), "cogs": money(cogs, quantum),
            "inventory": inventory, "purchases": money(spent, quantum), **physical}


def aging_balance(cohorts, accrued, period, days, lag, opening, opening_days, start, quantum):
    """Model uniform intra-month accruals with a fixed settlement lag."""
    end = month_key(period, 1)
    cohorts.append((end, days, accrued))
    cohorts[:] = [row for row in cohorts if D((end - row[0]).days) < lag]
    unpaid = sum((amount * min(ONE, (lag - (end - accrued_end).days) / duration)
                  for accrued_end, duration, amount in cohorts), ZERO)
    if (end - start).days < opening_days:
        unpaid += opening
    return money(unpaid, quantum)


def calculate(doc, raw_scenario):
    name, archetype, currency, q, start = terms_for_plan(doc)
    horizon = int(doc["months"])
    factors, delay = scenario_settings(raw_scenario)
    raw_streams = doc.get("streams")
    require(isinstance(raw_streams, list) and raw_streams, "At least one revenue stream is required")
    streams = [stream_settings(row) for row in raw_streams]
    require(len({row["id"] for row in streams}) == len(streams), "Duplicate stream ID")
    state = {s["id"]: {"units": s["opening_inventory"], "value": money(s["opening_inventory_value"], q),
                       "customers": s["opening_customers"]} for s in streams}
    opening_inventory = sum((v["value"] for v in state.values()), ZERO)
    working = doc.get("working_capital", {})
    require(isinstance(working, dict), "Working capital settings must be an object")
    ar_days = number(working.get("receivable_days", 0), "receivable days", maximum=365)
    ap_days = number(working.get("payable_days", 0), "payable days", maximum=365)
    opening_ar = money(number(working.get("opening_receivables", 0), "opening receivables"), q)
    opening_ap = money(number(working.get("opening_payables", 0), "opening payables"), q)
    opening_ar_days = number(working.get("opening_receivable_days_remaining", 0),
                             "remaining opening receivable days", maximum=365)
    opening_ap_days = number(working.get("opening_payable_days_remaining", 0),
                             "remaining opening payable days", maximum=365)
    ar_cohorts, ap_cohorts = [], []
    initial_working = opening_inventory + opening_ar - opening_ap
    nwc = initial_working
    monthly = doc.get("monthly_costs", {})
    require(isinstance(monthly, dict), "Monthly costs must be an object")
    budget = {key: number(value, f"monthly {key}") for key, value in monthly.items()}
    rd_fixed = budget.pop("rd", ZERO)
    fixed = sum(budget.values(), ZERO)
    hires, costs, funds = schedules(doc, horizon)
    tax_rate = number(doc.get("tax_rate", 0), "tax rate", maximum=1)
    base_cash = money(number(doc.get("opening_cash", 0), "opening cash"), q)
    cash = base_cash
    debt = money(number(doc.get("opening_debt", 0), "opening debt"), q)
    reserve = money(number(doc.get("minimum_cash_reserve", 0), "minimum reserve"), q)
    rows = []
    eligible_funds = {f["id"]: f for f in funds if f["id"] is not None}
    for month in range(1, horizon + 1):
        period = month_key(start, month - 1)
        days = monthrange(period.year, period.month)[1]
        results = [run_stream(s, state[s["id"]], month, factors, q) for s in streams]
        totals = {key: sum((r[key] for r in results), ZERO)
                  for key in ("revenue", "cogs", "inventory", "purchases")}
        purchase = totals.pop("purchases")
        revenue, cogs, inventory = (totals[k] for k in ("revenue", "cogs", "inventory"))
        gross = revenue - cogs
        timed = dict.fromkeys(TIMED_COSTS, ZERO)
        for scheduled, kind, amount, debt_id in costs:
            if debt_id is not None:
                if eligible_funds[debt_id]["eligible_month"] is None:
                    continue
                scheduled += delay
            if scheduled == month:
                timed[kind] += amount
        active_hires = sum((amount for m, amount in hires if m <= month), ZERO)
        opex = money((fixed + active_hires + timed["opex"]) * factors["fixed_cost"], q)
        rd = money((rd_fixed + timed["rd"]) * factors["fixed_cost"], q)
        depreciation, interest, capex, principal = (money(timed[k], q)
                                                      for k in ("depreciation", "interest", "capex", "principal"))
        pretax = gross - opex - rd - depreciation - interest
        tax = money(max(pretax, ZERO) * tax_rate, q)
        income = pretax - tax
        ar = aging_balance(ar_cohorts, revenue, period, days, ar_days, opening_ar, opening_ar_days, start, q)
        ap = aging_balance(ap_cohorts, purchase, period, days, ap_days, opening_ap, opening_ap_days, start, q)
        working_end = ar + inventory - ap
        delta = working_end - nwc
        operations = income + depreciation - delta
        arriving = [f for f in funds if f["eligible_month"] is not None and f["eligible_month"] + delay == month]
        loan = money(sum((f["amount"] for f in arriving if f["kind"] in DEBT), ZERO), q)
        other = money(sum((f["amount"] for f in arriving if f["kind"] not in DEBT), ZERO), q)
        received = loan + other
        require(principal <= debt + loan, "Principal repayment exceeds available debt")
        closing_debt = debt + loan - principal
        movement = operations - capex - principal + received
        closing = money(cash + movement, q)
        row = [month, period.isoformat()[:7], revenue, cogs, gross,
               money(100 * gross / revenue, D(".01")) if revenue else ZERO,
               opex, rd, depreciation, interest, tax, income, ar, ap, inventory, working_end, delta,
               operations, capex, principal, received, cash, movement, closing, debt, loan, closing_debt]
        rows.append(dict(zip(FIELDS, [str(v) if isinstance(v, Decimal) else v for v in row])))
        rows[-1]["streams"] = [{k: str(v) if isinstance(v, Decimal) else v for k, v in r.items()}
                              for r in results]
        cash, nwc, debt = closing, working_end, closing_debt
    validate_rows(rows, base_cash, initial_working)
    first_negative = next((r["month"] for r in rows if D(r["closing_cash"]) < 0), None)
    sustained = None
    for row in reversed(rows):
        if D(row["net_income"]) < 0:
            break
        sustained = row["month"]
    minimum = min(D(r["closing_cash"]) for r in rows)
    return {"name": name, "archetype": archetype, "currency": currency, "months": rows,
            "financing_schedule": [{**f, "amount": str(f["amount"]), "scenario_month":
                                    f["eligible_month"] + delay if f["eligible_month"] is not None else None}
                                   for f in funds],
            "summary": {"opening_cash": str(base_cash), "opening_net_working_capital": str(initial_working), "closing_cash": str(cash),
                        "minimum_cash": str(minimum), "first_negative_cash_month": first_negative,
                        "runway_months": first_negative - 1 if first_negative else horizon,
                        "sustained_break_even_month": sustained,
                        "additional_capital_for_reserve": str(max(ZERO, reserve - minimum)),
                        "total_revenue": str(sum(D(r["revenue"]) for r in rows)),
                        "funding_inflow": str(sum(D(r["financing"]) for r in rows))}}


def validate_rows(rows, initial, working=None):
    debt = None
    for expected, row in enumerate(rows, 1):
        require(type(row["month"]) is int and row["month"] == expected
                and isinstance(row["period"], str) and re.fullmatch(r"[0-9]{4}-(?:0[1-9]|1[0-2])", row["period"])
                and all(D(str(row[key])).is_finite() for key in FIELDS[2:]), "Invalid forecast row values")
        value = lambda field: D(row[field])
        require(value("opening_cash") == initial
                and value("gross_profit") == value("revenue") - value("cost_of_goods")
                and value("net_working_capital") == value("accounts_receivable") + value("inventory")
                    - value("accounts_payable")
                and (working is None or value("working_capital_change") == value("net_working_capital") - working)
                and value("gross_margin_pct") == (money(100 * value("gross_profit") / value("revenue"), D(".01"))
                    if value("revenue") else ZERO)
                and value("net_income") == value("gross_profit") - sum(value(k) for k in (
                    "operating_expense", "research_and_development", "depreciation", "interest", "tax"))
                and value("cash_from_operations") == value("net_income") + value("depreciation")
                    - value("working_capital_change")
                and value("cash_movement") == value("cash_from_operations") - value("capital_expenditure")
                    - value("principal_repayment") + value("financing")
                and value("closing_cash") == initial + value("cash_movement")
                and (debt is None or value("opening_debt") == debt)
                and value("closing_debt") == value("opening_debt") + value("debt_financing")
                    - value("principal_repayment") and value("closing_debt") >= 0,
                "Forecast identities disagree")
        initial, debt, working = value("closing_cash"), value("closing_debt"), value("net_working_capital")


def forecast(doc):
    require(isinstance(doc, dict), "Forecast input must be an object")
    scenarios = doc.get("scenarios", {})
    require(isinstance(scenarios, dict) and scenarios.keys() <= {"base", "downside", "upside"},
            "Use base, downside and upside scenario keys")
    result = {name: calculate(doc, factors) for name, factors in {"base": {}, **scenarios}.items()}
    return {"version": 1, "assumptions": doc, "scenarios": result}


def sensitivity(doc, field, values):
    require(field in MULTIPLIERS and isinstance(values, list) and 1 <= len(values) <= 20,
            "Select one sensitivity factor and up to twenty values")
    base = doc.get("scenarios", {}).get("base", {})
    scenario_settings(base)
    return [{"factor": field, "multiplier": value, "summary": calculate(doc, {**base, field: value})["summary"]}
            for value in values]


def capital_plan(doc):
    scenarios = forecast(doc)["scenarios"]
    without = {**doc, "financing": [],
               "one_offs": [c for c in doc.get("one_offs", []) if c.get("financing_id") is None]}
    gap = forecast(without)["scenarios"]
    return {"currency": scenarios["base"]["currency"],
            "scenarios": {name: {"unfunded": gap[name]["summary"], "funded": case["summary"],
                                 "disbursements": case["financing_schedule"]}
                          for name, case in scenarios.items()},
            "milestones": doc.get("milestones", {}),
            "unfunded_policy": "Removes new financing and explicitly linked debt service. Retains opening obligations."}
