#!/usr/bin/env bash

# For debug uncomment the following line.
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update

apt-get install -y \
    zsh \
    curl \
    -o Dpkg::Options::="--force-confold"

apt-get clean

export UV_CACHE_DIR="$(pwd)/.cache"
export UV_PYTHON_INSTALL_DIR="$(pwd)/.python"

if [ "$#" -eq 2 ]; then
    ./uv run --python 3.12 src/init.py --config "$1" --workspace "$2"
else
    ./uv run --python 3.12 src/init.py --config config.yaml --workspace ~/workspace
fi

rm -rf "$UV_CACHE_DIR"
rm -rf "$UV_PYTHON_INSTALL_DIR"
