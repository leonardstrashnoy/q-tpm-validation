# Hermes.md — Q-TPM 4D Block Space Validation

**Project**: Validating Rodgers’ Quantum-Enhanced Throughput Model (Q-TPM) using cosmological simulation data as a proxy for ethical decision worldlines.

**Core Idea**
Treat dark matter halo merger trees in IllustrisTNG as 4D worldlines. Map the six TPM ethical pathways onto measurable halo properties to test superposition, interference, decoherence, and collapse signatures predicted by the block-space model.

## Six Ethical Pathways → Halo Property Mapping

| Pathway       | Ethical Logic       | Halo Proxy                              | TNG Fields                          | Rationale |
|---------------|---------------------|-----------------------------------------|-------------------------------------|---------|
| Expedient     | Egoism              | Rapid recent mass growth + isolation    | `SubhaloMass`, recent ΔM, isolation | Selfish, fast accretion |
| Ruling-guide  | Deontology          | Strict merger mass-ratio thresholds     | Major/minor merger counts & ratios  | Follows rigid rules |
| Analytical    | Utilitarianism      | Maximum stellar mass conversion         | Stellar mass / total mass, SFR      | Maximizes "output" |
| Revisionist   | Relativism          | High variance across environments       | Property scatter vs. local density  | Context-dependent behavior |
| Value-driven  | Virtue ethics       | Early assembly + late quiescence        | Half-mass formation time            | Strong "character" |
| Global        | Ethics of care      | Environmental interaction & satellites  | Satellite count, tidal features     | Nurtures or shaped by surroundings |

## Files

- `qtpm_validator_lite.py` — Improved synthetic halo generator (400 halos, realistic distributions)
- `app.py` — Streamlit dashboard (Overview, Pathway Analysis, Proposition Validation tabs)
- `analyze_propositions.sql` — SQL queries testing all five formal propositions
- `qtpm_validation.db` — Current database (400 synthetic halos)
- `qtpm_tng_real.py` / `qtpm_cosmosim.py` — Real data fetchers (API key required for TNG)

## Quick Start

```bash
source .venv/bin/activate
python qtpm_validator_lite.py          # Regenerate data (optional)
streamlit run app.py                   # Launch interactive dashboard
```

## Next Steps

1. Obtain valid IllustrisTNG API key and complete `qtpm_tng_real.py` integration.
2. Run proposition queries via dashboard or SQL and interpret physical/ethical mappings.
3. Add visualization of 4D worldline curvature and interference effects.

**Status**: Synthetic validation pipeline + dashboard complete. Ready for real simulation data when API access is available.