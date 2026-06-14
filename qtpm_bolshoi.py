#!/usr/bin/env python3
"""
Q-TPM Bolshoi Validator (Public Data, No API Key)

Includes a download helper using requests for any known direct public files.
"""

import os
import glob
import sqlite3
import pandas as pd
import requests
from datetime import datetime
from pathlib import Path

DATA_DIR = "bolshoi_data/"
DB_PATH = "qtpm_bolshoi.db"

# Known small public Bolshoi-related files (update URLs when better ones are found)
PUBLIC_URLS = [
    # Example placeholder - replace with real direct links when available
    # "https://example.com/bolshoi_small_sample.txt",
]


def download_public_data():
    """Try to download any known public small Bolshoi files."""
    Path(DATA_DIR).mkdir(exist_ok=True)
    downloaded = []

    for url in PUBLIC_URLS:
        filename = os.path.join(DATA_DIR, os.path.basename(url))
        if os.path.exists(filename):
            print(f"Already have: {filename}")
            continue
        try:
            print(f"Downloading {url} ...")
            r = requests.get(url, timeout=60, stream=True)
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            downloaded.append(filename)
            print(f"Saved: {filename}")
        except Exception as e:
            print(f"Failed to download {url}: {e}")

    if not downloaded and not PUBLIC_URLS:
        print("No direct public URLs configured yet.")
        print("Please manually download Bolshoi catalogs into bolshoi_data/")

    return downloaded


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


def load_bolshoi_data():
    files = glob.glob(os.path.join(DATA_DIR, "*.txt")) + \
            glob.glob(os.path.join(DATA_DIR, "*.csv")) + \
            glob.glob(os.path.join(DATA_DIR, "*.fits"))

    if not files:
        print(f"No Bolshoi data files found in {DATA_DIR}")
        return pd.DataFrame()

    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f, sep=r"\s+", comment="#")
            dfs.append(df)
        except Exception as e:
            print(f"Could not read {f}: {e}")

    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def map_to_worldlines(df):
    # NOTE: Most derived fields below (recent_growth, major_mergers, curvature,
    # star_fraction, etc.) are PLACEHOLDER CONSTANTS, not real measurements.
    # Until proper column mapping is implemented they are identical for every
    # halo and must NOT be interpreted as validation results. See README TODO.
    if df.empty:
        return []

    has_id = any(c in df.columns for c in ("id", "ID"))
    if not has_id:
        print("WARNING: no id/ID column found — assigning sequential halo_ids.")

    records = []
    for i, (_, row) in enumerate(df.iterrows()):
        try:
            mass = float(row.get("mvir", row.get("Mvir", 1e12)))
            stellar_mass = mass * 0.02

            # Fall back to a unique sequential id so rows don't collide on the
            # halo_id PRIMARY KEY (which would silently drop all but one row).
            halo_id = int(row.get("id", row.get("ID", i))) if has_id else i

            record = {
                "halo_id": halo_id,
                "simulation": "Bolshoi",
                "mass": round(mass, 2),
                "stellar_mass": round(stellar_mass, 2),
                "local_density": 1.0,
                "recent_growth": 0.1,
                "star_fraction": 0.02,
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
    print("=== Bolshoi Public Data Helper ===")
    download_public_data()

    conn = init_db()
    df = load_bolshoi_data()

    if df.empty:
        print("No data loaded. Add files to bolshoi_data/ and re-run.")
        return

    print(f"Loaded {len(df)} halos")
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