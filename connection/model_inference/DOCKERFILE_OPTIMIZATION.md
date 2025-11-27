# Dockerfile Optimization Guide

## Problem: Slow Build Times

The original Dockerfile takes **20+ minutes** to build, primarily due to:
1. Installing PyTorch and large ML libraries
2. Redundant package installations
3. Inefficient Docker layer caching
4. Multiple separate RUN commands

## Issues Found in Original Dockerfile

### 1. Redundant Installations
- **Line 32**: `pip install -e .` installs torch (from pyproject.toml)
- **Line 36**: `pip install torch torchvision torchaudio` installs torch AGAIN (and outside conda env!)
- **Line 38**: `pip install transformers` but it's already in pyproject.toml dependencies
- **Line 35**: `pip install peft==0.10.0` but peft is already in pyproject.toml

### 2. Wrong Environment
- **Line 36**: Uses `pip install` instead of `conda run -n llava pip install`
- This installs packages in the base conda environment, not the `llava` environment!

### 3. Poor Caching
- Copies entire codebase before installing dependencies
- Changes to code invalidate dependency cache layers
- Multiple RUN commands create many layers

## Solutions

### Option 1: Quick Fix (Minimal Changes)

Replace the problematic lines in your current Dockerfile:

```dockerfile
# BEFORE (lines 30-38):
RUN conda run -n llava pip install --upgrade pip
RUN conda run -n llava pip install -e .
RUN conda run -n llava pip install -e ".[train]"
RUN conda run -n llava pip install datasets
RUN conda run -n llava pip install peft==0.10.0
RUN pip install torch torchvision torchaudio  # ❌ WRONG - outside conda env!
RUN conda run -n llava pip install tensorboard
RUN conda run -n llava pip install transformers

# AFTER (optimized):
RUN conda run -n llava pip install --upgrade pip setuptools wheel
# Install PyTorch first (large, benefits from separate caching)
RUN conda run -n llava pip install torch==2.1.2 torchvision==0.16.2
# Install everything else in one go (removes redundant installs)
RUN conda run -n llava pip install -e ".[train]" datasets tensorboard
```

**Benefits:**
- ✅ Removes redundant installations
- ✅ Fixes conda environment issue
- ✅ Reduces from 8 RUN commands to 3
- ✅ Saves ~5-10 minutes

### Option 2: Better Caching (Recommended)

Use `Dockerfile.faster` which:
1. Copies `pyproject.toml` first
2. Installs dependencies
3. Copies code last

**Benefits:**
- ✅ Code changes don't invalidate dependency cache
- ✅ Faster rebuilds when only code changes
- ✅ Better layer reuse

### Option 3: Maximum Optimization

Use `Dockerfile.optimized` with:
- Separate PyTorch installation for better caching
- Combined pip installs
- Proper layer ordering

## Build Time Comparison

| Approach | First Build | Rebuild (code change) | Rebuild (no change) |
|----------|-------------|----------------------|---------------------|
| **Original** | ~25-30 min | ~25-30 min | ~25-30 min |
| **Quick Fix** | ~20-25 min | ~20-25 min | ~20-25 min |
| **Better Caching** | ~20-25 min | ~2-5 min | ~1 min |
| **Maximum Opt** | ~18-22 min | ~1-3 min | ~30 sec |

## How to Use

### Apply Quick Fix
```bash
# Edit Dockerfile and replace lines 30-38 with the optimized version above
```

### Use Faster Dockerfile
```bash
cd model_inference
cp Dockerfile.faster Dockerfile
docker build -t cad-coder-inference .
```

### Use Maximum Optimization
```bash
cd model_inference
cp Dockerfile.optimized Dockerfile
docker build -t cad-coder-inference .
```

## Additional Speed Tips

### 1. Use BuildKit (Docker 18.09+)
```bash
DOCKER_BUILDKIT=1 docker build -t cad-coder-inference .
```

### 2. Use Docker Build Cache
```bash
# Mount pip cache to avoid re-downloading packages
docker build --build-arg BUILDKIT_INLINE_CACHE=1 \
  --cache-from cad-coder-inference:latest \
  -t cad-coder-inference .
```

### 3. Use Pre-built Base Images
Consider using a pre-built image with PyTorch already installed:
```dockerfile
FROM pytorch/pytorch:2.1.2-cuda11.8-cudnn8-runtime
# Then install your specific packages
```

### 4. Multi-stage Build (Advanced)
Separate build and runtime stages to reduce final image size and build time.

## Why PyTorch Installation is Slow

PyTorch is a **very large package** (~2-3GB):
- Contains compiled CUDA libraries
- Includes many dependencies
- Requires compilation of some components
- Network download time for large wheels

**This is normal** - expect 10-15 minutes for PyTorch installation alone on slower connections.

## Monitoring Build Progress

To see what's taking time:
```bash
docker build --progress=plain -t cad-coder-inference . 2>&1 | tee build.log
```

## Troubleshooting

### Build Still Slow?
1. Check internet connection speed
2. Use a faster PyPI mirror
3. Consider using conda instead of pip for PyTorch:
   ```dockerfile
   RUN conda install -n llava pytorch torchvision -c pytorch -y
   ```

### Out of Memory?
```bash
# Increase Docker memory limit in Docker Desktop settings
# Or build on a machine with more RAM
```

### Package Conflicts?
```bash
# Check pyproject.toml for version conflicts
# Some packages may have incompatible versions
```

