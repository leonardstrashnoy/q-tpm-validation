#!/usr/bin/env python3
"""
Improved Playwright-based scraper for CAMELS public data.
Better directory exploration + small file focus.
"""

from playwright.sync_api import sync_playwright

from scrape_utils import download_file, safe_dest

DATA_DIR = "camels_data"
TARGET_SITES = [
    "https://camels.readthedocs.io/en/latest/Data.html",
    "https://www.camels-simulations.org/",
]


def get_links_from_page(page):
    links = page.eval_on_selector_all(
        "a[href]",
        """els => els.map(e => {
            const href = e.href;
            const text = (e.innerText || '').toLowerCase();
            return {href, text};
        }).filter(item =>
            item.href.match(/\.(hdf5|h5|txt|csv)$/i) ||
            item.text.includes('halo') ||
            item.text.includes('subhalo') ||
            item.href.includes('camels')
        )"""
    )
    return [item["href"] for item in links]


def explore_directory(page, url: str, depth: int = 0, max_depth: int = 2):
    if depth > max_depth:
        return []

    print(f"{'  ' * depth}Exploring: {url}")
    try:
        page.goto(url, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        return []

    files = get_links_from_page(page)

    # Look for subdirectories
    dir_links = page.eval_on_selector_all(
        "a[href]",
        """els => els.map(e => e.href).filter(h =>
            h.endsWith('/') && !h.includes('?') &&
            !h.includes('parent') && !h.includes('..')
        )"""
    )

    for d in dir_links[:3]:
        if "camels" in d.lower() or "data" in d.lower() or "halo" in d.lower():
            files += explore_directory(page, d, depth + 1, max_depth)

    return list(set(files))


def main():
    Path(DATA_DIR).mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        all_files = []
        for site in TARGET_SITES:
            print(f"\n=== Starting at {site} ===")
            files = explore_directory(page, site)
            all_files.extend(files)

        browser.close()

    print(f"\nFound {len(all_files)} potential files")
    for f in all_files[:12]:
        print("  -", f)

    success = 0
    for link in all_files[:5]:
        dest = safe_dest(DATA_DIR, link)
        if dest is None:
            continue
        if download_file(link, dest, max_size_mb=30):
            success += 1
            if success >= 2:
                break

    if success == 0:
        print("\nNo small direct CAMELS files found automatically.")


if __name__ == "__main__":
    main()