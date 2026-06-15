#!/usr/bin/env python3
"""
Export a `worldlines` SQLite DB to a site/<name>.json for the static dashboard.

Unlike export_data.py (which regenerates the synthetic set deterministically),
this dumps an existing DB — including the real-data ones built by the CAMELS /
Bolshoi validators, whose merger-history columns are NULL. NULLs are preserved
as JSON null so the dashboard can detect which fields a dataset actually has.

Usage:
    python export_db.py qtpm_camels.db site/data_camels.json
"""

import json
import sqlite3
import sys
from pathlib import Path

PATHWAY_COLS = ["expedient", "ruling_guide", "analytical",
                "revisionist", "value_driven", "global"]

# Columns the dashboard never needs; dropped to keep the payload small.
DROP_COLS = {"created_at", "simulation", "snapshot"}
# Floats rounded to this many significant places to shrink the JSON.
ROUND = 6


def _coerce(value):
    if isinstance(value, float):
        return round(value, ROUND)
    return value


def export(db_path, out_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM worldlines").fetchall()
    conn.close()

    if not rows:
        raise SystemExit(f"{db_path}: worldlines is empty")

    cols = [c for c in rows[0].keys() if c not in DROP_COLS]
    halos = [{c: _coerce(r[c]) for c in cols} for r in rows]

    payload = {"pathway_cols": PATHWAY_COLS, "halos": halos}
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"Wrote {len(halos)} rows ({len(cols)} cols) to {out} "
          f"({out.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python export_db.py <db_path> <out_json>")
        raise SystemExit(1)
    export(sys.argv[1], sys.argv[2])
