#!/usr/bin/env bash
# scripts/init.sh: probe-kit init.sh 실행기
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "${SCRIPT_DIR}/../init.sh" "$@"
