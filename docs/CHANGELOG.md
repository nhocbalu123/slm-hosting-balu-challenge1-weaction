# Changelog

All notable changes to this project will be documented in this file.

## [0.1.1] - 2026-04-28

### Fixed

- **Pydantic Settings parsing error**: Fixed `SettingsError` when parsing `api_keys` environment variable. Changed field type to `Any` and added `field_validator` with `mode="before"` to handle comma-separated string values before Pydantic Settings' automatic JSON parsing.
- **Docker Compose container naming**: Added `name:` field to both compose files (`balu-weaction-gpu` and `balu-weaction-cpu`) to use project-scoped container names instead of fixed container names, preventing name collisions during rebuild and restart.
- **vLLM image pinning**: Confirmed vLLM image is pinned to `v0.20.0-cu129-ubuntu2404` for CUDA 12.9 compatibility with RTX 3060 GPU.
- **Updated logs commands**: Changed from old fixed container names (e.g., `balu-fastapi-wrapper`) to Docker Compose commands (e.g., `docker compose logs api`).
- **Docker BuildKit caching**: Added troubleshooting guidance for `--no-cache` flag when code changes aren't reflected in rebuilt images.

### Improved

- Added comprehensive troubleshooting section to RUNBOOK.md covering Pydantic Settings, Docker BuildKit caching, and container naming issues.
- Updated fallback test instructions to include health check verification before stopping vLLM.
- Added entries to AVOIDANCE_TABLE.md for configuration management best practices.

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
