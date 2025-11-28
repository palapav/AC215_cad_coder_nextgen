# Data Versioning

Data versioning for the CAD-Coder project using DVC (Data Version Control).

## Quick Start (Docker)

```bash
cd src/data_versioning

# Build and run the container
docker compose build
docker compose run --rm dvc

# Inside container: Create versions and initialize DVC
./create_all_versions.sh
./setup_dvc.sh
```

## Structure

- `data/v1/` - Version 1: Full GenCAD-Code dataset (baseline)
- `data/v2/` - Version 2: V1 + User-generated data
- `scripts/` - Conversion and transformation scripts
- `DATA_VERSIONING.md` - Complete documentation

## Key Commands

```bash
# Check DVC status
docker compose run --rm dvc dvc status

# View tracked files
docker compose run --rm dvc dvc list .

# Verify data integrity
docker compose run --rm dvc bash -c "wc -l data/v1/*.jsonl data/v2/*.jsonl"
```

## Documentation

For complete documentation including:
- Justification for DVC choice
- Version history and checksums
- LLM prompt/output format
- Reproducibility instructions
- Workflow diagrams

See `DATA_VERSIONING.md`.
