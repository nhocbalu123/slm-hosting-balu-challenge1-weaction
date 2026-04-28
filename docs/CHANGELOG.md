# Changelog

All notable changes to this project will be documented in this file.

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

## [0.1.1] - 2026-04-28

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
