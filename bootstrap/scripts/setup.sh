#!/bin/bash

set -e

# Ensure in git repo
git -C . rev-parse 2>/dev/null

if [ ! -d ".git" ]; then
  echo "Must be run from git root path"
  exit 1
fi

sudo apt-get install -y git-crypt gnupg

python3 -m venv venv
source venv/bin/activate

pip3 install -r requirements.txt
pre-commit install

echo "Run 'source venv/bin/activate' to activate"
