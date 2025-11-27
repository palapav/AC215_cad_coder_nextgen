# Docker Build Network Timeout Fix

## Problem
The Docker build fails when downloading large CUDA packages (especially `nvidia_cudnn_cu12` at 731.7 MB) due to network timeouts.

**Error:**
```
WARNING: Connection timed out while downloading.
× Download failed after 6 attempts because not enough bytes were received
```

## Solution Applied
The Dockerfile has been updated with:
1. **Extended timeouts**: Increased from default 15s to 1200s (20 minutes) for large package downloads
2. **Retry logic**: Automatic retry with even longer timeout (1800s) if first attempt fails
3. **Proper pip flags**: Using `--default-timeout` and `--timeout` flags

## What Changed

### Before:
```dockerfile
RUN conda run -n llava pip install -e .
```

### After:
```dockerfile
RUN conda run -n llava pip install \
    --default-timeout=1200 \
    --timeout=1200 \
    torch==2.1.2 torchvision==0.16.2 || \
    (echo "Retrying..." && \
     conda run -n llava pip install \
     --default-timeout=1800 \
     --timeout=1800 \
     torch==2.1.2 torchvision==0.16.2)
```

## Alternative Solutions

### Option 1: Use pip config file (More Reliable)
Create a `pip.conf` file:

```dockerfile
# Add before pip install commands
RUN mkdir -p /root/.pip && \
    echo "[global]" > /root/.pip/pip.conf && \
    echo "timeout = 1200" >> /root/.pip/pip.conf && \
    echo "retries = 10" >> /root/.pip/pip.conf
```

### Option 2: Use Environment Variables
```dockerfile
ENV PIP_DEFAULT_TIMEOUT=1200
ENV PIP_RETRIES=10
```

### Option 3: Pre-download Packages (Fastest for Repeated Builds)
```dockerfile
# Download packages to a local cache first
RUN mkdir -p /tmp/pip-cache && \
    conda run -n llava pip download \
    --dest /tmp/pip-cache \
    --default-timeout=1200 \
    torch==2.1.2 torchvision==0.16.2

# Then install from cache
RUN conda run -n llava pip install \
    --find-links /tmp/pip-cache \
    --no-index \
    torch==2.1.2 torchvision==0.16.2
```

### Option 4: Use Conda for PyTorch (If CPU-only is acceptable)
```dockerfile
# Conda handles large packages better than pip
RUN conda install -n llava -y -c pytorch pytorch==2.1.2 torchvision==0.16.2 cpuonly
```

### Option 5: Build with BuildKit and Better Network Settings
```bash
# Use BuildKit for better caching and network handling
DOCKER_BUILDKIT=1 docker build \
  --network=host \
  --build-arg PIP_TIMEOUT=1200 \
  -t cad-coder-inference .
```

## Network Speed Tips

1. **Check your internet connection** - 731MB at 1MB/s = ~12 minutes minimum
2. **Use a faster network** - Try building on a machine with better connectivity
3. **Use a VPN or proxy** - Sometimes helps with PyPI connectivity
4. **Build during off-peak hours** - PyPI may be slower during peak times

## Expected Build Times

- **PyTorch download**: 10-20 minutes (depending on connection speed)
- **nvidia_cudnn_cu12**: 12-20 minutes (731MB at 1-1.5 MB/s)
- **Total package installation**: 20-40 minutes

## Monitoring Progress

To see detailed download progress:
```bash
docker build --progress=plain -t cad-coder-inference . 2>&1 | tee build.log
```

## If Build Still Fails

1. **Check network stability** - Unstable connections cause timeouts
2. **Increase timeout further** - Change 1200 to 2400 (40 minutes)
3. **Use pre-downloaded packages** - Download packages manually first
4. **Consider CPU-only build** - If GPU isn't needed immediately

## Quick Test

Test if the timeout fix works:
```bash
# This should complete without timeout errors
docker build -t cad-coder-inference .
```

If you see timeout errors, the network connection may be too slow or unstable. Consider using Option 3 (pre-download) or Option 4 (conda CPU-only).

