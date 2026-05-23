#!/usr/bin/env sh
set -eu

my_path=$(git rev-parse --show-toplevel)

if [ -f "${my_path}/.venv/bin/activate" ]; then
  . "${my_path}/.venv/bin/activate"
  exec "$@"
elif [ -f "${my_path}/venv/bin/activate" ]; then
  . "${my_path}/venv/bin/activate"
  exec "$@"
else
  exec uv run "$@"
fi
