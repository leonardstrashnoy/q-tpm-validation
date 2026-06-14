#!/usr/bin/env python3
"""
Download small halo datasets from Hugging Face.
Many cosmology simulations now have public datasets here.
"""

from pathlib import Path
import requests

from scrape_utils import download_file, HEADERS

DATA_DIR = "hf_data"
# Some known public cosmology-related datasets on HF
DATASETS = [
    "camels/CAMELS",
    "abacusorg/AbacusSummit",
]


def download_from_hf(dataset: str, max_files: int = 3):
    """Try to download small files from a Hugging Face dataset."""
    api_url = f"https://huggingface.co/api/datasets/{dataset}/tree/main"
    try:
        r = requests.get(api_url, timeout=30, headers=HEADERS)
        r.raise_for_status()
        files = r.json()
    except Exception as e:
        print(f"Failed to list {dataset}: {e}")
        return []

    downloaded = []
    for f in files:
        if f.get("type") != "file":
            continue
        if not any(ext in f["path"].lower() for ext in [".hdf5", ".h5", ".txt", ".csv"]):
            continue
        size_mb = f.get("size", 0) / 1024 / 1024
        if size_mb > 50:  # skip >50MB
            continue

        url = f"https://huggingface.co/datasets/{dataset}/resolve/main/{f['path']}"
        dest = Path(DATA_DIR) / f['path'].replace("/", "_")
        print(f"Downloading: {f['path']} ({size_mb:.1f} MB)")
        if download_file(url, dest, max_size_mb=50):
            downloaded.append(dest)
            if len(downloaded) >= max_files:
                break

    return downloaded


def main():
    Path(DATA_DIR).mkdir(exist_ok=True)
    print("Looking for small halo datasets on Hugging Face...\n")

    for ds in DATASETS:
        print(f"=== {ds} ===")
        files = download_from_hf(ds)
        if files:
            print(f"Downloaded {len(files)} files to {DATA_DIR}")
        else:
            print("No suitable small files found.\n")


if __name__ == "__main__":
    main()