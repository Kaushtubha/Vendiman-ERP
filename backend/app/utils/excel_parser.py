"""
app/utils/excel_parser.py — Excel Ingestion Utility
"""

from __future__ import annotations

import io
from decimal import Decimal
from typing import Any

import openpyxl


def parse_product_excel(file_bytes: bytes) -> list[dict[str, Any]]:
    """
    Parses an uploaded Excel sheet of products.
    Expected columns (case-insensitive):
    SKU, Name, Category, MRP, Cost Price, Selling Price, GST Rate, Unit, Reorder Point, Reorder Quantity
    """
    wb = openpyxl.load_workbook(filename=io.BytesIO(file_bytes), data_only=True)
    sheet = wb.active

    headers = []
    rows = []
    for row_idx, row in enumerate(sheet.iter_rows(values_only=True)):
        if row_idx == 0:
            headers = [str(cell).strip().lower() if cell is not None else "" for cell in row]
            continue

        if not any(row):
            continue

        row_dict = dict(zip(headers, row))
        sku = str(row_dict.get("sku", "") or "").strip().upper()
        name = str(row_dict.get("name", "") or "").strip()

        if not sku or not name:
            continue

        try:
            mrp = Decimal(str(row_dict.get("mrp", 0) or 0))
            cost_price = Decimal(str(row_dict.get("cost price", row_dict.get("cost_price", 0)) or 0))
            selling_price = Decimal(str(row_dict.get("selling price", row_dict.get("selling_price", mrp)) or mrp))
            gst = str(row_dict.get("gst rate", row_dict.get("gst_rate", "18")) or "18").replace("%", "").strip()
            reorder_point = int(row_dict.get("reorder point", row_dict.get("reorder_point", 10)) or 10)
            reorder_qty = int(row_dict.get("reorder quantity", row_dict.get("reorder_quantity", 50)) or 50)
            brand = str(row_dict.get("brand", "") or "").strip() or None
            unit = str(row_dict.get("unit", "piece") or "piece").strip()

            rows.append({
                "sku": sku,
                "name": name,
                "brand": brand,
                "unit": unit,
                "mrp": mrp,
                "cost_price": cost_price,
                "selling_price": selling_price,
                "gst_rate": gst,
                "reorder_point": reorder_point,
                "reorder_quantity": reorder_qty,
            })
        except Exception:
            continue

    return rows
