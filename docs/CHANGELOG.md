# Changelog

All notable changes to this project will be documented in this file.

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
