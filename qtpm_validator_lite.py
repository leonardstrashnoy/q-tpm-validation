#!/usr/bin/env python3
"""
Improved Q-TPM Synthetic Data Generator

Creates realistic dark-matter halo distributions for testing the
Quantum-Enhanced Throughput Model (Q-TPM) ethical pathway mappings.
"""

import sqlite3
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Callable

DB_PATH = "qtpm_validation.db"

# Shared pathway assignment rules (also used by app.py)
PATHWAY_RULES: Dict[str, Callable] = {
    "expedient": lambda r, d: r > 0.22 and d < 1.2,
    "ruling_guide": lambda m: m <= 2,
    "analytical": lambda s: s > 0.035,
    "revisionist": lambda c: c > 0.085,
    "value_driven": lambda f: f < 38,
    "global": lambda m, d: m > 5 or d > 2.8,
}


def init_db() -> sqlite3.Connection:
    """Create the worldlines table if it does not exist."""
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


def generate_realistic_halos(n: int = 400) -> List[Dict[str, Any]]:
    """
    Generate n synthetic halos with realistic cosmological distributions.

    Returns a list of row dictionaries ready for database insertion.
    """
    data: List[Dict[str, Any]] = []
    np.random.seed(42)

    for i in range(n):
        log_mass = np.random.normal(11.5, 1.2)
        mass = 10 ** log_mass

        star_frac = max(0.008, min(0.09, np.random.beta(2, 5) * 0.12))
        stellar = mass * star_frac

        local_density = max(0.1, np.random.lognormal(0.3, 0.8))
        recent_growth = max(0.01, np.random.beta(2, 4) * 0.5)
        formation_snap = int(np.random.beta(1.5, 2.5) * 80 + 10)
        major_mergers = int(np.random.poisson(3.2))
        curvature = max(0.01, np.random.beta(2, 6) * 0.22)
        path_curv = max(0.005, np.random.beta(2, 7) * 0.15)

        pathways = {
            "expedient": int(PATHWAY_RULES["expedient"](recent_growth, local_density)),
            "ruling_guide": int(PATHWAY_RULES["ruling_guide"](major_mergers)),
            "analytical": int(PATHWAY_RULES["analytical"](star_frac)),
            "revisionist": int(PATHWAY_RULES["revisionist"](curvature)),
            "value_driven": int(PATHWAY_RULES["value_driven"](formation_snap)),
            "global": int(PATHWAY_RULES["global"](major_mergers, local_density)),
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


def main() -> None:
    """Generate and persist 400 synthetic halos to the database."""
    conn = init_db()
    halos = generate_realistic_halos(400)
    print(f"Generating {len(halos)} realistic synthetic halos...")

    conn.executemany("""
        INSERT OR REPLACE INTO worldlines VALUES
        (:halo_id, :snapshot, :mass, :stellar_mass, :local_density,
         :recent_growth, :star_fraction, :formation_snap, :major_mergers,
         :curvature, :path_curvature,
         :expedient, :ruling_guide, :analytical, :revisionist,
         :value_driven, :global, :created_at)
    """, halos)

    conn.commit()
    conn.close()
    print(f"Database updated: {DB_PATH} ({len(halos)} rows)")


if __name__ == "__main__":
    main()