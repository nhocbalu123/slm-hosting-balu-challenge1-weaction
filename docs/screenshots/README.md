# Screenshots for challenge proof

Capture real screenshots after running the stack and save the image files in this folder. Use these exact filenames so reviewers can match each screenshot to the proof item.

## Before taking screenshots

Use Git Bash on Windows and run commands from the repository root.

Start the GPU stack with the fallback profile when you want to prove both vLLM and Ollama fallback:

```bash
cp .env.example .env
bash scripts/download_model.sh
docker compose -f docker/docker-compose.yml --profile fallback up --build -d
bash scripts/pull_ollama_model.sh
```

Wait until the model containers finish loading. vLLM can take several minutes on first start. Check progress with:

```bash
docker compose -f docker/docker-compose.yml logs vllm-qwen --tail=100
docker compose -f docker/docker-compose.yml --profile fallback ps
```

If the Ollama pull command runs before the fallback container is ready, wait until `ollama` is `Up` in `docker compose ps`, then run `bash scripts/pull_ollama_model.sh` again.

If you are using the CPU-only demo instead of a GPU, start this stack:

```bash
cp .env.example .env
docker compose -f docker/docker-compose.cpu.yml up --build -d
bash scripts/pull_ollama_model_cpu.sh
```

For each screenshot, make the terminal wide enough that the command and important output are visible. On Windows, use Snipping Tool or `Win + Shift + S`, save as PNG, and keep the command plus the result in the image.

## 1. `1-chat-success.png` - successful chat completion

Run a direct chat request through Nginx. This writes response headers and body to separate temporary files, then prints the useful headers and pretty JSON so the screenshot is readable. The provider header is normalized to `X-LLM-Provider` for display; HTTP header names are case-insensitive.

```bash
curl -sS -D /tmp/chat-headers.txt -o /tmp/chat-body.json \
  http://localhost/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: dev-balu-key' \
  -d '{
    "model": "qwen3.5-0.8b",
    "messages": [
      {"role": "user", "content": "Reply with exactly: vLLM OK"}
    ],
    "max_tokens": 16,
    "temperature": 0.0
  }' && \
sed -n '1p;s/^x-llm-provider:[[:space:]]*/X-LLM-Provider: /Ip;s/^x-request-id:[[:space:]]*/x-request-id: /Ip' /tmp/chat-headers.txt && \
jq . /tmp/chat-body.json
```

Capture the terminal showing:

- `HTTP/1.1 200 OK`
- `X-LLM-Provider: vllm` for the GPU stack, or the active provider in your demo
- A JSON response containing `choices` and a short assistant message, ideally `vLLM OK`

If `jq` is not installed, replace the last line with `python -m json.tool /tmp/chat-body.json`. If the response is long, scroll so the status/header and the start of the JSON body are visible.

## 2. `2-health-ok.png` - deep health with model loaded

Run the authenticated deep health check:

```bash
curl -s http://localhost/v1/health \
  -H 'X-API-Key: dev-balu-key' | jq
```

If `jq` is not installed, use:

```bash
curl -s http://localhost/v1/health \
  -H 'X-API-Key: dev-balu-key' | python -m json.tool
```

Capture the output showing:

- `"status": "ok"`
- `"model_loaded": true`
- `"active_provider": "vllm"`
- `"primary"` with `"healthy": true`

For CPU-only mode, the wrapper still calls the active primary provider `vllm`, but the backend URL is Ollama as configured in `docker/docker-compose.cpu.yml`.

## 3. `3-health-fail.png` - vLLM stopped and fallback/degraded health

Use the GPU stack with the fallback profile for this screenshot. First confirm both the stack and the Ollama model are ready:

```bash
docker compose -f docker/docker-compose.yml --profile fallback ps
bash scripts/pull_ollama_model.sh
```

Stop only the vLLM container:

```bash
docker compose -f docker/docker-compose.yml stop vllm-qwen
```

Wait a few seconds, then run:

```bash
curl -s http://localhost/v1/health \
  -H 'X-API-Key: dev-balu-key' | jq
```

Capture the output showing:

- `"status": "degraded"`
- `"active_provider": "ollama"`
- `"model_loaded": true`
- `"primary"` with `"healthy": false`
- `"fallback"` with `"healthy": true`

After taking the screenshot, restart vLLM for the remaining screenshots:

```bash
docker compose -f docker/docker-compose.yml --profile fallback up -d vllm-qwen
```

If you intentionally run without fallback, the health status may be `"down"` instead of `"degraded"`. For the challenge proof, prefer the fallback profile because it demonstrates graceful degradation.

## 4. `4-rate-limit.png` - Nginx 429 from burst traffic

Run the included burst test:

```bash
bash scripts/load_test_rate_limit.sh
```

The script sends 60 concurrent chat requests through Nginx and prints status-code counts. Capture the output showing a count for `429`, for example:

```text
Sending burst requests. Some should return 429 from Nginx when rate limit is hit.
     20 200
     40 429
```

The exact counts can differ. It is acceptable if the output also includes `503` when the model is overloaded, as long as `429` appears.

If no `429` appears, run the command again immediately while the Nginx rate-limit window is still hot.

## 5. `5-json-log.png` - FastAPI structured JSON logs

Generate at least one request first:

```bash
bash scripts/smoke_test.sh
```

Then show API logs:

```bash
docker compose -f docker/docker-compose.yml logs api --tail=100
```

For CPU-only mode, use:

```bash
docker compose -f docker/docker-compose.cpu.yml logs api --tail=100
```

Capture log lines that are valid JSON and include fields such as:

- `"message": "request completed"`
- `"request_id"`
- `"path"`
- `"status_code"`
- `"latency_ms"`
- `"message": "chat completion succeeded"` with `"provider"`
- `"subject": "api_key:..."` for authenticated requests, without exposing the raw API key

If the terminal output is too noisy, run a fresh chat request and then run the logs command again with a smaller tail, for example `--tail=30`.

## 6. `6-compose-healthy.png` - Docker Compose services running

For the GPU stack, run:

```bash
docker compose -f docker/docker-compose.yml --profile fallback ps
```

Capture the table showing these services as running:

- `nginx`
- `api`
- `vllm-qwen`
- `ollama` if you started the fallback profile

The `STATUS` column should show `Up` and preferably `healthy` for `nginx`, `api`, and loaded model services. If vLLM is still starting, wait and run the command again.

For CPU-only mode, capture:

```bash
docker compose -f docker/docker-compose.cpu.yml ps
```

The table should show `nginx`, `api`, and `ollama` running.

## Final checklist

- [ ] `1-chat-success.png`
- [ ] `2-health-ok.png`
- [ ] `3-health-fail.png`
- [ ] `4-rate-limit.png`
- [ ] `5-json-log.png`
- [ ] `6-compose-healthy.png`

Do not commit fake or placeholder screenshots. Capture the real terminal output from the machine where the stack is running.
