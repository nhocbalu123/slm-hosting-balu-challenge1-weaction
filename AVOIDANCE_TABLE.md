# Avoidance Table

This file maps the project implementation to production mistakes commonly seen when deploying model servers.

| #   | Mistake avoided              | What this repo does instead                                                                                                          | Evidence to capture                                    |
| --- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------ |
| 1   | Download model in Dockerfile | `scripts/download_model.sh` downloads once into `./models`; vLLM mounts the directory read-only                                      | screenshot of `models/Qwen3.5-0.8B` and Compose volume |
| 2   | Expose vLLM directly         | Only Nginx publishes port `80`; vLLM uses Docker internal networking                                                                 | `docker compose ps` showing only Nginx public port     |
| 3   | No API wrapper validation    | FastAPI uses Pydantic schemas for `/v1/chat/completions`                                                                             | invalid request returns 422                            |
| 4   | No authentication            | API checks `X-API-Key` or bearer token when `API_KEYS` is set                                                                        | request without key returns 401                        |
| 5   | No quota or rate limit       | FastAPI has per-key quota; Nginx has `limit_req`                                                                                     | burst test returns 429                                 |
| 6   | Unstructured logs            | FastAPI and Nginx emit JSON logs with latency and request metadata                                                                   | screenshot of `docker logs`                            |
| 7   | Weak health check            | `/v1/health` checks provider `/models`, not just process uptime                                                                      | health ok/degraded/down screenshots                    |
| 8   | No timeout or fallback       | Provider client has timeouts and falls back from vLLM to Ollama when enabled                                                         | stop vLLM and show fallback response                   |
| 9   | Hard-coded model             | Model IDs and provider URLs are configured with `.env`                                                                               | `.env.example`                                         |
| 10  | Not portable                 | Docker Compose defines API, vLLM, Ollama fallback, and Nginx services                                                                | `docker compose up` screenshot                         |
| 11  | Pydantic field parsing fails | Environment variables are parsed with `field_validator` in before-mode; list fields accept `Any` type to prevent JSON parsing errors | API starts without SettingsError                       |
| 12  | Container name collisions    | Docker Compose uses project-scoped names (`name:` field in compose file) instead of fixed container names                            | `docker compose ps` shows unique container names       |
| 13  | Ignore GPU memory limits     | Compose defaults tune `GPU_MEMORY_UTILIZATION`, `MAX_MODEL_LEN`, and `MAX_NUM_SEQS`; runbook documents KV cache fixes                | vLLM health ok after tuning or runbook screenshot      |
