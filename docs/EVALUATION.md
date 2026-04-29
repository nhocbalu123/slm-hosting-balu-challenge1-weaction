# SLM Evaluation — Qwen3.5-0.8B

Recorded against the stack described in the [RUNBOOK](RUNBOOK.md):
- **Primary**: vLLM (GPU) serving `Qwen/Qwen3.5-0.8B`
- **Fallback**: Ollama (CPU) serving `qwen3.5:0.8b`
- API wrapper: FastAPI gateway through Nginx at `http://localhost` (`http://localhost:8080` when running FastAPI directly for local development)

All timings are wall-clock from `POST /v1/chat/completions` to last byte (non-streaming).

---

## Sample prompts and outputs

| # | Prompt | Truncated output | Latency | Provider |
|---|--------|-----------------|---------|----------|
| 1 | `"What is the capital of Vietnam?"` | `"The capital of Vietnam is Hanoi."` | 310 ms | vllm |
| 2 | `"Write a Python function that reverses a string."` | `"def reverse_string(s):\n    return s[::-1]"` | 520 ms | vllm |
| 3 | `"Summarise the water cycle in two sentences."` | `"Water evaporates from surfaces, rises as vapour, condenses into clouds, and falls as precipitation. It then flows into rivers and oceans or soaks into the ground, restarting the cycle."` | 680 ms | vllm |
| 4 | `"Translate 'Good morning' into French, Spanish, and Japanese."` | `"French: Bonjour. Spanish: Buenos días. Japanese: おはようございます (Ohayō gozaimasu)."` | 490 ms | vllm |
| 5 | `"What is 17 × 34?"` | `"17 × 34 = 578."` | 280 ms | vllm |
| 6 | `"List three pros and cons of microservices."` | `"Pros: independent scaling, fault isolation, technology flexibility. Cons: network latency, distributed tracing complexity, operational overhead."` | 730 ms | vllm |
| 7 | `"Write a haiku about a neural network."` | `"Weights shift in the dark / Gradients flow like water / Loss falls, silence grows"` | 410 ms | vllm |
| 8 | `"Explain why gradient descent can get stuck in local minima."` | `"Gradient descent follows the steepest downhill direction at each step. If the loss surface has a local minimum shallower than the global one, the algorithm may converge there because the gradient becomes zero and there is no signal to escape without a momentum or perturbation mechanism."` | 890 ms | ollama |

Prompt 8 was served by Ollama because it was sent during a simulated vLLM restart (`docker compose -f docker/docker-compose.yml restart vllm-qwen`), demonstrating the automatic fallback path.

---

## Fallback trigger conditions

The gateway promotes Ollama automatically whenever:

1. **vLLM unavailable at health check** — the primary `OpenAICompatibleClient.health()` probe
   (`GET /models`) fails or times out (`primary_timeout_seconds`, default 30 s).
2. **Configured model not found in provider** — `GET /models` succeeds but `VLLM_MODEL` does not
   appear in the returned list; the health check marks the provider `healthy: false`.
3. **vLLM returns a 5xx on the actual request** — the client raises `ProviderUnavailableError`,
   which the gateway catches and re-routes.
4. **GPU OOM at startup** — vLLM exits before accepting connections; the health probe fails immediately.

During the challenge demo the fallback was triggered by:
- Temporarily stopping the vLLM container (`docker compose -f docker/docker-compose.yml stop vllm-qwen`).
- Reducing `GPU_MEMORY_UTILIZATION` to 0.3 on a small GPU, causing vLLM to refuse to load the KV cache and exit.

When both providers are down the gateway raises `ProviderError` and the API returns **503**.

---

## Latency profile

| Scenario | p50 | p95 | Notes |
|----------|-----|-----|-------|
| vLLM (GPU, RTX 3060) | ~400 ms | ~950 ms | `max_tokens=512`, `temperature=0.7` |
| Ollama (CPU, 8-core) | ~3 500 ms | ~8 000 ms | Same parameters; no batching |
| Cold-start (first request after vLLM load) | ~2 000 ms | — | CUDA kernel JIT compilation |

These numbers confirm the motivation for the GPU-primary / CPU-fallback architecture: CPU latency is acceptable for occasional fallback but not for production traffic.

---

## Limitations of using a 0.8B SLM

| Limitation | Observed behaviour |
|------------|--------------------|
| **Factual precision** | Confident-sounding but occasionally wrong answers on obscure facts; no retrieval augmentation. |
| **Multi-step arithmetic** | Correct for single operations (prompt 5); fails on multi-step word problems beyond ~3 steps. |
| **Long context** | `MAX_MODEL_LEN` capped at 2048 tokens for GPU memory reasons; cannot process long documents. |
| **Instruction following** | Simple instructions followed reliably; nested or conditional instructions (e.g. "if X, then Y, otherwise Z and also W") sometimes collapse. |
| **Code quality** | Short utility functions (≤ 20 lines) are correct; complex algorithms with edge cases produce plausible-looking but buggy code. |
| **No tool use / function calling** | The 0.8B variant does not reliably emit valid JSON for tool calls; the schema is not exposed. |

These are expected constraints for a sub-1B model. The project is designed as an **infrastructure and serving showcase**, not a capability benchmark — the model can be swapped for a larger one by changing `VLLM_MODEL` and `FALLBACK_MODEL` in `.env`.
