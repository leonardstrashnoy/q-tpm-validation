#!/usr/bin/env python3
"""
Export the deterministic synthetic halo dataset to site/data.json
for the static here.now dashboard.

Generation logic mirrors app.py exactly (np.random.seed(42), same
distributions and PATHWAY_RULES) so the static site shows identical
data to the Streamlit app. Run this whenever the rules change.
"""

import json
from pathlib import Path

import numpy as np

OUT_PATH = Path("site/data.json")
N_HALOS = 400

# Kept in sync with app.py / qtpm_validator_lite.py
PATHWAY_RULES = {
    "expedient": lambda r, d: r > 0.22 and d < 1.2,
    "ruling_guide": lambda m: m <= 2,
    "analytical": lambda s: s > 0.035,
    "revisionist": lambda c: c > 0.085,
    "value_driven": lambda f: f < 38,
    "global": lambda m, d: m > 5 or d > 2.8,
}

PATHWAY_COLS = list(PATHWAY_RULES.keys())


def generate_halos():
    np.random.seed(42)
    rows = []
    for i in range(N_HALOS):
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

        rows.append({
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
        })
    return rows


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    halos = generate_halos()
    payload = {
        "pathway_cols": PATHWAY_COLS,
        "halos": halos,
    }
    OUT_PATH.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"Wrote {len(halos)} halos to {OUT_PATH} ({OUT_PATH.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
