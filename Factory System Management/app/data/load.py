"""CLI loader for judge test data in the Annex B schema.

Usage: python -m app.data.load --dir <folder> [--planning-start YYYY-MM-DD] [--report <file>]
Loads orders.csv, plants.csv, transport_duties.csv and capacity_events.csv (any that exist),
then prints the validation report. If the folder has a data_card.json, its planning_start and
row_counts are used (a --planning-start flag wins over the card).
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

from app.config import planning_start, set_setting
from app.data.loader import TABLES, LoadError
from app.data.store import apply_data_card, ingest_bytes, run_checks
from app.data.validate import FileRejected

# plants first so capacity_events can be checked against known plants
ORDER = ("plants", "orders", "transport_duties", "capacity_events")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", required=True, help="folder with the CSV files")
    ap.add_argument("--planning-start", type=date.fromisoformat, help="first day of planning week 1")
    ap.add_argument("--data-card", help="data card JSON (default: <dir>/data_card.json if present)")
    ap.add_argument("--report", help="also write this report to a file")
    a = ap.parse_args(argv)
    folder = Path(a.dir)
    lines: list[str] = []

    def out(s: str = "") -> None:
        print(s)
        lines.append(s)

    card_path = Path(a.data_card) if a.data_card else folder / "data_card.json"
    if card_path.exists():
        try:
            applied = apply_data_card(json.loads(card_path.read_text(encoding="utf-8")))
            out(f"data card {card_path.name}: {'; '.join(applied) or 'no planning_start or row_counts'}")
        except (ValueError, json.JSONDecodeError) as e:
            out(f"data card {card_path.name}: ignored ({e})")
    if a.planning_start:
        set_setting("planning_start", a.planning_start.isoformat())
    out(f"planning start {planning_start().isoformat()}\n")

    failed = False
    for table in ORDER:
        path = folder / f"{table}.csv"
        if not path.exists():
            out(f"{table:17} not found (skipped)")
            continue
        try:
            r = ingest_bytes(path.read_bytes(), table)
        except (LoadError, FileRejected) as e:
            out(f"{table:17} REJECTED  {e}")
            failed = True
            continue
        out(f"{table:17} {r['status']:9} rows_loaded={r['rows_loaded']} rows_rejected={r['rows_rejected']}")
        for note in r["notes"]:
            out(f"    note: {note}")
        for rej in r["rejects"]:
            out(f"    row {rej['row']}  {rej['column']}: {rej['reason']}")
    out("\nValidation checks")
    checks = run_checks()
    for c in checks:
        tag = {True: "PASS", False: "FAIL", None: "SKIP"}[c["passed"]]
        out(f"  [{tag}] {c['check']}" + (f"  ({c['detail']})" if c["detail"] else ""))
    ran = [c for c in checks if c["passed"] is not None]
    out(f"{sum(c['passed'] for c in ran)} of {len(ran)} passed"
        + (f", {len(checks) - len(ran)} not checked" if len(ran) < len(checks) else ""))
    if a.report:
        Path(a.report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    assert set(ORDER) == set(TABLES)
    sys.exit(main())
