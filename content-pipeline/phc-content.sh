#!/usr/bin/env bash
# Compatibility wrapper; prefer ./content-pipeline/phc-content
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$DIR/phc-content" "$@"
