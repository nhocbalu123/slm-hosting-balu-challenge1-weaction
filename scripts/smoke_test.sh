#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
API_KEY="${API_KEY:-dev-balu-key}"
MODEL="${PUBLIC_MODEL_NAME:-qwen3.5-0.8b}"

echo "== Shallow health =="
curl -s "$BASE_URL/health" | jq .

echo "== Deep health =="
curl -s "$BASE_URL/v1/health" | jq .

echo "== Chat completion =="
curl -s "$BASE_URL/v1/chat/completions" \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $API_KEY" \
  -d "{\n    \"model\": \"$MODEL\",\n    \"messages\": [\n      {\"role\": \"system\", \"content\": \"You are a concise assistant for AI engineering demos.\"},\n      {\"role\": \"user\", \"content\": \"Explain what vLLM does in 3 short bullets.\"}\n    ],\n    \"max_tokens\": 256,\n    \"temperature\": 0.4\n  }" | jq .
