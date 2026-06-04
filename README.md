# Q-TPM 4D Block Space Validation

Validation pipeline for Rodgers’ Quantum-Enhanced Throughput Model using cosmological simulation data (IllustrisTNG) as a proxy for ethical decision worldlines.

## Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate     # macOS/Linux
# .venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

## Run the Pipeline

```bash
# Generate synthetic data + database
python qtpm_validator_lite.py

# Run proposition analysis
sqlite3 qtpm_validation.db < analyze_propositions.sql

# Launch web dashboard
streamlit run app.py
```

## Files

- `qtpm_validator_lite.py` — Synthetic data generator + SQLite
- `app.py` — Streamlit dashboard
- `analyze_propositions.sql` — Proposition validation queries
- `qtpm_validation.db` — Results database
- `hermes.md` — Project notes and mapping

## Next

Replace synthetic data with real IllustrisTNG files in the `trees/` folder and switch to `qtpm_tng_validator.py`.