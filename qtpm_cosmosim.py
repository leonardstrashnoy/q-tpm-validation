#!/usr/bin/env python3
"""
Q-TPM CosmoSim Validator
Downloads/reads halo data from CosmoSim and maps it to ethical pathways.
"""

import os
import glob
import h5py
import numpy as np
import sqlite3
from datetime import datetime

# ================== CONFIG ==================
DATA_DIR = "cosmosim_data/"          # Put downloaded CosmoSim files here
DB_PATH = "qtpm_cosmosim.db"

# ================== DATABASE ==================
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

# ================== PATHWAY CLASSIFICATION ==================
def classify_pathways(mass, stellar_mass, snap_num, major_mergers):
    recent_growth = (mass[-1] - mass[-5]) / mass[-5] if len(mass) > 5 else 0.0
    star_frac = stellar_mass[-1] / mass[-1] if mass[-1] > 0 else 0.0
    form_snap = int(snap_num[np.argmax(mass > mass[-1] * 0.5)])

    return {
        "expedient": int(recent_growth > 0.25),
        "ruling_guide": int(major_mergers <= 2),
        "analytical": int(star_frac > 0.03),
        "revisionist": int(np.std(mass) / np.mean(mass) > 0.35),
        "value_driven": int(form_snap < 40),
        "global": int(major_mergers > 5),
    }

# ================== DATA LOADING ==================
def load_cosmosim_file(filepath):
    """Load halo data from a CosmoSim HDF5 file"""
    with h5py.File(filepath, "r") as f:
        # Adjust these keys based on the actual CosmoSim file structure
        mass = f["SubhaloMass"][:]
        stellar = f["SubhaloMassType"][:, 0] if "SubhaloMassType" in f else np.zeros_like(mass)
        snap = f["SnapNum"][:] if "SnapNum" in f else np.arange(len(mass))
        mergers = int(f.attrs.get("MajorMergerCount", 3))

    return mass, stellar, snap, mergers

# ================== MAIN ==================
def main():
    conn = init_db()
    files = glob.glob(os.path.join(DATA_DIR, "*.hdf5"))

    if not files:
        print(f"No .hdf5 files found in {DATA_DIR}")
        print("Please download sample data from https://www.cosmosim.org/cms/data/")
        print("and place the files in the 'cosmosim_data/' folder.")
        return

    print(f"Found {len(files)} CosmoSim files.")

    for filepath in files:
        sim_name = os.path.basename(filepath)
        print(f"Processing {sim_name}...")

        try:
            mass, stellar, snap, major_mergers = load_cosmosim_file(filepath)
            pathways = classify_pathways(mass, stellar, snap, major_mergers)

            row = {
                "halo_id": hash(sim_name) % 1000000,
                "simulation": sim_name,
                "mass": float(mass[-1]),
                "stellar_mass": float(stellar[-1]),
                "local_density": 0.0,
                "recent_growth": float((mass[-1] - mass[-5]) / mass[-5]) if len(mass) > 5 else 0.0,
                "star_fraction": float(stellar[-1] / mass[-1]) if mass[-1] > 0 else 0.0,
                "formation_snap": int(snap[np.argmax(mass > mass[-1]*0.5)]),
                "major_mergers": major_mergers,
                "curvature": float(np.std(np.diff(mass)) / np.mean(mass)),
                **pathways,
                "created_at": datetime.now().isoformat()
            }

            conn.execute("""
                INSERT OR REPLACE INTO worldlines VALUES
                (:halo_id, :simulation, :mass, :stellar_mass, :local_density,
                 :recent_growth, :star_fraction, :formation_snap, :major_mergers,
                 :curvature, :expedient, :ruling_guide, :analytical, :revisionist,
                 :value_driven, :global, :created_at)
            """, row)

        except Exception as e:
            print(f"  Skipped {sim_name}: {e}")

    conn.commit()
    conn.close()
    print(f"\nDone. Results saved to {DB_PATH}")

if __name__ == "__main__":
    main()
