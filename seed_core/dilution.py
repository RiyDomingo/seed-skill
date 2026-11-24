"""Exact arithmetic for specified financing, preferences and dilution cases."""

from fractions import Fraction
from decimal import Decimal, localcontext

from .finance import number
from .schema import require, string


def fraction(value, label, minimum=0, maximum=10**15):
    return Fraction(number(value, label, minimum=minimum, maximum=maximum))


def format_fraction(value, places=8):
    with localcontext() as context:
        context.prec = 45
        n = Decimal(value.numerator) / Decimal(value.denominator)
        return f"{n:.{places}f}"


def instrument(row):
    require(isinstance(row, dict) and row.get("kind") in {"safe", "note"}, "Invalid convertible instrument")
    invested = fraction(row.get("amount"), "investment", minimum=1)
    cap = fraction(row["cap"], "valuation cap", minimum=1) if row.get("cap") is not None else None
    discount = fraction(row.get("discount", 0), "discount", maximum=0.99)
    basis = row.get("cap_basis")
    if cap:
        require(basis in {"pre_money", "post_money"}, "Specify pre-money or post-money cap basis")
    if row["kind"] == "note":
        rate = fraction(row.get("annual_interest"), "note annual interest", maximum=1)
        days = row.get("days")
        require(type(days) is int and 0 <= days <= 3650, "Give the note interest period in days")
        converted = invested * (1 + rate * days / 365)
    else:
        converted = invested
    return {"name": string(row.get("name"), "instrument name"), "amount": converted,
            "cap": cap, "basis": basis, "discount": discount}


def priced_round(doc):
    require(isinstance(doc, dict), "Round input must be an object")
    holders = doc.get("holders")
    require(isinstance(holders, dict) and holders, "Provide holders and issued shares")
    issued = {string(name, "holder"): fraction(value, "holder shares", minimum=1)
              for name, value in holders.items()}
    require(len({name.casefold() for name in issued}) == len(holders), "Duplicate normalized holder names")
    require(all(value.denominator == 1 for value in issued.values()), "Existing issued shares must be whole")
    unissued = fraction(doc.get("unissued_pool", 0), "existing pool shares")
    require(unissued.denominator == 1, "Existing pool shares must be whole")
    opening = sum(issued.values()) + unissued
    valuation = fraction(doc.get("pre_money"), "priced-round pre-money valuation", minimum=1)
    investment = fraction(doc.get("new_money"), "round investment", minimum=1)
    target = fraction(doc.get("target_post_pool", 0), "target post-round pool", maximum=0.5)
    convertibles = doc.get("instruments", [])
    require(isinstance(convertibles, list) and len(convertibles) <= 30, "Provide up to thirty convertibles")
    rows = [instrument(item) for item in convertibles]
    require(len({row["name"] for row in rows}) == len(rows), "Convertible names must be unique")
    at_cap = tuple(row["cap"] is not None for row in rows)
    visited = set()
    while at_cap not in visited:
        visited.add(at_cap)
        require(len(visited) <= 128, "Conversion terms did not settle")
        pre_fixed = sum(row["amount"] * opening / row["cap"]
                        for row, uses_cap in zip(rows, at_cap) if uses_cap and row["basis"] == "pre_money")
        post_ratio = sum(row["amount"] / row["cap"]
                         for row, uses_cap in zip(rows, at_cap) if uses_cap and row["basis"] == "post_money")
        discount_ratio = sum(row["amount"] / (valuation * (1 - row["discount"]))
                             for row, uses_cap in zip(rows, at_cap) if not uses_cap)
        require(post_ratio + discount_ratio < 1, "Conversion leaves no existing equity")
        pre_shares = (opening + pre_fixed) / (1 - post_ratio - discount_ratio)
        base = pre_shares
        additional_pool = Fraction(0)
        desired = target * (valuation + investment) / valuation
        if desired * pre_shares > unissued:
            denominator = 1 - desired - discount_ratio / (1 - post_ratio)
            require(denominator > 0, "Conversion and pool leave no existing equity")
            pre_shares = ((opening + pre_fixed) / (1 - post_ratio) - unissued) / denominator
            base = (opening + pre_fixed + discount_ratio * pre_shares) / (1 - post_ratio)
            additional_pool = pre_shares - base
        round_price = valuation / pre_shares
        cap_prices = [row["cap"] / (opening if row["basis"] == "pre_money" else base)
                      if row["cap"] else None for row in rows]
        change = tuple(p is not None and p <= round_price * (1 - r["discount"])
                       for p, r in zip(cap_prices, rows))
        if change == at_cap:
            break
        at_cap = change
    else:
        require(False, "Conversion terms did not settle")
    allocations = []
    for row, price_cap, uses_cap in zip(rows, cap_prices, at_cap):
        price = price_cap if uses_cap else round_price * (1 - row["discount"])
        allocations.append((row["name"], row["amount"] / price, "cap" if uses_cap else "discount_or_round"))
    new_shares = investment / round_price
    equity_rows = [(name, shares, "existing") for name, shares in issued.items()]
    equity_rows += allocations + [("Unissued option pool", unissued + additional_pool, "option_pool"),
                                 ("New round", new_shares, "new_financing")]
    post = pre_shares + new_shares
    require(sum(shares for _, shares, _ in equity_rows) == post, "Share allocation does not reconcile")
    return {"price_per_share": format_fraction(round_price), "post_shares": format_fraction(post),
            "added_pool_shares": format_fraction(additional_pool),
            "holders": [{"name": name, "shares": format_fraction(shares),
                         "post_ownership_pct": format_fraction(shares / post * 100), "via": method}
                        for name, shares, method in equity_rows],
            "assumptions": {"round_pre_money_includes_converted_shares_and_pool": True,
                            "pre_money_caps_exclude_converting_shares_and_pool_top_up": True,
                            "post_money_caps_include_all_convertibles_but_exclude_pool_top_up": True,
                            "notes_actual_365_simple_interest": True,
                            "elected_lower_conversion_price": True}}


def liquidation(doc):
    """Run a waterfall with explicit, founder-supplied conversion elections."""
    require(isinstance(doc, dict), "Waterfall must be an object")
    remaining = fraction(doc.get("exit_proceeds"), "exit proceeds")
    groups = doc.get("classes")
    require(isinstance(groups, list) and groups and len(groups) <= 30, "Provide share classes")
    shares, pref, caps, rank, payouts = {}, {}, {}, {}, {}
    for row in groups:
        require(isinstance(row, dict), "Invalid share class")
        name = string(row.get("name"), "class name")
        require(name not in shares, "Duplicate share class")
        count = fraction(row.get("shares"), "class shares", minimum=1)
        priority = row.get("priority", 0)
        require(type(priority) is int and priority >= 0, "Invalid preference priority")
        election = row.get("election")
        require(election in {"common", "convert", "nonparticipating", "participating"},
                "Each class needs an explicit liquidation election")
        cash = fraction(row.get("preference", 0), "contractual preference")
        shares[name] = count if election != "nonparticipating" else Fraction(0)
        pref[name] = cash if election in {"nonparticipating", "participating"} else Fraction(0)
        caps[name] = fraction(row["participation_cap"], "participation cap") if (
            election == "participating" and row.get("participation_cap") is not None) else None
        require(caps[name] is None or caps[name] >= pref[name], "Participation cap below preference")
        rank[name], payouts[name] = priority, Fraction(0)
    for priority in sorted(set(rank.values())):
        group = [name for name in shares if rank[name] == priority]
        due = sum(pref[name] for name in group)
        if due:
            paid = min(remaining, due)
            for name in group:
                payouts[name] += paid * pref[name] / due
            remaining -= paid
    eligible = {name for name, count in shares.items() if count}
    while remaining > 0 and eligible:
        total_shares = sum(shares[name] for name in eligible)
        capped = {name for name in eligible if caps[name] is not None
                  and remaining * shares[name] / total_shares > caps[name] - payouts[name]}
        if not capped:
            for name in eligible:
                payouts[name] += remaining * shares[name] / total_shares
            remaining = Fraction(0)
        else:
            for name in capped:
                paid = caps[name] - payouts[name]
                payouts[name] += paid
                remaining -= paid
            eligible -= capped
    return {"payouts": {name: format_fraction(cash) for name, cash in payouts.items()},
            "unallocated": format_fraction(remaining), "basis": "Explicit class elections and priorities"}


def ownership_adjustments(doc):
    require(isinstance(doc, dict), "Ownership adjustments must be an object")
    old_price = fraction(doc.get("previous_price"), "previous price", minimum=0.00000001)
    new_price = fraction(doc.get("issue_price"), "new price", minimum=0.00000001)
    old_shares = fraction(doc.get("previous_capitalization"), "previous capitalization", minimum=1)
    new_shares = fraction(doc.get("new_shares"), "new shares", minimum=1)
    ownership = fraction(doc.get("ownership"), "existing ownership fraction", maximum=1)
    broad = old_price * (old_shares + new_price * new_shares / old_price) / (old_shares + new_shares)
    return {"pro_rata_cash": format_fraction(ownership * new_price * new_shares),
            "broad_based_weighted_average_price": format_fraction(min(old_price, broad)),
            "full_ratchet_price": format_fraction(min(old_price, new_price)),
            "basis": "Uses the supplied capitalization universe and financing terms"}
