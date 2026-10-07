#!/usr/bin/env bash
# Prepend NVIDIA CUDA 12 runtime libs so onnxruntime-gpu can load its CUDA provider.
# The GPU driver is present but the toolkit isn't installed system-wide;
# the libs live inside the nvidia-* Python packages from another venv.
# Load .env if present
if [ -f "$(dirname "$0")/.env" ]; then
  # shellcheck disable=SC1091
  set -a; . "$(dirname "$0")/.env"; set +a
fi

if [ -n "${NVIDIA_BASE:-}" ] && [ -d "$NVIDIA_BASE" ]; then
  CUDA_LIBS=$(find "$NVIDIA_BASE" -mindepth 2 -maxdepth 2 -name "lib" -type d | paste -sd: -)
  export LD_LIBRARY_PATH="${CUDA_LIBS}:${LD_LIBRARY_PATH:-}"
fi

exec "$(dirname "$0")/venv/bin/python" "$(dirname "$0")/main.py" "$@"
