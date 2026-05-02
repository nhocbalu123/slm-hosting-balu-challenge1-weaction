# slm-hosting-balu-challenge1-weaction

[![CI](https://github.com/nhocbalu123/slm-hosting-balu-challenge1-weaction/actions/workflows/ci.yml/badge.svg)](https://github.com/nhocbalu123/slm-hosting-balu-challenge1-weaction/actions/workflows/ci.yml)

Production-style self-hosted SLM project for the WeAction Challenge 1 assignment.

This is an AI serving/MLOps project, not a model-training project.

This repository hosts a small Qwen 3.5 model behind a FastAPI wrapper, with Docker Compose, Nginx reverse proxy, basic API-key auth, request quota controls, structured JSON logs, deep health checks, and an Ollama CPU fallback path.

## Why this project exists

AI engineers often need to deploy their own fine-tuned or open-source models instead of calling a hosted API. This repo demonstrates the core production pattern:

```text
Client
  ↓ HTTPS / HTTP
Nginx reverse proxy
  ↓ rate-limited internal traffic
FastAPI wrapper
  ↓ validation, auth, quota, logging, timeout, fallback
vLLM OpenAI-compatible server  ── fallback ── Ollama OpenAI-compatible server
  ↓
Qwen 3.5 SLM
```

## Model choice

Default GPU model:

```text
Qwen/Qwen3.5-0.8B
```

Reason: it is small enough for portfolio/demo deployment, officially published by Qwen, compatible with vLLM, and suitable for prototyping or task-specific development. The original challenge suggested Qwen 2.5 1.5B AWQ, but this repo intentionally uses a current Qwen 3.5 small model while preserving the same production-serving architecture.

CPU fallback model:

```text
qwen3.5:0.8b
```

served by Ollama.

For a larger GPU, you can change `MODEL_ID` and `PUBLIC_MODEL_NAME` in `.env` to another Qwen 3.5 variant.

## Features

- FastAPI wrapper around an OpenAI-compatible-subset `/v1/chat/completions`
- vLLM primary provider
- Ollama CPU fallback provider
- Nginx reverse proxy with rate limiting
- Optional API-key authentication (`/v1/health`, `/v1/models`, and `/v1/chat/completions`)
- Lightweight in-memory per-key quota
- JSON logs with latency, provider, status, request IDs, and redacted API-key subjects
- Deep health checks for primary and fallback providers
- Docker Compose files for GPU and CPU-only demo modes
- GitHub Actions CI running the full test suite on pushes to `main` and `dev`, and on pull requests
- Runbook, architecture decision record, changelog, avoidance table, and evaluation doc

## Repository layout

```text
slm-hosting-balu-challenge1-weaction/
├── .github/workflows/           # CI (pytest on push/PR)
├── app/                         # FastAPI wrapper
├── docker/                      # Dockerfile and Compose files
├── docs/                        # runbook, ADR, changelog, evaluation, screenshots checklist
├── nginx/                       # Nginx reverse-proxy config
├── scripts/                     # setup, smoke test, rate-limit proof helpers
├── tests/                       # unit and HTTP-layer tests
├── docs/AVOIDANCE_TABLE.md      # proof of avoided production mistakes
├── pytest.ini                   # asyncio_mode = auto for pytest-asyncio
├── requirements.txt             # runtime dependencies
├── requirements-dev.txt         # test, lint, type-check dependencies
├── LICENSE
├── .env.example
└── README.md
```

## Getting started

See [docs/RUNBOOK.md](docs/RUNBOOK.md) for detailed setup and operational guides:

- **GPU path**: Start vLLM with Docker Compose
- **CPU-only path**: Start Ollama fallback for demos without a GPU
- **Health checks**: Verify services are running
- **Testing**: Run smoke tests and rate-limit proofs
- **Windows**: Use Git Bash for the shell commands in the runbook (including `bash scripts/download_model.sh`)

Quick smoke test:

```bash
bash scripts/smoke_test.sh
```

If `jq` is missing, the script prints raw JSON. You can also run it inside the API container:

```bash
docker compose -f docker/docker-compose.yml exec -e BASE_URL=http://localhost:8080 api bash /app/scripts/smoke_test.sh
```

## API endpoints

| Method | Endpoint               | Auth required | Purpose                                     |
| ------ | ---------------------- | ------------- | ------------------------------------------- |
| `GET`  | `/health`              | No            | Shallow app health                          |
| `GET`  | `/v1/health`           | Yes           | Deep provider health (includes internal URLs) |
| `GET`  | `/v1/models`           | Yes           | Proxy model list from active provider       |
| `POST` | `/v1/chat/completions` | Yes           | Validated OpenAI-compatible-subset chat completion |

Auth is enforced when `API_KEYS` is non-empty. When `API_KEYS` is empty, all endpoints are accessible without a key.

> **Model routing note:** The `model` field in the request body is accepted but the gateway always routes to the configured deployment model (`VLLM_MODEL` for the primary provider, `FALLBACK_MODEL` for the CPU fallback). The service is a single-model deployment, not a multi-model router. To switch models, update the environment variable and restart the stack.

## Authentication and quota

Authentication is enabled when `API_KEYS` is non-empty.

Accepted auth formats:

```bash
X-API-Key: dev-balu-key
Authorization: Bearer dev-balu-key
```

Quota is intentionally simple and in-memory for a portfolio project. Authenticated requests are tracked by a stable redacted subject such as `api_key:<hash-prefix>`, so raw API keys are not written to application logs. Known limitations: quota is per-process only (not distributed across replicas), counters are stored per subject with no TTL cleanup (unbounded memory growth with many unique subjects), and resets on process restart. For real production, replace it with Redis, API gateway quotas, or a managed identity layer.

## What I Would Improve Next

This repository focuses on the core serving pattern rather than a full production platform. Next improvements would be Redis-backed distributed quota, streaming responses, metrics, distributed tracing, TLS certificate management, Kubernetes deployment/autoscaling, and serving a larger model when GPU capacity allows.

## Portfolio talking points

Use these points in your 5-minute video:

- The project separates model inference from business/API responsibilities.
- vLLM provides high-throughput inference and an OpenAI-compatible API.
- FastAPI adds validation, auth, quota, logging, timeouts, and fallback.
- Nginx protects the app with edge rate limiting and reverse proxying.
- The model is downloaded once and mounted into the container for reproducibility.
- CPU fallback makes the demo possible without a GPU.

---

## Engineering decisions & lessons learned

Key choices worth calling out:

- `asyncio_mode = auto` keeps async tests running without per-test decorators.
- `/v1/health` requires auth because it exposes provider details; root `/health` stays public and shallow.
- Tests override FastAPI dependencies instead of patching app state directly.
- vLLM and Ollama are modelled as primary/fallback providers, not load-balanced peers.

### 0.8B SLM quality vs. latency trade-off

The 0.8B model is fast enough for interactive demos, but quality drops on multi-step reasoning, long-context tasks, and complex instruction following. The gateway is model-agnostic, so moving to a larger model is mostly an environment-variable change.

See [`docs/EVALUATION.md`](docs/EVALUATION.md) for sample prompts, measured latencies, and a detailed limitations table.

## License

MIT. See [`LICENSE`](LICENSE).

