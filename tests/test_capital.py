from decimal import Decimal
from io import BytesIO, StringIO
import csv
import unittest
from xml.etree import ElementTree
from zipfile import ZipFile

from seed_core import dilution, finance, model_export
from seed_core.schema import SeedError

MANUFACTURER = {
    "name": "Synthetic components", "archetype": "manufacturing", "currency": "USD",
    "months": 36, "start": "2027-01", "opening_cash": 1000, "minimum_cash_reserve": 150,
    "streams": [{"id": "part", "kind": "manufacturing", "volume": 100, "price": 20,
                 "capacity": 120, "utilisation": 0.5, "yield": 0.5, "material_cost": 2,
                 "labour_cost": 1, "rework_cost": 0.5, "logistics_cost": 1, "warranty_cost": 0.5}],
    "monthly_costs": {"payroll": 100, "rd": 20}, "tax_rate": 0.25,
    "working_capital": {"receivable_days": 31, "payable_days": 0},
    "one_offs": [{"month": 1, "kind": "capex", "amount": 100}],
    "milestones": {"tooling": 2, "certification": None},
    "financing": [{"kind": "grant", "month": 1, "amount": 500, "requires": ["tooling"]},
                  {"kind": "equity", "month": 2, "amount": 1000, "requires": ["certification"]}],
    "scenarios": {"downside": {"financing_delay_months": 2, "unit_cost": 1.1},
                  "upside": {"price": 1.2}},
}


class Capital(unittest.TestCase):
    def test_manufacturing_cash_timing_matches_manual_calculation(self):
        cases = finance.forecast(MANUFACTURER)["scenarios"]
        month = cases["base"]["months"][0]
        for name, target in {"revenue": 600, "cost_of_goods": 240, "gross_profit": 360,
                             "accounts_receivable": 600, "net_income": 180, "tax": 60,
                             "cash_from_operations": -420, "capital_expenditure": 100,
                             "closing_cash": 480}.items():
            self.assertEqual(Decimal(month[name]), target)
        self.assertEqual(Decimal(cases["base"]["months"][1]["financing"]), 500)
        self.assertEqual(Decimal(cases["downside"]["months"][3]["financing"]), 500)
        self.assertIsNone(cases["base"]["financing_schedule"][1]["scenario_month"])
        self.assertEqual(len(cases["base"]["months"]), 36)

    def test_all_archetype_labels_and_csv_excel_from_identical_result(self):
        for archetype in finance.MODELS:
            with self.subTest(archetype=archetype):
                case = finance.calculate({**MANUFACTURER, "archetype": archetype, "months": 60}, {})
                self.assertEqual(len(case["months"]), 60)
        data = list(csv.DictReader(StringIO(model_export.csv_bytes(case).decode())))
        monthly = data[-1]["closing_cash"]
        self.assertEqual(monthly, case["summary"]["closing_cash"])
        with ZipFile(BytesIO(model_export.xlsx_bytes(case))) as z:
            self.assertIsNone(z.testzip())
            for name in z.namelist():
                ElementTree.fromstring(z.read(name))
            self.assertIn(f'<c r="X61"><v>{monthly}</v></c>'.encode(), z.read("xl/worksheets/sheet1.xml"))

    def test_receivable_and_payable_aging_never_create_negative_collections(self):
        doc = {"name": "Synthetic billed service", "archetype": "services", "currency": "USD",
               "months": 36, "start": "2027-01", "streams": [
                   {"id": "work", "kind": "service", "volume": 10, "price": 100, "unit_cost": 20}],
               "working_capital": {"receivable_days": 90, "payable_days": 90},
               "scenarios": {"base": {"price": 2}}}
        base = finance.forecast(doc)["scenarios"]["base"]
        first = base["months"][0]
        self.assertEqual(Decimal(first["accounts_receivable"]), 2000)
        self.assertEqual(Decimal(first["accounts_payable"]), 200)
        self.assertEqual(Decimal(first["cash_from_operations"]), 0)
        self.assertEqual(finance.sensitivity(doc, "volume", [1])[0]["summary"], base["summary"])

    def test_unfunded_comparison_retains_opening_debt_obligations(self):
        doc = {"name": "Synthetic debt", "archetype": "services", "currency": "USD",
               "months": 36, "start": "2027-01", "opening_cash": 110, "opening_debt": 100,
               "streams": [{"id": "work", "kind": "service", "volume": 0, "price": 100}],
               "one_offs": [{"kind": "principal", "month": 1, "amount": 100},
                            {"kind": "interest", "month": 1, "amount": 10},
                            {"kind": "principal", "month": 13, "amount": 100, "financing_id": "future"}],
               "financing": [{"kind": "debt", "id": "future", "month": 12, "amount": 100}]}
        plan = finance.capital_plan(doc)["scenarios"]["base"]
        self.assertEqual(Decimal(plan["unfunded"]["closing_cash"]), 0)
        self.assertEqual(Decimal(plan["unfunded"]["minimum_cash"]), 0)
        self.assertEqual(Decimal(plan["funded"]["closing_cash"]), 0)

    def test_invalid_financing_and_model_parameters_are_refused(self):
        with self.assertRaises(SeedError):
            finance.forecast({**MANUFACTURER, "months": 35})
        with self.assertRaises(SeedError):
            finance.forecast({**MANUFACTURER, "milestones": {"tooling": 0}})
        with self.assertRaises(SeedError):
            finance.forecast({**MANUFACTURER, "streams": [
                {**MANUFACTURER["streams"][0], "yield": 0}]})
        plan = finance.capital_plan(MANUFACTURER)
        self.assertEqual(Decimal(plan["scenarios"]["base"]["unfunded"]["funding_inflow"]), 0)


class Dilution(unittest.TestCase):
    def test_pre_and_post_caps_note_and_pool(self):
        transaction = {"holders": {"Founder": 10000000}, "pre_money": 20000000, "new_money": 5000000}
        safe = {"name": "Synthetic SAFE", "kind": "safe", "amount": 500000,
                "cap": 10000000, "cap_basis": "post_money"}
        post = dilution.priced_round({**transaction, "instruments": [safe]})
        self.assertEqual(Decimal(post["holders"][1]["post_ownership_pct"]), 4)
        pre = dilution.priced_round({**transaction, "instruments": [{**safe, "cap_basis": "pre_money"}]})
        self.assertAlmostEqual(float(pre["holders"][1]["post_ownership_pct"]), 80 / 21, places=6)
        note = {"name": "Synthetic Note", "kind": "note", "amount": 100000,
                "annual_interest": 0.10, "days": 365, "discount": 0.2}
        mixed = dilution.priced_round({**transaction, "instruments": [safe, note], "target_post_pool": 0.1})
        self.assertAlmostEqual(sum(float(r["post_ownership_pct"]) for r in mixed["holders"]), 100, places=6)
        pool = next(r for r in mixed["holders"] if r["via"] == "option_pool")
        self.assertEqual(Decimal(pool["post_ownership_pct"]), 10)

    def test_explicit_preferences_and_anti_dilution(self):
        payout = dilution.liquidation({"exit_proceeds": 1000, "classes": [
            {"name": "A", "shares": 10, "preference": 200, "participation_cap": 250, "election": "participating"},
            {"name": "Founder", "shares": 90, "election": "common"},
        ]})
        self.assertEqual({k: Decimal(v) for k, v in payout["payouts"].items()},
                         {"A": Decimal(250), "Founder": Decimal(750)})
        prices = dilution.ownership_adjustments({"previous_price": 10, "issue_price": 5,
                                                "previous_capitalization": 900, "new_shares": 100,
                                                "ownership": 0.1})
        self.assertEqual(Decimal(prices["pro_rata_cash"]), 50)
        self.assertEqual(Decimal(prices["broad_based_weighted_average_price"]), Decimal("9.5"))
