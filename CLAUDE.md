# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Validation pipeline for Rodgers' Quantum-Enhanced Throughput Model (Q-TPM). It treats dark-matter halo merger trees as 4D "block-space worldlines" and maps six ethical pathways (Egoism, Deontology, Utilitarianism, Relativism, Virtue ethics, Ethics of care) onto measurable halo properties to test for superposition/interference/collapse signatures. See `hermes.md` and `README.md` for the conceptual mapping; the project is currently driven by **synthetic** data, with real-simulation ingestion partially built.

## Environment & commands

Uses a local `.venv` (Python 3.9), **not** conda. `requirements.txt` only covers the Streamlit app (`streamlit plotly pandas numpy`); the scrapers additionally need `requests` and `playwright` (+ `playwright install chromium`), and the CAMELS validator needs `h5py` + `scipy`.

```bash
source .venv/bin/activate

python qtpm_validator_lite.py     # (re)generate qtpm_validation.db with 400 synthetic halos
streamlit run app.py              # launch the Streamlit dashboard (auto-creates the DB on first run)

python export_data.py             # regenerate site/data.json for the static dashboard
python -m http.server -d site 8000  # preview the static site locally

# Real-data ingestion (incomplete; see "Real-data pipeline" below)
python scrape_<halo|camels|abacus>_data.py   # Playwright scrapers -> *_data/ dirs
python download_from_hf.py                    # Hugging Face fetch -> hf_data/
python qtpm_<bolshoi|camels|...>.py           # load a *_data/ dir -> qtpm_<source>.db
```

There is **no test suite** and no linter configured. To verify the static site end-to-end, serve `site/` and drive it with Playwright (the venv already has it) — that's how regressions in the JS/sql.js logic are caught.

## Architecture: the `worldlines` table is the contract

Every entry point converges on a single 18-column SQLite table named `worldlines` (`halo_id` PK, halo properties, six 0/1 pathway flags, `created_at`). **This schema is duplicated verbatim** in `qtpm_validator_lite.py`, `app.py`, and each `qtpm_<source>.py` validator — there is no shared schema module. Changing a column means editing every `CREATE TABLE` and every `INSERT OR REPLACE`.

Three pipelines feed/consume it:

1. **Synthetic (primary):** `qtpm_validator_lite.py` → `qtpm_validation.db` → `app.py` (Streamlit). `np.random.seed(42)` makes the 400 halos fully reproducible.
2. **Static mirror:** `export_data.py` → `site/data.json` → `site/index.html` (published to here.now). The HTML is a single-page port of the three Streamlit tabs using plotly.js, an in-browser pathway filter, and **sql.js (SQLite-WASM)** to run `analyze_propositions.sql` verbatim in the browser.
3. **Real-data (incomplete):** Playwright scrapers / HF downloader populate `*_data/` dirs; each `qtpm_<source>.py` loads a dir into its **own** `qtpm_<source>.db`. `scrape_utils.py` holds the shared download helpers.

### Cross-file invariants to preserve

- **`PATHWAY_RULES` is duplicated** (identical lambdas) in `qtpm_validator_lite.py`, `app.py`, and `export_data.py`. They must stay in sync or the synthetic data, the Streamlit pathway flags, and the static `data.json` will silently disagree.
- **`export_data.py` must mirror `app.py`'s generation exactly** (same seed, distributions, rounding). It regenerates the data independently rather than reading the DB, so any change to one generator must be mirrored in the other to keep the static site faithful.
- **`global` is a column name.** It is a reserved word in some SQL engines — this is why the static site uses sql.js (SQLite, which tolerates it) rather than DuckDB. Quote it if you ever target another engine.
- **Real-data validators differ in maturity.** `qtpm_camels.py` does a *real* Subfind-catalog mapping: it reads `Group/`+`Subhalo/` HDF5 (units 1e10 M⊙/h, type 4 = stars), computes a KD-tree local density, and assigns pathway flags by **percentile** within the loaded population (synthetic thresholds don't transfer to physical units). Merger-history fields (`recent_growth`, `major_mergers`, `formation_snap`, `curvature`) and the pathways depending on them are written **NULL**, not faked — only `analytical` (full) and `global` (density branch, partial) are real from a single snapshot. By contrast `qtpm_bolshoi.py` still emits **placeholder constants** for derived fields (flagged TODO) — don't interpret its output as a real result.
- **Python 3.9 venv:** `X | None` annotations require `from __future__ import annotations` (see `scrape_utils.py`).

## Deployment

- **Streamlit Cloud:** pushing to `main` auto-redeploys the app (`.streamlit/config.toml` sets the dark theme).
- **Static site (here.now):** publish with `bash ~/.claude/skills/here-now/scripts/publish.sh site --slug <slug>`. The live demo is `https://queued-voyage-cbzb.here.now/`. `.herenow/` (local state/credential cache) is gitignored.

## Data files

`*.db` and the simulation data dirs (`abacus_data/`, `bolshoi_data/`, `camels_data/`, `cosmosim_data/`, `hf_data/`) are gitignored; `site/data.json` is committed so the static site is self-contained.
