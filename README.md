# Q-TPM 4D Block Space Validation

Validation pipeline for Rodgers' Quantum-Enhanced Throughput Model (Q-TPM) using cosmological simulation data (dark matter halo merger trees) as a proxy for ethical decision "worldlines".

## Core Idea

Treat dark-matter halo merger trees as 4D block-space worldlines. Map the six ethical pathways from Q-TPM onto measurable halo properties to look for signatures of superposition, interference, decoherence, and collapse.

## The Six Ethical Pathways & Halo Proxies

| Pathway       | Ethical Logic      | Halo Proxy                              | Key Fields                     | Interpretation |
|---------------|--------------------|-----------------------------------------|--------------------------------|----------------|
| **Expedient**     | Egoism             | Rapid recent mass growth + isolation    | `recent_growth`, `local_density` | Selfish/fast accretion |
| **Ruling-guide**  | Deontology         | Strict merger mass-ratio rules          | `major_mergers`                | Follows rigid thresholds |
| **Analytical**    | Utilitarianism     | Maximum stellar mass conversion         | `star_fraction`                | Maximizes "output" |
| **Revisionist**   | Relativism         | High variance / context dependence      | `curvature`, `local_density`   | Environment-sensitive |
| **Value-driven**  | Virtue ethics      | Early assembly + late quiescence        | `formation_snap`               | Strong "character" |
| **Global**        | Ethics of care     | Environmental interaction & satellites  | `major_mergers`, `local_density` | Nurtures surroundings |

## Dashboard Tabs

- **Overview** — High-level KPIs, pathway activation rates, curvature vs density scatter.
- **Pathway Analysis** — Correlations between pathways + mass-quartile distributions.
- **Proposition Validation** — Formal tests of the five Q-TPM propositions using live SQL queries.

## Datasets

Three datasets are available in both the Streamlit app and the static dashboard:

| Dataset | Source | Halos | Notes |
|---------|--------|-------|-------|
| **Synthetic** | `qtpm_validator_lite.py` | 400 | All six pathways + curvature; fully reproducible (`seed=42`) |
| **CAMELS · IllustrisTNG LH_0** | Subfind HDF5, z=0 | 15,712 subhalos | Real data; only `analytical` + `global` derivable (single snapshot, no merger trees) |
| **Bolshoi-P · Rockstar hlist** | consistent-trees hlist, z≈0 | 1,328-halo sample | DM-only (no stellar mass); `value_driven`, `expedient`, `global` lit; others NULL |

## Quick Start

```bash
source .venv/bin/activate

# Streamlit app (interactive)
streamlit run app.py

# Regenerate synthetic DB (optional)
python qtpm_validator_lite.py

# Regenerate static site data
python export_data.py
python -m http.server -d site 8000   # preview at http://localhost:8000
```

The app auto-creates `qtpm_validation.db` with 400 synthetic halos on first run.

## Files

| File | Purpose |
|------|---------|
| `qtpm_validator_lite.py` | Synthetic halo generator; `PATHWAY_RULES`; writes `qtpm_validation.db` |
| `app.py` | Streamlit dashboard (3 tabs, dataset selector, proposition tests) |
| `export_data.py` | Regenerates `site/data.json` (and `data_camels.json`, `data_bolshoi.json`) for the static site |
| `analyze_propositions.sql` | Five formal proposition queries (run in-browser via sql.js) |
| `qtpm_camels.py` | Real-data validator: CAMELS Subfind HDF5 → `qtpm_camels.db` |
| `qtpm_bolshoi.py` | Real-data validator: Rockstar hlist → `qtpm_bolshoi.db` |
| `qtpm_tng_real.py` | IllustrisTNG API validator → `qtpm_tng_real.db` |
| `qtpm_cosmosim.py` | CosmoSim HDF5 validator → `qtpm_cosmosim.db` |
| `scrape_camels_data.py` | Playwright scraper → `camels_data/` |
| `scrape_halo_data.py` | Playwright scraper → `bolshoi_data/` |
| `scrape_abacus_data.py` | Playwright scraper → `abacus_data/` |
| `download_from_hf.py` | Hugging Face downloader → `hf_data/` |
| `scrape_utils.py` | Shared download helpers |
| `site/` | Static dashboard (Plotly.js + sql.js); published to here.now |

## Deployment

- **Streamlit Cloud:** pushing to `main` auto-redeploys the app (`.streamlit/config.toml` sets the dark theme).
- **Static site (here.now):** live at `https://queued-voyage-cbzb.here.now/`. Republish with:
  ```bash
  bash ~/.claude/skills/here-now/scripts/publish.sh site --slug queued-voyage-cbzb
  ```

---

*Q-TPM Validation · Synthetic + CAMELS + Bolshoi-P · v0.5*
