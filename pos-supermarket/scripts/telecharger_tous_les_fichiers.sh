#!/usr/bin/env bash
set -euo pipefail

# Crée une archive ZIP de tout le projet (hors fichiers temporaires)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUTPUT_NAME="${1:-pos-supermarket-complet.zip}"
OUTPUT_PATH="${PROJECT_DIR}/${OUTPUT_NAME}"

cd "${PROJECT_DIR}"

zip -r "${OUTPUT_PATH}" . \
  -x "*.git*" \
  -x "*.venv/*" \
  -x "__pycache__/*" \
  -x "*.pyc" \
  -x "data/*.db" \
  -x "data/backup.db"

echo "Archive créée: ${OUTPUT_PATH}"
