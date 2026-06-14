#!/usr/bin/env python3
"""
Q-TPM CAMELS Validator (Public Data, No API Key)

CAMELS (Cosmology and Astrophysics with MachinE Learning Simulations)
has public data releases available without API keys.

Download instructions:
- Main site: https://camels.readthedocs.io/
- Public data: https://camels.readthedocs.io/en/latest/Data.html
- Many suites have halo catalogs in HDF5 or text format.

Instructions:
1. Download CAMELS halo data (e.g. from IllustrisTNG or SIMBA suites)
2. Place files in the `camels_data/` folder
3. Run this script

This is a template — you will need to adapt column mapping.
"""

import os
import glob
import sqlite3
import pandas as pd
from datetime import datetime

DATA_DIR = "camels_data/"
DB_PATH = "qtpm_camels.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS worldlines (
            halo_id INTEGER PRIMARY KEY,
            simulation TEXT,
            mass REAL,
            stellar_mass REAL,
            local_density REAL,
            recent_growth REAL,
            star_fraction REAL,
            formation_snap INTEGER,
            major_mergers INTEGER,
            curvature REAL,
            path_curvature REAL,
            expedient INTEGER,
            ruling_guide INTEGER,
            analytical INTEGER,
            revisionist INTEGER,
            value_driven INTEGER,
            global INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn


def load_camels_data():
    """Load CAMELS halo files from camels_data/ folder."""
    files = (
        glob.glob(os.path.join(DATA_DIR, "*.hdf5")) +
        glob.glob(os.path.join(DATA_DIR, "*.h5")) +
        glob.glob(os.path.join(DATA_DIR, "*.txt")) +
        glob.glob(os.path.join(DATA_DIR, "*.csv"))
    )

    if not files:
        print(f"No CAMELS data files found in {DATA_DIR}")
        return pd.DataFrame()

    dfs = []
    for f in files:
        try:
            if f.endswith((".hdf5", ".h5")):
                # CAMELS often uses HDF5 with groups
                import h5py
                with h5py.File(f, "r") as hf:
                    # Adjust group/key names based on actual CAMELS structure
                    if "Halos" in hf:
                        data = hf["Halos"][:]
                        df = pd.DataFrame(data)
                    else:
                        # fallback: take first dataset
                        key = list(hf.keys())[0]
                        df = pd.DataFrame(hf[key][:])
                dfs.append(df)
            else:
                df = pd.read_csv(f, sep=r"\s+", comment="#")
                dfs.append(df)
        except Exception as e:
            print(f"Could not read {f}: {e}")

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def map_to_worldlines(df):
    """Map CAMELS columns to Q-TPM worldlines schema.

    NOTE: recent_growth, formation_snap, major_mergers, curvature, etc. are
    PLACEHOLDER CONSTANTS, identical for every halo. They are not real
    measurements and must not be read as validation results until proper
    column mapping is implemented.
    """
    if df.empty:
        return []

    has_id = any(c in df.columns for c in ("id", "ID"))
    if not has_id:
        print("WARNING: no id/ID column found — assigning sequential halo_ids.")

    records = []
    for i, (_, row) in enumerate(df.iterrows()):
        try:
            mass = float(row.get("Mvir", row.get("mass", row.get("M200c", 1e12))))
            stellar = float(row.get("Mstar", mass * 0.015))

            # Unique fallback id prevents PRIMARY KEY collisions that would
            # silently collapse every row into one.
            halo_id = int(row.get("id", row.get("ID", i))) if has_id else i

            record = {
                "halo_id": halo_id,
                "simulation": "CAMELS",
                "mass": round(mass, 2),
                "stellar_mass": round(stellar, 2),
                "local_density": float(row.get("rho", 1.0)),
                "recent_growth": 0.1,
                "star_fraction": round(stellar / mass, 4) if mass > 0 else 0.0,
                "formation_snap": 50,
                "major_mergers": 3,
                "curvature": 0.05,
                "path_curvature": 0.03,
                "expedient": 0,
                "ruling_guide": 0,
                "analytical": 0,
                "revisionist": 0,
                "value_driven": 0,
                "global": 0,
                "created_at": datetime.now().isoformat()
            }
            records.append(record)
        except Exception:
            continue

    return records


def main():
    conn = init_db()
    df = load_camels_data()

    if df.empty:
        print("No data loaded. Please download CAMELS catalogs into camels_data/")
        return

    print(f"Loaded {len(df)} halos from CAMELS data")

    records = map_to_worldlines(df)
    if records:
        conn.executemany("""
            INSERT OR REPLACE INTO worldlines VALUES
            (:halo_id, :simulation, :mass, :stellar_mass, :local_density,
             :recent_growth, :star_fraction, :formation_snap, :major_mergers,
             :curvature, :path_curvature,
             :expedient, :ruling_guide, :analytical, :revisionist,
             :value_driven, :global, :created_at)
        """, records)
        conn.commit()
        print(f"Inserted {len(records)} halos into {DB_PATH}")

    conn.close()


if __name__ == "__main__":
    main()