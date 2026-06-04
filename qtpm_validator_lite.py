#!/usr/bin/env python3
"""
Lightweight Q-TPM Validator (no numpy/h5py required)
Generates synthetic halo worldlines and stores them in SQLite.
"""

import sqlite3
import random
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

def generate_synthetic_halos(n=300):
    data = []
    for i in range(n):
        mass = random.uniform(1e10, 5e12)
        stellar = mass * random.uniform(0.01, 0.08)
        density = random.uniform(0.2, 4.5)
        recent_growth = random.uniform(0.05, 0.45)
        star_frac = stellar / mass
        form_snap = random.randint(20, 70)
        major = random.randint(0, 9)
        curvature = random.uniform(0.01, 0.18)
        path_curv = random.uniform(0.005, 0.12)

        pathways = {
            "expedient": int(recent_growth > 0.25 and density < 1.0),
            "ruling_guide": int(major <= 2),
            "analytical": int(star_frac > 0.03),
            "revisionist": int(curvature > 0.09),
            "value_driven": int(form_snap < 40),
            "global": int(major > 6 or density > 2.0),
        }

        row = {
            "halo_id": 10000 + i,
            "snapshot": 99,
            "mass": round(mass, 2),
            "stellar_mass": round(stellar, 2),
            "local_density": round(density, 3),
            "recent_growth": round(recent_growth, 4),
            "star_fraction": round(star_frac, 4),
            "formation_snap": form_snap,
            "major_mergers": major,
            "curvature": round(curvature, 5),
            "path_curvature": round(path_curv, 5),
            **pathways,
            "created_at": datetime.now().isoformat()
        }
        data.append(row)
    return data

def main():
    conn = init_db()
    halos = generate_synthetic_halos(300)
    print(f"Generating {len(halos)} synthetic halos...")

    for row in halos:
        conn.execute("""
            INSERT OR REPLACE INTO worldlines VALUES
            (:halo_id, :snapshot, :mass, :stellar_mass, :local_density,
             :recent_growth, :star_fraction, :formation_snap, :major_mergers,
             :curvature, :path_curvature,
             :expedient, :ruling_guide, :analytical, :revisionist,
             :value_driven, :global, :created_at)
        """, row)

    conn.commit()
    conn.close()
    print(f"Database created: {DB_PATH} ({len(halos)} rows)")

if __name__ == "__main__":
    main()
