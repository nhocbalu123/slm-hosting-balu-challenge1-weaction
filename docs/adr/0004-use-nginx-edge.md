# ADR 0004: Use Nginx as the edge reverse proxy

## Status
Accepted

## Context
The project needs a production-style ingress layer that supports:
- reverse proxying,
- rate limiting,
- request forwarding,
- future TLS termination.

The API wrapper itself should remain focused on application concerns.

## Decision
Use Nginx as the edge reverse proxy in front of FastAPI.

Nginx is responsible for:
- ingress traffic,
- request buffering,
- rate limiting,
- upstream forwarding.

## Consequences
### Positive
- Separation of infrastructure and application concerns.
- Industry-standard deployment pattern.
- Simple request throttling support.

### Negative
- Extra infrastructure component to maintain.
- Slightly more complex Docker Compose configuration.
