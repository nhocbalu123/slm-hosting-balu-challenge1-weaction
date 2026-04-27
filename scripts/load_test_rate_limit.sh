#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
API_KEY="${API_KEY:-dev-balu-key}"
MODEL="${PUBLIC_MODEL_NAME:-qwen3.5-0.8b}"

payload="{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"Say ok\"}],\"max_tokens\":8}"

echo "Sending burst requests. Some should return 429 from Nginx when rate limit is hit."
seq 1 60 | xargs -I{} -P 20 sh -c "curl -s -o /dev/null -w '%{http_code}\n' '$BASE_URL/v1/chat/completions' -H 'Content-Type: application/json' -H 'X-API-Key: $API_KEY' -d '$payload'" | sort | uniq -c
