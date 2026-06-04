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

- `qtpm_tng_validator.py` — Full batch processor (IllustrisTNG → SQLite)
- `analyze_propositions.sql` — SQL queries testing all five formal propositions
- `qtpm_validation.db` — Generated SQLite database (after running the validator)

## Quick Start

```bash
python qtpm_tng_validator.py          # process trees/ folder into SQLite
sqlite3 qtpm_validation.db < analyze_propositions.sql
```

## Next Steps

1. Point `qtpm_tng_validator.py` at real TNG tree files.
2. Run the five proposition queries and interpret results.
3. Extend with additional TNG fields or visualization.

**Status**: Core pipeline implemented. Ready for real data.