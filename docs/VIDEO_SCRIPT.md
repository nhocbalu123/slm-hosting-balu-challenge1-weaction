# 5-Minute Demo Video Script

## 0:00-0:30 — Introduction

Hi, I am BALU. This project is `slm-hosting-balu-challenge1-weaction`. It demonstrates how to self-host a small Qwen 3.5 model behind a production-style API stack.

## 0:30-1:20 — Architecture

Show the diagram in the README.

Explain:

- Nginx is the public entrypoint and rate limiter.
- FastAPI is the wrapper for validation, API keys, quota, logs, health checks, timeout, and fallback.
- vLLM serves the model on GPU.
- Ollama is the CPU fallback path.

## 1:20-2:20 — Model choice

Explain:

- The original challenge suggested Qwen 2.5 1.5B AWQ.
- I selected `Qwen/Qwen3.5-0.8B` because it is a newer small model suitable for demo and portfolio usage.
- For CPU-only environments, I use `qwen3.5:0.8b` via Ollama.

## 2:20-3:20 — Docker Compose demo

Run:

```bash
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml ps
```

Point out:

- `vllm-qwen`
- `api`
- `nginx`
- optional `ollama`

Mention important config:

- `max-model-len`
- `gpu-memory-utilization`
- model volume mount
- GPU tuning knobs: `MAX_MODEL_LEN`, `MAX_NUM_SEQS`, and `GPU_MEMORY_UTILIZATION` (show the values from your `.env`)

## 3:20-4:20 — Product demo

Run:

```bash
bash scripts/smoke_test.sh
```

Show:

- health check
- chat completion response
- `X-LLM-Provider` header from the smoke test or the clean header/body command in `docs/screenshots/README.md`
- note: if `jq` is missing, the script prints raw JSON or run it inside the API container

## 4:20-5:00 — Production-readiness proof

Show:

- JSON logs
- rate limit test
- degraded/fallback health state
- `docs/AVOIDANCE_TABLE.md`
- `docs/RUNBOOK.md`

Close by explaining that a real production version would use Redis quota, TLS certificates, metrics, tracing, Kubernetes autoscaling, and streaming response support.
