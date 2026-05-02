# Changelog

All notable changes to this project will be documented in this file.

## [0.1.6] - 2026-05-02

### Added

- **MIT license**: added `LICENSE` so the portfolio project has clear reuse terms.
- **README CI badge and portfolio positioning**: added the GitHub Actions badge, explicit AI serving/MLOps positioning, a Mermaid architecture diagram, and a concise "Current limitations and next improvements" section.
- **Provider HTTP boundary tests**: added mocked `httpx` tests for provider 4xx, 5xx, timeout, connection error, malformed JSON, `/models` failure, and model-mismatch health behavior.

### Changed

- **Runtime and development dependencies split**: `requirements.txt` now contains only runtime dependencies, while `requirements-dev.txt` installs test, lint, type-check, and coverage tools for local development and CI.
- **CI dependency install path**: GitHub Actions now installs `requirements-dev.txt`; the Docker runtime image continues to install only `requirements.txt`.
- **Provider request rejection handling**: provider 4xx responses from chat completions now raise a request error, skip fallback, and return a wrapper 400 instead of being treated as provider outages.

### Security

- **Raw API keys removed from log subjects**: authenticated requests now use a stable redacted subject such as `api_key:<hash-prefix>` for quota and structured logs instead of logging the raw API key.
- **Constant-time API key comparison**: configured API keys are checked with `hmac.compare_digest` to avoid ordinary string-comparison timing criticism.

### Fixed

- **CI mypy failure**: narrowed the optional fallback provider before using fallback fields in gateway health and chat paths.
- **Linux pytest import path**: `pytest.ini` now adds the repository root to `pythonpath` so CI can import the local `app` package during test collection.

## [0.1.5] - 2026-04-29

### Added

- **ruff, mypy, and coverage in CI**: the test job now runs `ruff check .`, `mypy app/`, and `pytest -q --cov=app --cov-report=term-missing`. `pytest-cov>=5.0.0`, `ruff>=0.4.0`, and `mypy>=1.10.0` added to `requirements.txt`.
- **Docker build job in CI**: a separate `docker` job runs `docker build -f docker/Dockerfile .` on every CI run, catching Dockerfile regressions before they reach production.

### Changed

- **CI triggers on `dev` branch**: the workflow now runs on pushes to both `main` and `dev`, and on all pull requests. Previously only `main` push and PRs triggered CI.
- **CI Python version aligned to 3.12**: matches `docker/Dockerfile` (`python:3.12-slim`) so CI tests the same interpreter that ships in the container. Previously CI used Python 3.11.
- **`.env` file loaded automatically for local development**: `SettingsConfigDict` now sets `env_file=".env"` and `env_file_encoding="utf-8"`. Copying `.env.example` to `.env` and running `uvicorn app.main:app` locally is now sufficient — no manual shell variable export required. Docker Compose is unaffected because it injects environment variables at the container level, which take precedence over the file.
- **Health check verifies the configured model name**: `OpenAICompatibleClient.health()` now checks that the expected model ID (`settings.vllm_model` for the primary, `settings.fallback_model` for the fallback) appears in the provider's `/models` list. A provider is marked `healthy: false` if the endpoint responds but the model is absent, and the `detail` field reports which model was expected and which were found.
- **Provider responses protected against malformed JSON**: `chat_completions()` and `models()` now wrap `response.json()` in `try/except ValueError` and raise `ProviderUnavailableError`, so a provider returning a non-JSON 200 body produces a clean 503 instead of an unhandled 500.
- **Endpoint tests now override auth dependency**: `tests/test_endpoints.py` overrides `authenticated_subject` in the test client fixture so endpoint tests remain independent of the local `.env` `API_KEYS` value.

### Documentation

- README: CI trigger description corrected from "on every push" to "on pushes to `main` and `dev`, and on pull requests"; `/v1/chat/completions` labelled as "OpenAI-compatible-subset"; model routing behaviour documented below the API table; quota limitations note expanded with per-process, unbounded-growth, and restart-reset caveats.
- Screenshot guide and runbook: replaced inline header/body chat examples with separated output and short deterministic prompts so provider headers remain visible while JSON responses stay readable in screenshots.

## [0.1.4] - 2026-04-29

### Added

- **GitHub Actions CI**: `.github/workflows/ci.yml` runs `pytest -q` on pushes to `main` and on pull requests using Python 3.11.
- **`pytest.ini`**: configures `asyncio_mode = auto` and `asyncio_default_fixture_loop_scope = function` so async tests run without per-function decorators.
- **Test suite expansion** — three new test files (14 tests total, up from 5):
  - `tests/test_chat_schema.py`: Pydantic schema validation (empty messages, missing user role, temperature out of range).
  - `tests/test_gateway.py`: async unit tests for `LLMGateway` (primary success, primary failure → Ollama fallback, both providers down).
  - `tests/test_endpoints.py`: HTTP-layer tests via `TestClient` (stream rejection → 400, provider header on success, both providers down → 503).
- **`docs/EVALUATION.md`**: sample prompts with outputs, measured latencies, fallback trigger conditions, and a 0.8B SLM limitations table.
- **README engineering decisions section**: documents `asyncio_mode = auto` rationale, `/v1/health` auth fix, dependency-override test isolation, and vLLM-primary/Ollama-fallback design choice.

### Security

- **`GET /v1/health` now requires authentication**: added `AuthSubjectDep` to the deep health endpoint (matching `GET /v1/models`). The response includes `base_url` for each provider; requiring a valid API key prevents internal service topology from leaking in public deployments. The unauthenticated root `GET /health` is unaffected.

## [0.1.3] - 2026-04-28

### Fixed

- **Model path case mismatch**: Fixed `MODEL_DIR` default in `scripts/download_model.sh` from `./models/qwen3.5-0.8b` (lowercase) to `./models/Qwen3.5-0.8B` (mixed case) to match the paths defined in `.env.example` and Docker Compose, preventing vLLM from failing to locate the downloaded model on case-sensitive Linux filesystems.

## [0.1.2] - 2026-04-28

### Fixed

- **vLLM startup crash**: Removed unsupported `--disable-log-requests` from the GPU compose command to prevent vLLM from exiting on startup.
- **vLLM KV cache initialization failures**: Tuned default GPU settings to increase `GPU_MEMORY_UTILIZATION` and reduce `MAX_MODEL_LEN`/`MAX_NUM_SEQS` for smaller GPUs.
- **Smoke test JSON payload**: Switched to a heredoc payload to avoid invalid JSON escaping, and added a formatter fallback when `jq` is missing.

### Improved

- **In-container smoke tests**: Bundled `bash`, `curl`, and `jq` in the API image and copied scripts into the container for easier smoke testing.
- **Runbook usability**: Documented the container smoke test command and clarified smoke test behavior without `jq`.

## [0.1.0] - 2026-04-27

### Added

- Initial WeAction Challenge 1 repository structure.
- FastAPI wrapper for OpenAI-compatible chat completions.
- vLLM primary provider integration.
- Ollama CPU fallback provider integration.
- Docker Compose GPU stack.
- Docker Compose CPU-only demo stack.
- Nginx reverse proxy and rate limiting.
- API-key authentication with `X-API-Key` and bearer token support.
- In-memory fixed-window request quota.
- Structured JSON access and provider logs.
- Deep health check endpoint.
- Model download script for Hugging Face models.
- Ollama model pull scripts.
- Smoke test and rate-limit proof scripts.
- Runbook, architecture decision record, and avoidance table.

### Notes

- Screenshots in `docs/screenshots/` must be captured after running the stack on the target machine.
- For real production, replace in-memory quota with a shared store such as Redis.
