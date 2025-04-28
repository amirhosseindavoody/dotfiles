#!/usr/bin/env bash

# For debug uncomment the following line.
set -euo pipefail

export UV_CACHE_DIR="$(pwd)/.cache"
export UV_PYTHON_INSTALL_DIR="$(pwd)/.python"

if [ "$#" -eq 2 ]; then
    ./uv run src/init.py --config "$1" --workspace "$2"
else
    ./uv run src/init.py --config config.yaml --workspace ~/workspace
fi

rm -rf "$UV_CACHE_DIR"
rm -rf "$UV_PYTHON_INSTALL_DIR"