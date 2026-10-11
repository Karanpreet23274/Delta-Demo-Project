import json
import re

import pandas as pd
import streamlit as st
from common import analyze, api_get, api_post, settings

st.caption("STEP 1 OF 2 · BEFORE PLANNING")
st.title("Data and planning settings")
st.write("Load the four CSV files, fix anything rejected, then set how cost and carbon are weighed.")

settings()  # seed default weight and policy before the widgets read them
TABLES = {"orders": "rows loaded", "plants": "rows", "transport_duties": "lanes", "capacity_events": "events"}
status = api_get("/data/status") or {"datasets": {}, "rejects": [], "checks": []}

st.subheader("Input files · POST /ingest")


def _table_of(name: str) -> str:
    """'orders (1).csv' -> 'orders': browsers add ' (n)' to repeated downloads."""
    return re.sub(r"\s*\(\d+\)$", "", name.rsplit(".", 1)[0].strip().lower())


pack = st.file_uploader("Upload all files at once: orders.csv, plants.csv, transport_duties.csv, capacity_events.csv "
                        "and optionally data_card.json (each file goes to the table its name matches)",
                        type=["csv", "json"], accept_multiple_files=True, key="up_all")
if pack and st.session_state.get("done_all") != tuple(sorted(f.file_id for f in pack)):
    st.session_state["done_all"] = tuple(sorted(f.file_id for f in pack))
    by = {_table_of(f.name): f for f in pack}
    card = {}
    if "data_card" in by:
        try:
            card = json.loads(by["data_card"].getvalue())
        except json.JSONDecodeError:
            st.session_state["upload_error"] = "**File rejected** — data_card.json is not valid JSON"
    notes, problems = [], []
    for table in ("plants", "orders", "transport_duties", "capacity_events"):  # plants first: events check plants
        if table not in by:
            continue
        meta = {"table": table, **({"data_card": card} if card else {})}
        r = api_post("/ingest", files={"file": (f"{table}.csv", by[table].getvalue(), "text/csv")},
                     data={"meta": json.dumps(meta)})
        if not r:
            continue
        notes += [f"{table}.csv: {n}" for n in r.get("notes", [])]
        if r.get("status") in ("rejected", "partial") or "_error" in r:
            problems.append(f"{table}.csv: {r.get('error') or r.get('detail') or str(r['rows_rejected']) + ' rows rejected'}")
    unknown = sorted(set(by) - {"plants", "orders", "transport_duties", "capacity_events", "data_card"})
    if unknown:
        problems.append("not loaded (name matches no table): " + ", ".join(f.name for k, f in by.items() if k in unknown))
    st.session_state["upload_notes"] = notes
    if problems:
        st.session_state["upload_error"] = "**Partly loaded** — " + "; ".join(problems)
    st.rerun()

cols = st.columns(4)
for col, (table, noun) in zip(cols, TABLES.items(), strict=False):
    with col, st.container(border=True):
        ds = status["datasets"].get(table)
        st.markdown(f"**`{table}.csv`**")
        if ds:
            label = "Validated" if not ds["rows_rejected"] else f"{ds['rows_rejected']} rejected"
            st.markdown(f":{'green' if not ds['rows_rejected'] else 'orange'}-background[{label}]")
            a, b = st.columns(2)
            a.metric(noun, ds["rows_loaded"])
            b.metric("rows rejected", ds["rows_rejected"])
        else:
            st.markdown(":gray-background[Not loaded]")
            if table == "capacity_events":
                st.caption("Arrives at the late data drop. Planning works without it; load it to re-plan.")
        up = st.file_uploader("Replace file" if ds else "Upload CSV", type=["csv"], key=f"up_{table}",
                              label_visibility="collapsed")
        if up is not None and st.session_state.get(f"done_{table}") != up.file_id:
            r = api_post("/ingest", files={"file": (f"{table}.csv", up.getvalue(), "text/csv")},
                         data={"meta": f'{{"table": "{table}"}}'})
            st.session_state[f"done_{table}"] = up.file_id
            if r and r.get("notes"):
                st.session_state["upload_notes"] = [f"{table}.csv: {n}" for n in r["notes"]]
            if r and r.get("status") == "rejected":
                st.session_state["upload_error"] = f"**File rejected** — {r.get('error') or 'no valid rows'}"
            elif r and r.get("status") == "partial":
                st.session_state["upload_error"] = (f"**Partly loaded** — {r['rows_loaded']} rows loaded, "
                                                    f"{r['rows_rejected']} rejected. See Rejected rows for each reason.")
            st.rerun()

if msg := st.session_state.pop("upload_error", None):
    (st.error if msg.startswith("**File rejected") else st.warning)(msg)
for note in st.session_state.pop("upload_notes", []):
    st.info(note)
st.caption("Files can have any number of rows (up to the upload safety limit); nothing here assumes the sample's sizes.")

left, right = st.columns(2)
with left, st.container(border=True):
    checks = status["checks"]
    ran = [c for c in checks if c["passed"] is not None]
    passed = sum(c["passed"] for c in ran)
    st.markdown(f"**Validation checks** · {passed} of {len(ran)} passed"
                + (f" · {len(checks) - len(ran)} not checked" if len(ran) < len(checks) else ""))
    for c in checks:
        st.markdown(f"{ {True: '✅', False: '❌', None: '⚪'}[c['passed']] } {c['check']}" + (f"  \n  :gray[{c['detail']}]" if c["detail"] else ""))
    cross_failed = any(c["passed"] is False for c in checks[:2])  # product made somewhere / lane exists
    loaded = {t: d["loaded_at"][:19] for t, d in status["datasets"].items() if t != "capacity_events"}
    if cross_failed and len(set(t[:16] for t in loaded.values())) > 1:  # loaded in different minutes
        st.warning("These files were loaded at different times ("
                   + ", ".join(f"{t} {ts[11:16]}" for t, ts in sorted(loaded.items()))
                   + "), so they may come from different packs. Upload the matching orders, plants and "
                     "transport_duties together with **Upload all files at once**.")
    card = st.file_uploader("Data card (optional) · data_card.json", type=["json"], key="up_card",
                            help="Row counts are never fixed. Upload the data card that came with these files "
                                 "to check their row counts (and set the planning start); without one, the "
                                 "row-count check is shown as not checked.")
    if card is not None and st.session_state.get("done_card") != card.file_id:
        st.session_state["done_card"] = card.file_id
        try:
            r = api_post("/data_card", json=json.loads(card.getvalue()))
        except json.JSONDecodeError:
            r = {"_error": 422, "detail": "data_card.json is not valid JSON"}
        if r and "_error" in r:
            st.session_state["upload_error"] = f"**File rejected** — {r.get('detail')}"
        st.rerun()
with right, st.container(border=True):
    st.markdown("**Rejected rows**")
    rej = pd.DataFrame(status["rejects"])
    if rej.empty:
        st.caption("No rejected rows.")
    else:
        st.dataframe(rej, hide_index=True, use_container_width=True, height=200)
        st.download_button("Download rejects.csv", rej.to_csv(index=False), "rejects.csv")
    st.caption("Rejected rows are left out of planning. Fix the source file and upload it again to include them.")

with st.container(border=True):
    st.markdown("**Planning settings**")
    a, b, c = st.columns([2, 2, 1])
    with a:
        # widgets write to plain session keys so the values survive page switches
        ss = st.session_state
        ss.cost_w = st.slider("Cost versus carbon weight (cost %)", 0, 100, value=ss.cost_w, step=5)
        st.caption(f"Cost **{ss.cost_w}%** · Carbon **{100 - ss.cost_w}%**. "
                   "Default 70 / 30. Weights apply to normalised cost and carbon, so they mean what they say.")
    with b:
        opts = ["never_late", "allow_late"]
        ss.policy = st.radio("Delivery policy", opts, index=opts.index(ss.policy),
                             format_func=lambda p: {"never_late": "Never late — orders with no on-time option are flagged, not hidden",
                                                    "allow_late": "Allow late with a penalty — late orders are counted and shown"}[p])
    with c:
        ss.start = st.date_input("Planning start", value=ss.get("start"), help="Leave empty to use the planning start loaded with the data "
                                 f"({status.get('planning_start', 'config.yaml')})")
    ready = all(t in status["datasets"] and status["datasets"][t]["rows_loaded"] for t in
                ("orders", "plants", "transport_duties"))
    if st.button("Generate allocation", type="primary", disabled=not ready):
        settings()
        r = analyze("Allocate this week's orders.")
        if r:
            st.switch_page("screens/results.py")
    st.caption("Runs the solver through POST /analyze. Enabled once every required file passes validation."
               if ready else "Disabled until orders.csv, plants.csv and transport_duties.csv are loaded.")
