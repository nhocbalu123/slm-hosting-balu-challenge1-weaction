#!/usr/bin/env bash
set -euo pipefail

MODEL_NAME="${MODEL_NAME:-Qwen/Qwen3.5-0.8B}"
MODEL_DIR="${MODEL_DIR:-./models/Qwen3.5-0.8B}"

find_python() {
  if command -v python >/dev/null 2>&1; then
    echo "python"
  elif command -v python3 >/dev/null 2>&1; then
    echo "python3"
  elif command -v py >/dev/null 2>&1; then
    echo "py -3"
  else
    return 1
  fi
}

PYTHON_CMD="$(find_python || true)"

if [[ -z "${PYTHON_CMD}" ]]; then
  echo "Could not find Python."
  echo ""
  echo "Install Python 3.10+ from https://www.python.org/downloads/"
  echo "During installation, enable: Add python.exe to PATH"
  echo ""
  echo "Then reopen Git Bash and verify:"
  echo "  python --version"
  echo "or:"
  echo "  py -3 --version"
  exit 1
fi

if ! command -v huggingface-cli >/dev/null 2>&1; then
  echo "huggingface-cli not found. Installing huggingface_hub..."
  # shellcheck disable=SC2086
  $PYTHON_CMD -m pip install --upgrade huggingface_hub
fi

mkdir -p "${MODEL_DIR}"

echo "Downloading ${MODEL_NAME} to ${MODEL_DIR}..."
huggingface-cli download "${MODEL_NAME}" \
  --local-dir "${MODEL_DIR}" \
  --local-dir-use-symlinks False

echo "Model downloaded successfully."
