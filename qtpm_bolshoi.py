#!/usr/bin/env python3
"""
Q-TPM Bolshoi Validator (Public Data, No API Key)

Reads real Rockstar / consistent-trees ``hlist_*.list`` halo catalogs
(as published for Bolshoi / MultiDark on skiesanduniverses.org) and maps the
measurable columns onto the Q-TPM worldlines schema.

What is real vs. unavailable from a Rockstar hlist
--------------------------------------------------
An hlist is consistent-trees output, so unlike a single Subfind snapshot it
carries some merger-history columns — but Bolshoi is dark-matter-only, so it
has no stellar mass.

  Real (computed here):   mass (mvir), local_density, recent_growth
                          (specific accretion from an Acc_Rate* column),
                          last-major-merger timing (scale_of_last_MM)
  NULL (not in an hlist): stellar_mass, star_fraction (DM-only),
                          cumulative major_mergers count (needs a tree walk),
                          curvature, path_curvature

Pathway flags assigned where their inputs exist (percentile-calibrated, since
synthetic thresholds don't transfer to physical units):

  value_driven  -> scale_of_last_MM (early last major merger = quiescent)
  expedient     -> recent_growth high AND local_density low (rapid + isolated)
  global        -> local_density branch only (partial)
  analytical, ruling_guide, revisionist -> NULL

Usage
-----
1. Download a Rockstar hlist into ``bolshoi_data/`` (the scraper targets small
   public files; full hlists are large).
2. Run this script. It writes ``qtpm_bolshoi.db``.
"""

import glob
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = "bolshoi_data/"
DB_PATH = "qtpm_bolshoi.db"

# Bolshoi cosmology h (H0/100); hlist masses are Msun/h, positions Mpc/h.
BOLSHOI_H = 0.70
MASS_MSUN_PER_H = 1.0
DENSITY_RADIUS_MPC_H = 5.0  # comoving Mpc/h sphere for the local-density estimate
PCTL_HIGH = 67
PCTL_LOW = 33


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


def parse_hlist_header(path):
    """Parse the leading ``#`` header of an hlist into a name -> column-index map.

    hlist headers look like ``#scale(0) id(1) ... mvir(10) ... Acc_Rate_Inst(43)``.
    Names are lower-cased for robust lookup across catalog versions.
    """
    with open(path) as f:
        first = f.readline()
    if not first.startswith("#"):
        return {}
    cols = {}
    for name, idx in re.findall(r"([^\s(]+)\((\d+)\)", first):
        cols[name.lower()] = int(idx)
    return cols


def _find_accretion_col(colmap):
    """Pick the first available Acc_Rate* column (instantaneous or windowed)."""
    for name in colmap:
        if name.startswith("acc_rate"):
            return colmap[name]
    return None


def local_number_density(pos, boxsize=None, radius=DENSITY_RADIUS_MPC_H):
    """Neighbours within `radius` (comoving Mpc/h) -> number density."""
    from scipy.spatial import cKDTree

    n = len(pos)
    if n == 0:
        return np.zeros(0)
    tree = cKDTree(pos, boxsize=boxsize)
    counts = tree.query_ball_point(pos, r=radius, return_length=True)
    volume = (4.0 / 3.0) * np.pi * radius ** 3
    return (np.asarray(counts) - 1) / volume  # exclude self


def load_bolshoi_data():
    """Load Rockstar hlist catalogs in DATA_DIR into one physical DataFrame."""
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*.list")) +
                   glob.glob(os.path.join(DATA_DIR, "hlist*.txt")) +
                   glob.glob(os.path.join(DATA_DIR, "*.csv")))
    if not files:
        print(f"No Rockstar hlist files found in {DATA_DIR}")
        return pd.DataFrame()

    frames = []
    for path in files:
        colmap = parse_hlist_header(path)
        if "mvir" not in colmap or "x" not in colmap:
            print(f"  {os.path.basename(path)}: no recognisable hlist header — skipping")
            continue

        acc_idx = _find_accretion_col(colmap)
        wanted = {"mvir": colmap["mvir"], "x": colmap["x"],
                  "y": colmap["y"], "z": colmap["z"]}
        if "id" in colmap:
            wanted["id"] = colmap["id"]
        if "scale_of_last_mm" in colmap:
            wanted["scale_of_last_mm"] = colmap["scale_of_last_mm"]
        if acc_idx is not None:
            wanted["acc_rate"] = acc_idx

        raw = pd.read_csv(path, sep=r"\s+", comment="#", header=None,
                          usecols=list(wanted.values()))
        # Map original column indices back to friendly names.
        idx_to_name = {v: k for k, v in wanted.items()}
        raw.columns = [idx_to_name[c] for c in raw.columns]

        pos = raw[["x", "y", "z"]].to_numpy(dtype=float)
        density = local_number_density(pos)

        frame = pd.DataFrame({
            "halo_id": raw["id"].astype("int64") if "id" in raw else np.arange(len(raw)),
            "mass": raw["mvir"].to_numpy(dtype=float) / BOLSHOI_H,  # Msun/h -> Msun
            "local_density": density,
        })
        if "acc_rate" in raw:
            # Specific accretion rate (1/yr); h cancels (both Msun/h). NULL if <=0.
            with np.errstate(divide="ignore", invalid="ignore"):
                spec = raw["acc_rate"].to_numpy(dtype=float) / raw["mvir"].to_numpy(dtype=float)
            frame["recent_growth"] = np.where(np.isfinite(spec), spec, np.nan)
        if "scale_of_last_mm" in raw:
            frame["last_mm_scale"] = raw["scale_of_last_mm"].to_numpy(dtype=float)

        frames.append(frame)
        print(f"  {os.path.basename(path)}: {len(frame)} halos"
              f"{' (with accretion)' if 'acc_rate' in raw else ''}")

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def map_to_worldlines(df):
    """Map real Rockstar columns to the worldlines schema with percentile flags.

    Merger-history-dependent fields that an hlist does not provide are written
    NULL rather than fabricated.
    """
    if df.empty:
        return []
    df = df[df["mass"] > 0].copy()
    if df.empty:
        return []

    dens = df["local_density"].to_numpy(dtype=float)
    rg = df["recent_growth"].to_numpy(dtype=float) if "recent_growth" in df else np.full(len(df), np.nan)
    mm = df["last_mm_scale"].to_numpy(dtype=float) if "last_mm_scale" in df else np.full(len(df), np.nan)

    def pctl(arr, q):
        return np.nanpercentile(arr, q) if np.isfinite(arr).any() else np.nan

    thr_dens_hi = pctl(dens, PCTL_HIGH)
    thr_dens_lo = pctl(dens, PCTL_LOW)
    thr_rg_hi = pctl(rg, PCTL_HIGH)
    thr_mm_lo = pctl(mm, PCTL_LOW)

    def finite(*vals):
        return all(np.isfinite(v) for v in vals)

    records = []
    for _, row in df.iterrows():
        density = float(row["local_density"])
        growth = float(row.get("recent_growth", np.nan))
        last_mm = float(row.get("last_mm_scale", np.nan))

        # value_driven: an early last major merger (low scale) -> late quiescence.
        value_driven = int(last_mm < thr_mm_lo) if finite(last_mm, thr_mm_lo) else None
        # expedient: rapid recent growth AND isolation (low local density).
        expedient = (int(growth > thr_rg_hi and density < thr_dens_lo)
                     if finite(growth, thr_rg_hi, density, thr_dens_lo) else None)
        # global: dense-environment branch only (satellite/merger branch needs trees).
        glob_flag = int(density > thr_dens_hi) if finite(density, thr_dens_hi) else None

        records.append({
            "halo_id": int(row["halo_id"]),
            "simulation": "Bolshoi",
            "mass": round(float(row["mass"]), 2),
            "stellar_mass": None,               # DM-only catalog
            "local_density": round(density, 8) if np.isfinite(density) else None,
            "recent_growth": round(growth, 12) if np.isfinite(growth) else None,
            "star_fraction": None,              # DM-only catalog
            "formation_snap": None,             # needs the full assembly history
            "major_mergers": None,              # cumulative count needs a tree walk
            "curvature": None,                  # needs merger tree
            "path_curvature": None,             # needs merger tree
            "expedient": expedient,
            "ruling_guide": None,               # needs major_mergers count
            "analytical": None,                 # needs stellar mass (DM-only)
            "revisionist": None,                # needs curvature
            "value_driven": value_driven,
            "global": glob_flag,                # density branch only (partial)
            "created_at": datetime.now().isoformat(),
        })
    return records


def main():
    print("=== Bolshoi Rockstar hlist Validator ===")
    Path(DATA_DIR).mkdir(exist_ok=True)
    conn = init_db()
    df = load_bolshoi_data()

    if df.empty:
        print("No data loaded. Add Rockstar hlist files to bolshoi_data/ and re-run.")
        return

    print(f"Loaded {len(df)} halos")
    records = map_to_worldlines(df)
    if records:
        def n(flag):
            return sum(1 for r in records if r[flag] == 1)
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
        print(f"  value_driven: {n('value_driven')}  expedient: {n('expedient')}  "
              f"global (partial): {n('global')}")
        print("  stellar_mass/analytical NULL (DM-only); major_mergers NULL "
              "(needs a tree walk).")

    conn.close()


if __name__ == "__main__":
    main()
