"""Schema, type and value checks per row, plus the guide's six cross-file checks (section 4.5).

Bad rows are rejected with a reason; the loader never crashes on a broken file.
"""
import json
from datetime import date

import pandas as pd

from app.config import cfg, get_setting, planning_start

# Annex B required columns and their types. Extra columns are allowed.
SCHEMA = {
    "orders": {"order_id": "str", "product": "str", "qty": "int", "destination": "str", "due": "date"},
    "plants": {"plant": "str", "product": "str", "weekly_capacity": "int", "unit_cost": "float",
               "energy_kwh_per_unit": "float", "carbon_kg_per_kwh": "float"},
    "transport_duties": {"plant": "str", "destination": "str", "transport_cost_per_unit": "float",
                         "transit_days": "int", "duty_pct": "float", "carbon_kg_per_unit": "float"},
    "capacity_events": {"event_id": "str", "plant": "str", "from_date": "date", "to_date": "date",
                        "capacity_loss_pct": "float"},
}
# Optional columns this system understands (see README, "Schema extensions")
OPTIONAL = {"plants": {"energy_price_per_kwh": "float", "week_start": "date"}}
KEYS = {"orders": ["order_id"], "plants": ["plant", "product", "week_start"],
        "transport_duties": ["plant", "destination"], "capacity_events": ["event_id"]}
MAX_CARBON_KG_PER_KWH = 2.0  # above this the value is almost certainly g/kWh, not kg/kWh
# Annex B calls these a "percentage" / "share"; packs write them either as 0-100 or as fractions (0.65 = 65%).
PERCENT_COLS = {"transport_duties": "duty_pct", "capacity_events": "capacity_loss_pct"}


class FileRejected(ValueError):
    """Required columns are missing, so nothing in the file can be loaded."""


def _parse(value: str, kind: str):
    if kind == "str":
        if value == "":
            raise ValueError("is empty")
        return value
    if kind == "int":
        f = float(value)
        if not f.is_integer():
            raise ValueError("must be a whole number")
        return int(f)
    if kind == "float":
        f = float(value)
        if f != f or f in (float("inf"), float("-inf")):
            raise ValueError("is not a finite number")
        return f
    if kind == "date":
        return date.fromisoformat(value)
    raise AssertionError(kind)


def _value_rules(table: str, r: dict, start: date) -> tuple[str, str] | None:
    """Return (column, reason) for the first business rule this row breaks."""
    if table == "orders":
        if r["qty"] <= 0:
            return "qty", "Quantity must be a positive whole number"
        if r["due"] <= start:
            return "due", "Due date is before the planning start"
    elif table == "plants":
        if r["weekly_capacity"] <= 0:
            return "weekly_capacity", "Capacity must be positive (units per week)"
        if r["unit_cost"] < 0 or r["energy_kwh_per_unit"] < 0:
            return "unit_cost", "Costs and energy use cannot be negative"
        if not 0 <= r["carbon_kg_per_kwh"] <= MAX_CARBON_KG_PER_KWH:
            return "carbon_kg_per_kwh", f"Carbon intensity must be kg CO2e per kWh (0 to {MAX_CARBON_KG_PER_KWH})"
        if r.get("energy_price_per_kwh") is not None and r["energy_price_per_kwh"] < 0:
            return "energy_price_per_kwh", "Energy price cannot be negative"
    elif table == "transport_duties":
        if r["transit_days"] < 0:
            return "transit_days", "Transit days cannot be negative"
        if not 0 <= r["duty_pct"] <= 100:
            return "duty_pct", "Duty must be a percentage between 0 and 100"
        if r["transport_cost_per_unit"] < 0 or r["carbon_kg_per_unit"] < 0:
            return "transport_cost_per_unit", "Transport cost and carbon cannot be negative"
    elif table == "capacity_events":
        if not 0 < r["capacity_loss_pct"] <= 100:
            return "capacity_loss_pct", "Capacity loss must be between 0 and 100 percent"
        if r["to_date"] < r["from_date"]:
            return "to_date", "End date is before the start date"
    return None


def validate_table(table: str, df: pd.DataFrame, file: str | None = None,
                   start: date | None = None) -> tuple[pd.DataFrame, list[dict]]:
    """Return (valid rows with typed columns, rejected rows with reasons)."""
    file = file or f"{table}.csv"
    start = start or planning_start()
    missing = [c for c in SCHEMA[table] if c not in df.columns]
    if missing:
        raise FileRejected(f"{file} is missing the required column {', '.join(missing)}. Nothing was loaded.")
    types = {**SCHEMA[table], **{c: t for c, t in OPTIONAL.get(table, {}).items() if c in df.columns}}

    parsed = []  # (row_no, record, error)
    for i, raw in enumerate(df.to_dict("records")):
        rec, err = dict(raw), None
        for col, kind in types.items():
            v = raw.get(col, "")
            if v == "" and col in OPTIONAL.get(table, {}):
                rec[col] = None
                continue
            try:
                rec[col] = _parse(v, kind)
            except ValueError as e:
                err = (col, f"'{v}' {e}" if "must" in str(e) or "empty" in str(e) else f"'{v}' is not a valid {kind}")
                break
        parsed.append((i + 2, rec, err))  # header is line 1

    notes = []
    col = PERCENT_COLS.get(table)
    if col:
        vals = [r[col] for _, r, e in parsed if e is None]
        if vals and max(vals) <= 1 and max(vals) > 0:
            # every value is a fraction: read 0.65 as 65 % so the rest of the system sees 0-100
            for _, r, e in parsed:
                if e is None:
                    r[col] = round(r[col] * 100, 6)
            notes.append(f"{col}: all values are between 0 and 1, read as fractions (0.65 = 65%)")

    valid, rejects, seen = [], [], set()
    for row_no, rec, err in parsed:
        if err is None:
            err = _value_rules(table, rec, start)
        key = tuple(rec.get(k) for k in KEYS[table])
        if err is None and key in seen:
            err = (KEYS[table][0], f"Duplicate key {', '.join(str(k) for k in key if k is not None)}")
        if err:
            rejects.append({"file": file, "row": row_no, "column": err[0], "reason": err[1]})
            continue
        seen.add(key)
        valid.append(rec)
    out = pd.DataFrame(valid, columns=list(df.columns) + [c for c in types if c not in df.columns])
    out.attrs["notes"] = notes
    return out, rejects


def cross_checks(t: dict[str, pd.DataFrame], file_rows: dict[str, int] | None = None) -> list[dict]:
    """The six checks from guide section 4.5, over whatever tables are loaded.

    file_rows: rows per file as read (loaded + rejected), compared with the data card's row_counts.
    A check that cannot run (no data card) has passed=None, shown as "not checked", never as a pass.
    """
    orders, plants, lanes = t.get("orders"), t.get("plants"), t.get("transport_duties")
    checks = []

    def add(name, ok, detail=""):
        checks.append({"check": name, "passed": None if ok is None else bool(ok), "detail": detail})

    if orders is not None and plants is not None and len(orders) and len(plants):
        makeable = set(plants["product"])
        bad = orders.loc[~orders["product"].isin(makeable), "order_id"].tolist()
        add("Every order's product can be made in at least one plant", not bad,
            f"No plant makes the product of {', '.join(bad[:10])}" if bad else "")
    else:
        add("Every order's product can be made in at least one plant", False, "orders or plants not loaded")

    if orders is not None and plants is not None and lanes is not None and len(lanes):
        have = set(zip(lanes["plant"], lanes["destination"], strict=False))
        need = {(p, d) for p in set(plants["plant"]) for d in set(orders["destination"])}
        gap = sorted(need - have)
        add("Every plant and destination pair has a transport row", not gap,
            f"Missing: {', '.join(f'{p}->{d}' for p, d in gap[:10])}" if gap else "")
    else:
        add("Every plant and destination pair has a transport row", False, "a table is not loaded")

    unit = cfg()["units"]
    cap_ok = plants is not None and len(plants) and (plants["weekly_capacity"] > 0).all()
    add(f"Capacity is positive, in {unit['capacity']}", cap_ok)
    due_ok = orders is not None and len(orders) and (orders["due"] > planning_start()).all()
    add("Due dates are after the planning start", due_ok)
    ci_ok = plants is not None and len(plants) and plants["carbon_kg_per_kwh"].between(0, MAX_CARBON_KG_PER_KWH).all()
    if ci_ok:
        weekly = [c for c in plants.columns if c.startswith("carbon_kg_per_kwh_week_")]
        ci_ok = all(pd.to_numeric(plants[c], errors="coerce").dropna().between(0, MAX_CARBON_KG_PER_KWH).all()
                    for c in weekly)
    add(f"Carbon intensity is in {unit['carbon_intensity']}", ci_ok)

    stored = get_setting("data_card_row_counts")
    expected = json.loads(stored) if stored else {}  # only from a data card loaded with the files; never fixed
    rows = file_rows or {k: len(v) for k, v in t.items()}
    compared = {k: v for k, v in expected.items() if k in rows}
    if not compared:
        add("Row counts match the data card", None, "not checked: no data card loaded (data_card.json or /ingest meta)")
    else:
        mism = [f"{k}: file has {rows[k]} rows, data card says {v}" for k, v in compared.items() if rows[k] != v]
        add("Row counts match the data card", not mism,
            "; ".join(mism) if mism else ", ".join(f"{k} {v}" for k, v in compared.items()))
    return checks


def plant_capacity_mode(plants: pd.DataFrame) -> str:
    """'plant' if each plant states one weekly capacity for all its products, else 'plant_product'."""
    per_plant = plants.groupby("plant")["weekly_capacity"].nunique()
    return "plant" if (per_plant <= 1).all() else "plant_product"
