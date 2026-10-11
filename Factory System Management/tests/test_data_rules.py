"""Unit conventions, planning start and data-card checks; loading a pack from scripts/generate_data.py."""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from app.config import planning_start, set_setting
from app.data.validate import cross_checks, validate_table
from tests.conftest import START

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def clean_settings():
    for k in ("planning_start", "data_card_row_counts"):
        set_setting(k, None)
    yield
    for k in ("planning_start", "data_card_row_counts"):
        set_setting(k, None)


def lanes(*duties):
    return pd.DataFrame([{"plant": "A", "destination": f"D{i}", "transport_cost_per_unit": "1", "transit_days": "3",
                          "duty_pct": str(d), "carbon_kg_per_unit": "0.5"} for i, d in enumerate(duties)])


def test_fraction_duties_read_as_percent():
    valid, rejects = validate_table("transport_duties", lanes(0.65, 0.03, 0), start=START)
    assert list(valid["duty_pct"]) == [65.0, 3.0, 0.0] and not rejects
    assert "fractions" in valid.attrs["notes"][0]


def test_percent_duties_unchanged():
    valid, _ = validate_table("transport_duties", lanes(4, 25, 0), start=START)
    assert list(valid["duty_pct"]) == [4.0, 25.0, 0.0] and not valid.attrs["notes"]


def test_fraction_capacity_loss_read_as_percent():
    ev = pd.DataFrame([{"event_id": "E1", "plant": "B", "from_date": "2026-10-19", "to_date": "2026-11-01",
                        "capacity_loss_pct": "0.3"}])
    valid, _ = validate_table("capacity_events", ev, start=START)
    assert valid.loc[0, "capacity_loss_pct"] == 30.0


def test_planning_start_setting_drives_due_date_check():
    orders = pd.DataFrame([{"order_id": "O-1", "product": "P1", "qty": "5", "destination": "DE", "due": "2026-11-05"}])
    set_setting("planning_start", "2026-11-09")
    assert planning_start() == date(2026, 11, 9)
    valid, rejects = validate_table("orders", orders)
    assert valid.empty and rejects[0]["column"] == "due"


def test_row_count_check_is_skipped_mismatched_or_passed(tiny):
    check6 = lambda: cross_checks(tiny)[-1]  # noqa: E731
    assert check6()["passed"] is None                      # no data card: not checked, never a silent pass
    set_setting("data_card_row_counts", json.dumps({"orders": 2}))
    assert check6()["passed"] is False                     # file has 1 order
    set_setting("data_card_row_counts", json.dumps({"orders": 1, "plants": 2}))
    assert check6()["passed"] is True


@pytest.mark.skipif(not (REPO / "scripts" / "generate_data.py").exists(), reason="teammate generator not present")
def test_loads_pack_from_teammate_generator(tmp_path):
    """scripts/generate_data.py writes fractions and its own planning start; the loader must honour both."""
    out = tmp_path / "pack"
    subprocess.run([sys.executable, str(REPO / "scripts" / "generate_data.py"), "--output", str(out),
                    "--start-date", "2026-11-02"], check=True, capture_output=True)
    from app.data.load import main as load
    from app.data.store import read_table, run_checks
    from app.tools.planner import make_ctx, run_plan

    report = tmp_path / "report.txt"
    assert load(["--dir", str(out), "--report", str(report)]) == 0
    assert planning_start() == date(2026, 11, 2)
    text = report.read_text(encoding="utf-8")
    assert "read as fractions" in text
    raw = pd.read_csv(out / "capacity_events.csv")
    assert read_table("capacity_events")["capacity_loss_pct"].max() == pytest.approx(raw["capacity_loss_pct"].max() * 100)
    checks = run_checks()
    assert all(c["passed"] for c in checks), checks          # all six run and pass, row counts included
    r = run_plan(make_ctx(), {"cost": 0.7, "carbon": 0.3}, "never_late")
    assert r["validator"]["valid"]
