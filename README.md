# Q-TPM 4D Block Space Validation

Validation pipeline for Rodgers’ Quantum-Enhanced Throughput Model (Q-TPM) using cosmological simulation data (dark matter halo merger trees) as a proxy for ethical decision "worldlines".

## Core Idea

Treat IllustrisTNG-style halo merger trees as 4D block-space worldlines. Map the six ethical pathways from Q-TPM onto measurable halo properties to look for signatures of superposition, interference, decoherence, and collapse.

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

## Quick Start

```bash
source .venv/bin/activate
python qtpm_validator_lite.py          # (optional) regenerate synthetic data
streamlit run app.py                   # launch interactive dashboard
```

The app auto-creates `qtpm_validation.db` with 400 realistic synthetic halos on first run.

## Files

- `qtpm_validator_lite.py` — Synthetic halo generator with realistic distributions + `PATHWAY_RULES`
- `app.py` — Streamlit dashboard (3 tabs + proposition tests)
- `analyze_propositions.sql` — The five formal proposition queries
- `qtpm_validation.db` — Current working database (400 halos)
- `.streamlit/config.toml` — Dark theme for Cloud deployment

## Future Work

- Real IllustrisTNG integration (`qtpm_tng_real.py`)
- CosmoSim / Uchuu / Bolshoi merger trees
- 4D worldline curvature visualization
- Interference / decoherence metrics

## Deployment

Pushes to `main` automatically trigger redeploy on Streamlit Community Cloud.

---

*Q-TPM Synthetic Validation v0.3*