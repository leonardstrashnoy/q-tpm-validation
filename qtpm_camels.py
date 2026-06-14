#!/usr/bin/env python3
"""
Q-TPM CAMELS Validator (Public Data, No API Key)

Reads real CAMELS / IllustrisTNG-format Subfind halo catalogs
(``fof_subhalo_tab_*.hdf5``) and maps the measurable subhalo properties
onto the Q-TPM worldlines schema.

What is real vs. unavailable from a SINGLE catalog snapshot
-----------------------------------------------------------
A Subfind group catalog is one snapshot, so it has no merger history.

  Real (computed here):   mass, stellar_mass, star_fraction, local_density
  NULL (need merger tree):recent_growth, formation_snap, major_mergers,
                          curvature, path_curvature

Pathway flags are therefore only assigned where their inputs exist:

  analytical    -> star_fraction (full)
  global        -> local_density branch only (partial; merger branch needs trees)
  expedient, ruling_guide, revisionist, value_driven -> NULL

Calibration
-----------
The synthetic ``PATHWAY_RULES`` thresholds are tuned to synthetic units and
do NOT transfer to physical CAMELS data. Flags are instead assigned by
PERCENTILE within the loaded population (top third = "high"), preserving the
intent of each rule while remaining distribution-independent.

Usage
-----
1. Download a CAMELS Subfind catalog (e.g. an IllustrisTNG/SIMBA LH box)
   into ``camels_data/``.
2. Run this script. It loads ``*.hdf5`` catalogs and writes ``qtpm_camels.db``.
"""

import glob
import os
import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd

DATA_DIR = "camels_data/"
DB_PATH = "qtpm_camels.db"

# Mass unit in Subfind catalogs is 1e10 Msun/h; positions are in ckpc/h.
MASS_UNIT_MSUN = 1e10
DENSITY_RADIUS_MPC = 2.0  # comoving sphere radius for the local-density estimate

# Percentile (0-100) above/below which a pathway flag fires, echoing the
# "high"/"low" intent of the original synthetic PATHWAY_RULES.
PCTL_HIGH = 67


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


def read_subfind_catalog(path):
    """Read one Subfind HDF5 catalog into physical per-subhalo arrays.

    Returns a dict with numpy arrays (mass, stellar_mass, star_fraction,
    pos in comoving Mpc) and the box size, or None if the file is not a
    recognisable Subfind catalog.
    """
    import h5py

    with h5py.File(path, "r") as hf:
        if "Subhalo" not in hf or "SubhaloMass" not in hf["Subhalo"]:
            print(f"  {os.path.basename(path)}: no Subhalo group — skipping")
            return None

        header = dict(hf["Header"].attrs) if "Header" in hf else {}
        h = float(header.get("HubbleParam", 1.0)) or 1.0
        boxsize_ckpc = float(header.get("BoxSize", 0.0))

        sub = hf["Subhalo"]
        total = np.asarray(sub["SubhaloMass"][:], dtype=np.float64)

        # Stellar mass = mass in particle type 4 (stars).
        if "SubhaloMassType" in sub:
            stellar = np.asarray(sub["SubhaloMassType"][:, 4], dtype=np.float64)
        else:
            stellar = np.full_like(total, np.nan)

        pos_ckpc = np.asarray(sub["SubhaloPos"][:], dtype=np.float64) \
            if "SubhaloPos" in sub else np.zeros((total.size, 3))

    # Convert to physical units: mass -> Msun, positions -> comoving Mpc.
    mass = total * MASS_UNIT_MSUN / h
    stellar_msun = stellar * MASS_UNIT_MSUN / h
    pos_mpc = pos_ckpc / 1000.0 / h
    boxsize_mpc = boxsize_ckpc / 1000.0 / h

    with np.errstate(divide="ignore", invalid="ignore"):
        star_fraction = np.where(total > 0, stellar / total, np.nan)

    return {
        "mass": mass,
        "stellar_mass": stellar_msun,
        "star_fraction": star_fraction,
        "pos": pos_mpc,
        "boxsize": boxsize_mpc,
    }


def local_number_density(pos_mpc, boxsize_mpc, radius=DENSITY_RADIUS_MPC):
    """Count neighbours within `radius` (comoving Mpc) -> number density.

    Uses a periodic KD-tree when the box size is known, so halos near an
    edge aren't spuriously under-dense.
    """
    from scipy.spatial import cKDTree

    n = len(pos_mpc)
    if n == 0:
        return np.zeros(0)
    boxsize = boxsize_mpc if boxsize_mpc and boxsize_mpc > 0 else None
    tree = cKDTree(pos_mpc, boxsize=boxsize)
    counts = tree.query_ball_point(pos_mpc, r=radius, return_length=True)
    volume = (4.0 / 3.0) * np.pi * radius ** 3
    return (np.asarray(counts) - 1) / volume  # exclude self


def load_camels_data():
    """Load every CAMELS catalog in DATA_DIR into one physical DataFrame."""
    hdf5_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.hdf5")) +
                        glob.glob(os.path.join(DATA_DIR, "*.h5")))
    text_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.txt")) +
                        glob.glob(os.path.join(DATA_DIR, "*.csv")))

    if not hdf5_files and not text_files:
        print(f"No CAMELS data files found in {DATA_DIR}")
        return pd.DataFrame()

    frames = []
    for f in hdf5_files:
        cat = read_subfind_catalog(f)
        if cat is None:
            continue
        density = local_number_density(cat["pos"], cat["boxsize"])
        frames.append(pd.DataFrame({
            "mass": cat["mass"],
            "stellar_mass": cat["stellar_mass"],
            "star_fraction": cat["star_fraction"],
            "local_density": density,
        }))
        print(f"  {os.path.basename(f)}: {len(cat['mass'])} subhalos")

    # Legacy plain-text fallback (no environment/units handling).
    for f in text_files:
        try:
            df = pd.read_csv(f, sep=r"\s+", comment="#")
            frames.append(df)
        except Exception as e:
            print(f"Could not read {f}: {e}")

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def map_to_worldlines(df):
    """Map real CAMELS columns to the worldlines schema with percentile flags.

    Only `analytical` (star_fraction) and `global` (local_density branch) are
    assignable from a single catalog; every merger-history field and its
    pathway flag is left NULL rather than fabricated.
    """
    if df.empty:
        return []

    # Keep only physical subhalos with a defined star fraction.
    df = df[df.get("mass", pd.Series(dtype=float)) > 0].copy()
    if df.empty:
        return []

    sf = df["star_fraction"].to_numpy(dtype=float)
    dens = df["local_density"].to_numpy(dtype=float) if "local_density" in df else np.full(len(df), np.nan)

    thr_analytical = np.nanpercentile(sf, PCTL_HIGH) if np.isfinite(sf).any() else np.nan
    thr_global = np.nanpercentile(dens, PCTL_HIGH) if np.isfinite(dens).any() else np.nan

    def flag(value, thr):
        if not np.isfinite(value) or not np.isfinite(thr):
            return None
        return int(value > thr)

    records = []
    for i, (_, row) in enumerate(df.iterrows()):
        mass = float(row["mass"])
        stellar = float(row.get("stellar_mass", np.nan))
        star_frac = float(row.get("star_fraction", np.nan))
        density = float(row.get("local_density", np.nan))

        records.append({
            "halo_id": i,                       # unique subhalo index -> no PK collision
            "simulation": "CAMELS",
            "mass": round(mass, 2),
            "stellar_mass": round(stellar, 2) if np.isfinite(stellar) else None,
            "local_density": round(density, 6) if np.isfinite(density) else None,
            "recent_growth": None,              # needs merger tree
            "star_fraction": round(star_frac, 5) if np.isfinite(star_frac) else None,
            "formation_snap": None,             # needs merger tree
            "major_mergers": None,              # needs merger tree
            "curvature": None,                  # needs merger tree
            "path_curvature": None,             # needs merger tree
            "expedient": None,                  # needs recent_growth
            "ruling_guide": None,               # needs major_mergers
            "analytical": flag(star_frac, thr_analytical),
            "revisionist": None,                # needs curvature
            "value_driven": None,               # needs formation_snap
            "global": flag(density, thr_global),  # density branch only (partial)
            "created_at": datetime.now().isoformat(),
        })
    return records


def main():
    conn = init_db()
    print(f"Loading CAMELS catalogs from {DATA_DIR} ...")
    df = load_camels_data()

    if df.empty:
        print("No data loaded. Please download CAMELS catalogs into camels_data/")
        return

    print(f"Loaded {len(df)} subhalos")
    records = map_to_worldlines(df)
    if records:
        n_analytical = sum(1 for r in records if r["analytical"] == 1)
        n_global = sum(1 for r in records if r["global"] == 1)
        conn.executemany("""
            INSERT OR REPLACE INTO worldlines VALUES
            (:halo_id, :simulation, :mass, :stellar_mass, :local_density,
             :recent_growth, :star_fraction, :formation_snap, :major_mergers,
             :curvature, :path_curvature,
             :expedient, :ruling_guide, :analytical, :revisionist,
             :value_driven, :global, :created_at)
        """, records)
        conn.commit()
        print(f"Inserted {len(records)} subhalos into {DB_PATH}")
        print(f"  analytical flagged: {n_analytical}  |  global (partial): {n_global}")
        print("  recent_growth / formation_snap / major_mergers left NULL "
              "(need a merger tree).")

    conn.close()


if __name__ == "__main__":
    main()
