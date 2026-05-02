#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
API_KEY="${API_KEY:-dev-balu-key}"
MODEL="${PUBLIC_MODEL_NAME:-qwen3.5-0.8b}"
TMP_DIR="$(mktemp -d)"
LAST_BODY=""

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

pretty_json() {
  if command -v jq >/dev/null 2>&1; then
    jq .
  elif command -v python >/dev/null 2>&1; then
    python -m json.tool
  elif command -v py >/dev/null 2>&1; then
    py -3 -m json.tool
  else
    echo "WARN: jq/python not found; printing raw JSON." >&2
    cat
  fi
}

json_field() {
  local file="$1"
  local field="$2"

  if command -v jq >/dev/null 2>&1; then
    jq -r ".$field // empty" "$file"
  elif command -v python >/dev/null 2>&1; then
    python - "$file" "$field" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    value = json.load(handle).get(sys.argv[2], "")
print(value if value is not None else "")
PY
  elif command -v py >/dev/null 2>&1; then
    py -3 - "$file" "$field" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    value = json.load(handle).get(sys.argv[2], "")
print(value if value is not None else "")
PY
  else
    echo "ERROR: jq or Python is required to validate smoke-test JSON." >&2
    return 1
  fi
}

request_json() {
  local label="$1"
  local expected_status="$2"
  shift 2

  LAST_BODY="$TMP_DIR/${label}.json"
  local status
  if ! status="$(curl -sS -o "$LAST_BODY" -w "%{http_code}" "$@")"; then
    echo "ERROR: ${label} request failed before an HTTP response was returned." >&2
    return 1
  fi
  if [[ "$status" != "$expected_status" ]]; then
    echo "ERROR: ${label} returned HTTP ${status}; expected ${expected_status}." >&2
    pretty_json < "$LAST_BODY" >&2 || cat "$LAST_BODY" >&2
    return 1
  fi
  pretty_json < "$LAST_BODY"
}

echo "== Shallow health =="
request_json "shallow-health" "200" "$BASE_URL/health"
shallow_status="$(json_field "$LAST_BODY" "status")"
if [[ "$shallow_status" != "ok" ]]; then
  echo "ERROR: shallow health status is '${shallow_status}', expected 'ok'." >&2
  exit 1
fi

echo "== Deep health =="
request_json "deep-health" "200" "$BASE_URL/v1/health" \
  -H "X-API-Key: $API_KEY"
deep_status="$(json_field "$LAST_BODY" "status")"
if [[ "$deep_status" != "ok" && "$deep_status" != "degraded" ]]; then
  echo "ERROR: deep health status is '${deep_status}', expected 'ok' or 'degraded'." >&2
  exit 1
fi

echo "== Chat completion =="
payload=$(cat <<EOF
{
  "model": "$MODEL",
  "messages": [
    {"role": "system", "content": "You are a concise assistant for AI engineering demos."},
    {"role": "user", "content": "Explain what vLLM does in 3 short bullets."}
  ],
  "max_tokens": 256,
  "temperature": 0.4
}
EOF
)

request_json "chat-completion" "200" "$BASE_URL/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $API_KEY" \
  -d "$payload"
