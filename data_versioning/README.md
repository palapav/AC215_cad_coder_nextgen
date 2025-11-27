# Data Versioning

Quick start guide for data versioning. See `DATA_VERSIONING.md` for complete documentation.

## Quick Start

```bash
# Create all versions (V1 and V2)
./create_all_versions.sh

# Initialize DVC versioning
./setup_dvc.sh
```

## Structure

- `data/v1/` - Version 1: Full GenCAD-Code dataset
- `data/v2/` - Version 2: V1 + User data
- `scripts/` - Conversion scripts
- `DATA_VERSIONING.md` - Complete documentation

## Commands

```bash
# Check DVC status
dvc status

# View tracked files
dvc list .
```

For detailed documentation, see `DATA_VERSIONING.md`.

