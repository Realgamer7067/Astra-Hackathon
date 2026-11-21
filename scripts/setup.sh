#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  python3 "$script_dir/doctor.py" "$@"
elif command -v python >/dev/null 2>&1; then
  python "$script_dir/doctor.py" "$@"
else
  echo "Python 3 is needed for portable task management and validation."
  echo "Install Python 3 with your OS's trusted package manager, then rerun this script."
  exit 2
fi

