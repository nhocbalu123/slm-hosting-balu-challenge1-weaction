#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
API_KEY="${API_KEY:-dev-balu-key}"
MODEL="${PUBLIC_MODEL_NAME:-qwen3.5-0.8b}"

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

echo "== Shallow health =="
curl -s "$BASE_URL/health" | pretty_json

echo "== Deep health =="
curl -s "$BASE_URL/v1/health" | pretty_json

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

curl -s "$BASE_URL/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $API_KEY" \
  -d "$payload" | pretty_json
