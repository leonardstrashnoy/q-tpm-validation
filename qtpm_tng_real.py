#!/usr/bin/env python3
"""
Q-TPM Real Data Validator (IllustrisTNG)
Fetches real halo merger trees from IllustrisTNG and maps them to ethical pathways.
"""

import os
import requests
import h5py
import numpy as np
import sqlite3
from datetime import datetime
from io import BytesIO

# ================== CONFIG ==================
API_KEY = os.getenv("TNG_API_KEY") or "24b613fb38c60be4b4df008752de6158"   # ← put your key here or set env var
BASE_URL = "https://www.tng-project.org/api/TNG100-1/"
HEADERS = {"api-key": API_KEY}
DB_PATH = "qtpm_tng_real.db"

# ================== DATABASE ==================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS worldlines (
            halo_id INTEGER PRIMARY KEY,
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

# ================== ILLUSTRISTNG API ==================
def get(path, params=None):
    # Use the exact pattern from the official TNG examples
    r = requests.get(BASE_URL + path, headers=HEADERS, params=params)
    r.raise_for_status()
    if r.headers['content-type'] == 'application/json':
        return r.json()
    return r

def fetch_halo_sample(limit=50, simulation="TNG100-1"):
    """Fetch a sample of halos at z=0"""
    # Try snapshots endpoint first
    snapshots = get(f"{simulation}/snapshots/")
    if snapshots is None:
        return None
    
    print(f"Found {len(snapshots)} snapshots")
    
    # Try to get halos from snapshot 99
    data = get(f"{simulation}/snapshots/99/halos/", params={
        "limit": limit,
        "order_by": "-mass"
    })
    
    if data is None:
        print("Halos endpoint returned None. Trying alternative...")
        # Alternative: try without snapshot number
        data = get(f"{simulation}/halos/", params={"limit": limit})
    
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    elif isinstance(data, list):
        return data[:limit]
    else:
        print(f"Unexpected data type: {type(data)}")
        return None

def fetch_merger_tree(halo_id):
    """Download merger tree for a halo"""
    tree_data = get(f"halos/{halo_id}/tree/", params={
        "fields": "SubhaloMass,SubhaloMassType,SnapNum,DescendantID"
    })
    return tree_data

# ================== PATHWAY CLASSIFICATION ==================
def classify_pathways(tree):
    mass = np.array(tree["SubhaloMass"])
    snap = np.array(tree["SnapNum"])
    stellar = np.array(tree.get("SubhaloMassType", [[0]*5]*len(mass)))[:, 0]

    recent_growth = (mass[-1] - mass[-5]) / mass[-5] if len(mass) > 5 else 0.0
    star_frac = stellar[-1] / mass[-1] if mass[-1] > 0 else 0.0
    form_snap = int(snap[np.argmax(mass > mass[-1] * 0.5)])
    major_mergers = int(np.sum(np.diff(mass) < -0.2))   # crude major merger proxy

    return {
        "expedient": int(recent_growth > 0.25),
        "ruling_guide": int(major_mergers <= 2),
        "analytical": int(star_frac > 0.03),
        "revisionist": int(np.std(mass) / np.mean(mass) > 0.35),
        "value_driven": int(form_snap < 40),
        "global": int(major_mergers > 5),
    }

# ================== MAIN ==================
def main(limit=30):
    if "YOUR_API_KEY" in API_KEY:
        print("ERROR: Please set your IllustrisTNG API key in the script or as TNG_API_KEY env var.")
        return

    conn = init_db()
    print(f"Fetching {limit} halos from IllustrisTNG...")

    halos = fetch_halo_sample(limit)

    for i, halo in enumerate(halos):
        halo_id = halo["id"]
        print(f"  Processing halo {halo_id} ({i+1}/{limit})...")

        try:
            tree = fetch_merger_tree(halo_id)
            pathways = classify_pathways(tree)

            mass = np.array(tree["SubhaloMass"])[-1]
            stellar = np.array(tree.get("SubhaloMassType", [[0]*5]*len(tree["SubhaloMass"])))[:, 0][-1]
            recent_growth = (mass - np.array(tree["SubhaloMass"])[-5]) / np.array(tree["SubhaloMass"])[-5]

            row = {
                "halo_id": halo_id,
                "mass": float(mass),
                "stellar_mass": float(stellar),
                "local_density": 0.0,          # TODO: compute from positions
                "recent_growth": float(recent_growth),
                "star_fraction": float(stellar / mass) if mass > 0 else 0.0,
                "formation_snap": 0,
                "major_mergers": pathways["global"] * 3,
                "curvature": float(np.std(np.diff(np.array(tree["SubhaloMass"]))) / np.mean(np.array(tree["SubhaloMass"]))),
                **pathways,
                "created_at": datetime.now().isoformat()
            }

            conn.execute("""
                INSERT OR REPLACE INTO worldlines VALUES
                (:halo_id, :mass, :stellar_mass, :local_density, :recent_growth,
                 :star_fraction, :formation_snap, :major_mergers, :curvature,
                 :expedient, :ruling_guide, :analytical, :revisionist,
                 :value_driven, :global, :created_at)
            """, row)

        except Exception as e:
            print(f"    Skipped halo {halo_id}: {e}")

    conn.commit()
    conn.close()
    print(f"\nDone. Results saved to {DB_PATH}")

if __name__ == "__main__":
    main(limit=20)
