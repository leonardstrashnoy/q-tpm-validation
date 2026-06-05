# Q-TPM 4D Block Space Validation

Validation pipeline for Rodgers’ Quantum-Enhanced Throughput Model using cosmological simulation data as a proxy for ethical decision worldlines.

## Current Status (Synthetic Mode)

- Improved synthetic halo generator with realistic distributions
- Enhanced Streamlit dashboard with proposition validation
- 400 synthetic halos in database

## Quick Start

```bash
source .venv/bin/activate
python qtpm_validator_lite.py          # Regenerate data
streamlit run app.py                   # Launch dashboard
```

## Files

- `qtpm_validator_lite.py` — Improved synthetic data generator
- `app.py` — Enhanced interactive dashboard
- `analyze_propositions.sql` — Proposition queries
- `qtpm_validation.db` — Current database (400 halos)

## Future

When TNG or CosmoSim API access is stable, we can switch to real data using `qtpm_tng_real.py` or `qtpm_cosmosim.py`.