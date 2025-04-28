#!/usr/bin/env bash

# For debug uncomment the following line.
set -euo pipefail

export UV_CACHE_DIR="$(pwd)/.cache"
export UV_PYTHON_INSTALL_DIR="$(pwd)/.python"

if [ "$#" -eq 2 ]; then
    ./uv run src/init.py --config "$1" --workspace "$2"
else
    echo "Error: you must pass the config yaml file." >&2
    exit 1
fi

rm -rf "$UV_CACHE_DIR"
rm -rf "$UV_PYTHON_INSTALL_DIR"