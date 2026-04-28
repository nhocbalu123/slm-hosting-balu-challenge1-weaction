# Runbook

This runbook explains how to operate, debug, and demonstrate `slm-hosting-balu-challenge1-weaction`.

## Services

| Service     | Purpose                               | Internal URL               |
| ----------- | ------------------------------------- | -------------------------- |
| `nginx`     | Public reverse proxy and rate limiter | `http://nginx:80`          |
| `api`       | FastAPI wrapper                       | `http://api:8080`          |
| `vllm-qwen` | GPU inference provider                | `http://vllm-qwen:8000/v1` |
| `ollama`    | CPU fallback provider                 | `http://ollama:11434/v1`   |

## Start GPU stack

```bash
cp .env.example .env
bash scripts/download_model.sh
docker compose -f docker/docker-compose.yml up --build -d
```

Optional fallback:

```bash
docker compose -f docker/docker-compose.yml --profile fallback up --build -d
bash scripts/pull_ollama_model.sh
```

## Start CPU-only stack

```bash
cp .env.example .env
docker compose -f docker/docker-compose.cpu.yml up --build -d
bash scripts/pull_ollama_model_cpu.sh
```

## Health checks

Shallow API health:

```bash
curl http://localhost/health
```

Deep provider health:

```bash
curl http://localhost/v1/health | jq
```

Expected states:

| State      | Meaning                                       |
| ---------- | --------------------------------------------- |
| `ok`       | vLLM is reachable and model endpoint responds |
| `degraded` | vLLM is down, fallback provider is reachable  |
| `down`     | no provider is reachable                      |

## Smoke test

```bash
bash scripts/smoke_test.sh
```

If `jq` is not installed, the script prints raw JSON with a warning.

Run inside the API container (uses bundled `jq`):

```bash
docker compose -f docker/docker-compose.yml exec -e BASE_URL=http://localhost:8080 api bash /app/scripts/smoke_test.sh
```

## Logs

FastAPI JSON logs:

```bash
docker compose -f docker/docker-compose.yml logs api --tail=100
```

Nginx JSON access logs:

```bash
docker compose -f docker/docker-compose.yml logs nginx --tail=100
```

vLLM initialization logs:

```bash
docker compose -f docker/docker-compose.yml logs vllm-qwen --tail=100
```

Important fields:

- `request_id`
- `path`
- `status_code`
- `latency_ms`
- `provider`
- `subject`

## Fallback test

1. Start GPU stack with fallback profile:

```bash
docker compose -f docker/docker-compose.yml --profile fallback up -d
```

2. Call health to confirm vLLM is serving:

```bash
curl http://localhost/v1/health | jq
```

Expected `primary.healthy: true`.

3. Stop vLLM:

```bash
docker compose -f docker/docker-compose.yml stop vllm-qwen
```

4. Wait a few seconds for health check to detect the outage, then call health:

```bash
curl http://localhost/v1/health | jq
```

4. Call chat completion and check response header:

```bash
curl -i http://localhost/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: dev-balu-key' \
  -d '{"messages":[{"role":"user","content":"Say fallback ok"}],"max_tokens":32}'
```

Expected header:

```text
X-LLM-Provider: ollama
```

## Rate-limit proof

```bash
bash scripts/load_test_rate_limit.sh
```

Expected result: a mix of `200`, `503` if model is overloaded, and `429` when Nginx rate limiting is hit. For the screenshot required by the challenge, capture the terminal output showing `429`.

## Common incidents

### vLLM container exits immediately

Check GPU support:

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

If this fails, install or fix NVIDIA Container Toolkit.

### NVIDIA requirement error: `unsatisfied condition: cuda>=13.0`

If you use `vllm/vllm-openai:nightly`, the image may require CUDA 13.
If your host driver supports CUDA 12.x (for example 12.9), pin a CUDA 12.9 image tag in `.env`:

```env
VLLM_IMAGE=vllm/vllm-openai:v0.20.0-cu129-ubuntu2404
```

Then recreate the GPU stack:

```bash
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml up --build -d
```

If you do not need GPU serving, use CPU-only mode instead:

```bash
docker compose -f docker/docker-compose.cpu.yml up --build -d
```

### Model path not found

Check that `scripts/download_model.sh` created:

```bash
ls -lah models/Qwen3.5-0.8B
```

Check `.env`:

```env
VLLM_MODEL_PATH=/models/Qwen3.5-0.8B
```

### vLLM memory errors

If you see a KV cache error like:

```text
KV cache is needed ... larger than the available KV cache memory
```

Increase GPU memory utilization and/or lower the model length:

```env
GPU_MEMORY_UTILIZATION=0.70
MAX_MODEL_LEN=1024
MAX_NUM_SEQS=4
```

If you see CUDA OOM errors, lower `GPU_MEMORY_UTILIZATION` or `MAX_MODEL_LEN` instead.

Or run CPU-only mode with Ollama.

### API returns 401

Add a valid key:

```bash
-H 'X-API-Key: dev-balu-key'
```

Or disable auth for local debugging by setting:

```env
API_KEYS=
```

### API returns 429

The in-memory app quota or Nginx rate limiter is working. Lower traffic or increase `REQUESTS_PER_MINUTE` and the Nginx `limit_req_zone` rate.

### API container exits or fails health checks with SettingsError

If the API container shows this error in logs:

```
pydantic_settings.sources.SettingsError: error parsing value for field "api_keys" from source "EnvSettingsSource"
```

This occurs because Pydantic Settings tries to parse the `API_KEYS` environment variable before field validators run. The solution is to rebuild the Docker image without cache to pick up the fixed configuration:

```bash
docker compose -f docker/docker-compose.yml down
docker image rm balu-weaction-gpu-api
docker compose -f docker/docker-compose.yml build --no-cache api
docker compose -f docker/docker-compose.yml up -d
```

The fix in `app/core/config.py` uses a `field_validator` with `mode="before"` and accepts the `api_keys` field as `Any` type to bypass Pydantic Settings' automatic JSON parsing.

### Docker BuildKit caches old application code

If you update Python code in `app/` but the Docker image still runs old code, Docker BuildKit may be caching the `COPY app ./app` layer. Force a rebuild without cache:

```bash
docker compose -f docker/docker-compose.yml build --no-cache api
docker compose -f docker/docker-compose.yml up -d
```

### Container name already in use

If you see "Conflict. The container name '/balu-vllm-qwen35' is already in use by container...", the old container name from a previous deployment is blocking the new one.

Fix: Docker Compose now uses project-scoped container names (e.g., `balu-weaction-gpu-api-1` instead of fixed names). Remove the old containers:

```bash
docker compose -f docker/docker-compose.yml down --remove-orphans
docker compose -f docker/docker-compose.yml up -d
```

## Mistakes avoided from the challenge

1. Model weights are not downloaded in the Dockerfile.
2. vLLM is not exposed directly to the internet; Nginx is the edge.
3. The wrapper validates request shape before calling the model.
4. API keys are checked by the wrapper.
5. Quota/rate limiting exists in both FastAPI and Nginx layers.
6. Logs are structured JSON and include latency/request metadata.
7. Health checks verify downstream provider readiness, not only process uptime.
8. Timeout and fallback prevent the API from hanging forever when vLLM is slow or down.

## Development

Run the API locally against any OpenAI-compatible backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

Run tests:

```bash
pytest -q
```

### Windows note

On Windows, run these commands in Git Bash:

```bash
bash scripts/download_model.sh
```

If `python` is not found, install Python 3.10+ and enable **Add python.exe to PATH**, then reopen Git Bash.

## Screenshot checklist

Save evidence into `docs/screenshots/`:

1. `1-chat-success.png` — successful `POST /v1/chat/completions`
2. `2-health-ok.png` — `GET /v1/health` when the provider is up
3. `3-health-fail.png` — `GET /v1/health` after stopping vLLM, showing fallback/degraded state
4. `4-rate-limit.png` — Nginx returns 429 under spam load
5. `5-json-log.png` — container logs with JSON fields
6. `6-compose-healthy.png` — `docker compose ps` showing healthy/running containers

Helper commands:

```bash
bash scripts/smoke_test.sh
bash scripts/load_test_rate_limit.sh
```
