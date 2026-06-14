#!/usr/bin/env python3
"""
Shared helpers for the cosmology data scrapers.

Previously each scraper carried its own near-identical `download_file`
with two bugs: `stream=True` was ignored (the whole body was loaded via
`r.content`), and the size cap relied on a HEAD `content-length` that many
servers omit — letting large files through. This version enforces the cap
*during* the streamed download.
"""

from __future__ import annotations

from pathlib import Path
import requests

HEADERS = {
    # Some astro data servers reject the default python-requests UA.
    "User-Agent": "Mozilla/5.0 (compatible; qtpm-scraper/1.0; +https://here.now)",
}


def safe_dest(data_dir: str, url: str) -> Path | None:
    """Build a destination path from a URL, or None if it has no real filename."""
    name = url.split("?")[0].rstrip("/").rsplit("/", 1)[-1]
    if not name or "." not in name:
        return None
    return Path(data_dir) / name


def download_file(url: str, dest: Path, max_size_mb: int = 30) -> bool:
    """Stream a file to `dest`, aborting if it exceeds `max_size_mb`.

    The size limit is enforced while streaming, so it works even when the
    server reports no Content-Length.
    """
    max_bytes = max_size_mb * 1024 * 1024
    try:
        with requests.get(url, stream=True, timeout=120, headers=HEADERS) as r:
            r.raise_for_status()

            # Fast path: trust Content-Length if present.
            declared = int(r.headers.get("content-length", 0))
            if declared > max_bytes:
                print(f"Skipping large file ({declared/1024/1024:.1f} MB): {url}")
                return False

            written = 0
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    written += len(chunk)
                    if written > max_bytes:
                        print(f"Aborting oversized file (>{max_size_mb} MB): {url}")
                        f.close()
                        dest.unlink(missing_ok=True)
                        return False
                    f.write(chunk)

        print(f"Saved ({written/1024/1024:.1f} MB): {dest}")
        return True
    except Exception as e:
        print(f"Failed: {e}")
        dest.unlink(missing_ok=True)
        return False
