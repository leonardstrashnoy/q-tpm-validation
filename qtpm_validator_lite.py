#!/usr/bin/env python3
"""
Improved Q-TPM Synthetic Data Generator
Creates more realistic halo distributions for testing.
"""

import sqlite3
import random
import numpy as np
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

def generate_realistic_halos(n=400):
    data = []
    np.random.seed(42)
    
    for i in range(n):
        # More realistic mass distribution (log-normal)
        log_mass = np.random.normal(11.5, 1.2)
        mass = 10 ** log_mass
        
        # Stellar fraction decreases with mass
        star_frac = max(0.008, min(0.09, np.random.beta(2, 5) * 0.12))
        stellar = mass * star_frac
        
        # Density correlates with environment
        local_density = max(0.1, np.random.lognormal(0.3, 0.8))
        
        # Recent growth more realistic
        recent_growth = max(0.01, np.random.beta(2, 4) * 0.5)
        
        # Formation time
        formation_snap = int(np.random.beta(1.5, 2.5) * 80 + 10)
        
        # Major mergers
        major_mergers = int(np.random.poisson(3.2))
        
        # Curvature
        curvature = max(0.01, np.random.beta(2, 6) * 0.22)
        path_curv = max(0.005, np.random.beta(2, 7) * 0.15)
        
        pathways = {
            "expedient": int(recent_growth > 0.22 and local_density < 1.2),
            "ruling_guide": int(major_mergers <= 2),
            "analytical": int(star_frac > 0.035),
            "revisionist": int(curvature > 0.085),
            "value_driven": int(formation_snap < 38),
            "global": int(major_mergers > 5 or local_density > 2.8),
        }
        
        row = {
            "halo_id": 10000 + i,
            "snapshot": 99,
            "mass": round(mass, 2),
            "stellar_mass": round(stellar, 2),
            "local_density": round(local_density, 3),
            "recent_growth": round(recent_growth, 4),
            "star_fraction": round(star_frac, 4),
            "formation_snap": formation_snap,
            "major_mergers": major_mergers,
            "curvature": round(curvature, 5),
            "path_curvature": round(path_curv, 5),
            **pathways,
            "created_at": datetime.now().isoformat()
        }
        data.append(row)
    
    return data

def main():
    conn = init_db()
    halos = generate_realistic_halos(400)
    print(f"Generating {len(halos)} realistic synthetic halos...")
    
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
    print(f"Database updated: {DB_PATH} ({len(halos)} rows)")

if __name__ == "__main__":
    main()