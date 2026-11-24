"""Spreadsheet exports from reconciled monthly output values."""

import csv
from decimal import Decimal
from io import BytesIO, StringIO
import re
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from .finance import FIELDS, validate_rows
from .schema import require


def csv_bytes(case):
    rows = case["months"]
    validate_rows(rows, Decimal(case["summary"]["opening_cash"]),
                  Decimal(case["summary"]["opening_net_working_capital"]))
    text = StringIO(newline="")
    writer = csv.DictWriter(text, fieldnames=FIELDS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows({**row, **{key: f"{Decimal(row[key]):f}" for key in FIELDS[2:]}} for row in rows)
    return text.getvalue().encode("utf-8")


def xlsx_bytes(case):
    rows = case["months"]
    validate_rows(rows, Decimal(case["summary"]["opening_cash"]),
                  Decimal(case["summary"]["opening_net_working_capital"]))
    currency = case["currency"]
    require(isinstance(currency, str) and re.fullmatch(r"[A-Z]{3}", currency), "Invalid workbook currency")

    def column_name(number):
        name = ""
        while number:
            number, digit = divmod(number - 1, 26)
            name = chr(ord("A") + digit) + name
        return name

    cells = []
    for index, values in enumerate([FIELDS, *[[row[field] for field in FIELDS] for row in rows]], 1):
        cell_xml = []
        for column, value in enumerate(values):
            letter = column_name(column + 1)
            address = f"{letter}{index}"
            if index == 1 or column == 1:
                cell = f'<c r="{address}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'
            else:
                cell = f'<c r="{address}"><v>{Decimal(value):f}</v></c>'
            cell_xml.append(cell)
        cells.append(f'<row r="{index}">{"".join(cell_xml)}</row>')
    sheet_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    relationships = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    package = "http://schemas.openxmlformats.org/package/2006/relationships"
    content = """<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
    <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
    </Types>"""
    workbook = f'<workbook xmlns="{sheet_ns}" xmlns:r="{relationships}"><sheets><sheet name="Forecast {currency}" sheetId="1" r:id="rId1"/></sheets></workbook>'
    workbook_rels = f'<Relationships xmlns="{package}"><Relationship Id="rId1" Type="{relationships}/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
    root_rels = f'<Relationships xmlns="{package}"><Relationship Id="rId1" Type="{relationships}/officeDocument" Target="xl/workbook.xml"/></Relationships>'
    end = column_name(len(FIELDS))
    sheet = (f'<worksheet xmlns="{sheet_ns}"><sheetViews><sheetView workbookViewId="0">'
             '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
             f'</sheetView></sheetViews><cols><col min="1" max="{len(FIELDS)}" width="20" customWidth="1"/></cols>'
             f'<sheetData>{"".join(cells)}</sheetData><autoFilter ref="A1:{end}{len(rows)+1}"/></worksheet>')
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for path, xml in {"[Content_Types].xml": content, "_rels/.rels": root_rels,
                          "xl/workbook.xml": workbook, "xl/_rels/workbook.xml.rels": workbook_rels,
                          "xl/worksheets/sheet1.xml": sheet}.items():
            archive.writestr(path, '<?xml version="1.0" encoding="UTF-8"?>' + xml)
    return buffer.getvalue()
