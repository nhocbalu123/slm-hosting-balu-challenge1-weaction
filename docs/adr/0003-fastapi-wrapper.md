# ADR 0003: Use FastAPI as the API gateway and wrapper

## Status
Accepted

## Context
The challenge explicitly requires a wrapper layer implementing:
- validation,
- authentication,
- logging,
- health checks,
- timeout handling,
- fallback behavior.

The wrapper must remain lightweight and easy to extend.

## Decision
Use FastAPI as the API wrapper and gateway service.

The wrapper:
- validates requests,
- proxies chat completion requests,
- performs health checks,
- implements fallback routing,
- emits structured JSON logs.

## Consequences
### Positive
- Async-first framework.
- Strong developer productivity.
- Easy OpenAPI documentation generation.
- Clean middleware support.

### Negative
- Additional network hop.
- Requires careful timeout management.
