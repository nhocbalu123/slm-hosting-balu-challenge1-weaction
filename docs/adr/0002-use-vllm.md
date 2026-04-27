# ADR 0002: Use vLLM as the GPU inference engine

## Status
Accepted

## Context
The challenge requires efficient model serving and production-oriented architecture.
Raw Transformers inference introduces additional engineering complexity and generally lower throughput.

The solution should:
- support OpenAI-compatible APIs,
- provide efficient batching,
- support GPU acceleration,
- minimize custom inference code.

## Decision
Use vLLM as the primary GPU inference engine.

The FastAPI wrapper proxies requests to vLLM through an internal service network.

## Consequences
### Positive
- OpenAI-compatible serving interface.
- Better throughput and latency.
- Reduced implementation complexity.
- Industry-relevant deployment experience.

### Negative
- GPU dependency for optimal performance.
- Additional Docker orchestration complexity.
