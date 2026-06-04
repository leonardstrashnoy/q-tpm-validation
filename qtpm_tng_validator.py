#!/usr/bin/env python3
"""
Q-TPM Validation Pipeline
Maps Rodgers’ six ethical pathways onto IllustrisTNG halo worldlines
and stores results in SQLite for proposition testing.
"""

import numpy as np
import sqlite3
import h5py
import glob
from scipy.spatial import cKDTree
from datetime import datetime

DB_PATH = "qtpm_validation.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS worldlines (
            halo_id INTEGER PRIMARY KEY,
            snapshot INTEGER,
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

def compute_local_density(positions, k=32):
    if len(positions) < k:
        return 0.0
    tree = cKDTree(positions)
    dist, _ = tree.query(positions, k=k)
    r = dist[:, -1]
    vol = (4/3) * np.pi * r**3
    return k / np.mean(vol)

def compute_path_curvature(mass):
    if len(mass) < 3:
        return 0.0
    d1 = np.diff(mass)
    d2 = np.diff(d1)
    return float(np.mean(np.abs(d2)) / (np.mean(np.abs(d1)) + 1e-8))

def classify_pathways(sub, tree, density):
    mass = np.array(tree["SubhaloMass"])
    snap = np.array(tree["SnapNum"])
    stellar = sub.get("StellarMass", 0.0)
    recent_growth = (mass[-1] - mass[-5]) / mass[-5] if len(mass) > 5 else 0.0
    star_frac = stellar / mass[-1] if mass[-1] > 0 else 0.0
    form_snap = int(snap[np.argmax(mass > mass[-1]*0.5)])
    major = int(tree.get("MajorMergerCount", 0))

    return {
        "expedient": int(recent_growth > 0.25 and density < 1.0),
        "ruling_guide": int(major <= 2),
        "analytical": int(star_frac > 0.03),
        "revisionist": int(np.std(mass) / np.mean(mass) > 0.35),
        "value_driven": int(form_snap < 40),
        "global": int(major > 6 or density > 2.0),
    }

def process_halo(h5file):
    with h5py.File(h5file, "r") as f:
        sub = {k: float(f[k][()]) if f[k].ndim == 0 else f[k][()] 
               for k in f.keys() if k != "tree"}
        tree = {k: f["tree"][k][()] for k in f["tree"].keys()}

    mass = np.array(tree["SubhaloMass"])
    density = compute_local_density(sub.get("SubhaloPos", np.zeros((10,3))))
    pathways = classify_pathways(sub, tree, density)
    curvature = float(np.std(np.diff(mass)) / np.mean(mass)) if len(mass) > 1 else 0.0
    path_curv = compute_path_curvature(mass)

    return {
        "halo_id": int(sub.get("ID", -1)),
        "snapshot": 99,
        "mass": float(mass[-1]),
        "stellar_mass": float(sub.get("StellarMass", 0)),
        "local_density": float(density),
        "recent_growth": float((mass[-1] - mass[-5]) / mass[-5]) if len(mass) > 5 else 0.0,
        "star_fraction": float(sub.get("StellarMass", 0) / mass[-1]) if mass[-1] > 0 else 0.0,
        "formation_snap": int(np.argmax(mass > mass[-1]*0.5)),
        "major_mergers": int(tree.get("MajorMergerCount", 0)),
        "curvature": curvature,
        "path_curvature": path_curv,
        **pathways,
        "created_at": datetime.now().isoformat()
    }

def run_batch(tree_dir, limit=500):
    conn = init_db()
    files = glob.glob(f"{tree_dir}/*.hdf5")[:limit]
    print(f"Processing {len(files)} halos into {DB_PATH}...")

    for i, f in enumerate(files):
        try:
            row = process_halo(f)
            conn.execute("""
                INSERT OR REPLACE INTO worldlines VALUES
                (:halo_id, :snapshot, :mass, :stellar_mass, :local_density,
                 :recent_growth, :star_fraction, :formation_snap, :major_mergers,
                 :curvature, :path_curvature,
                 :expedient, :ruling_guide, :analytical, :revisionist,
                 :value_driven, :global, :created_at)
            """, row)
            if (i + 1) % 50 == 0:
                print(f"  {i+1} halos processed...")
        except Exception as e:
            print(f"  Skipped {f}: {e}")

    conn.commit()
    conn.close()
    print(f"\nComplete. Database ready at {DB_PATH}")

if __name__ == "__main__":
    run_batch("trees/", limit=300)
