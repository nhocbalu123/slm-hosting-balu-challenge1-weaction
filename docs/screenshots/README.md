# Screenshots for challenge proof

Capture real screenshots after running the stack and save them here:

1. `1-chat-success.png` — successful `POST /v1/chat/completions`
2. `2-health-ok.png` — `GET /v1/health` with model loaded
3. `3-health-fail.png` — `GET /v1/health` with vLLM stopped and fallback/degraded state
4. `4-rate-limit.png` — Nginx `429` response from burst traffic
5. `5-json-log.png` — JSON logs from `docker logs balu-fastapi-wrapper`
6. `6-compose-healthy.png` — `docker compose ps`

The repo includes this folder so your final GitHub submission has the expected location ready.
