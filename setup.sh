#!/usr/bin/env bash

export DEBIAN_FRONTEND=noninteractive

apt-get update

apt-get install -y \
    zsh \
    git \
    gnupg \
    curl \
    rsync \
    just \
    -o Dpkg::Options::="--force-confold"

apt-get clean

cd "$(dirname "${BASH_SOURCE}")";

git pull origin main;

rsync --exclude ".git/" \
  --exclude ".DS_Store" \
  --exclude ".osx" \
  --exclude "setup.sh" \
  --exclude "README.md" \
  --exclude "LICENSE" \
  -avh --no-perms . ${HOME};
  

# Install Antigen for Zsh plugin management
mkdir -p ${HOME}/.antigen
curl -L git.io/antigen > ${HOME}/.antigen/antigen.zsh
chmod +x ${HOME}/.antigen/antigen.zsh

mkdir -p ${HOME}/.zsh/custom-scripts
just --completions zsh > ${HOME}/.zsh/custom-scripts/_just
