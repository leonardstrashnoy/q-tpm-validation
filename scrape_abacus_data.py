#!/usr/bin/env python3
"""
Experimental scraper for AbacusSummit public halo data.
AbacusSummit has some publicly available small catalogs.
"""

from playwright.sync_api import sync_playwright

from scrape_utils import download_file, safe_dest

DATA_DIR = "abacus_data"
TARGET_SITES = [
    "https://abacussummit.readthedocs.io/",
    "https://github.com/abacusorg/AbacusSummit",
]


def main():
    Path(DATA_DIR).mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        all_links = []
        for site in TARGET_SITES:
            print(f"\nVisiting: {site}")
            try:
                page.goto(site, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=10000)
                links = page.eval_on_selector_all(
                    "a[href]",
                    """els => els.map(e => e.href).filter(h =>
                        h.match(/\.(hdf5|h5|txt|csv|fits)$/i) ||
                        h.includes('halo') || h.includes('subhalo')
                    )"""
                )
                all_links.extend(links)
            except Exception as e:
                print(f"Error: {e}")

        browser.close()

    print(f"\nFound {len(all_links)} candidate links")
    for link in all_links[:10]:
        print("  -", link)

    success = 0
    for link in all_links[:4]:
        dest = safe_dest(DATA_DIR, link)
        if dest is None:
            continue
        if download_file(link, dest, max_size_mb=30):
            success += 1
            if success >= 1:
                break

    if success == 0:
        print("\nNo small AbacusSummit files found automatically.")


if __name__ == "__main__":
    main()