# ADR 0001: Use Qwen 3.5 as the primary Small Language Model

## Status
Accepted

## Context
The challenge requires hosting a Small Language Model (SLM) behind a production-style API wrapper.
The model must be lightweight enough for local development while still demonstrating modern
LLM deployment practices.

The project also targets AI engineer portfolio presentation, so the chosen model should:
- support local inference,
- integrate cleanly with vLLM,
- have permissive usage,
- provide acceptable instruction-following quality,
- support CPU fallback where possible.

## Decision
Use Qwen 3.5 0.8B as the default model family.

GPU inference uses vLLM-compatible Qwen weights.
CPU fallback uses the Ollama Qwen 3.5 variant.

## Consequences
### Positive
- Small enough for affordable local experimentation.
- Modern instruction-tuned behavior.
- Good ecosystem support.
- Fast startup compared with larger models.

### Negative
- Lower reasoning quality than larger models.
- Limited context and factual reliability compared with frontier models.
