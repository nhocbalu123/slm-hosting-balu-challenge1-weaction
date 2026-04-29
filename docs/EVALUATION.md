# SLM Evaluation — Qwen3.5-0.8B

> **Status: results pending.**
> This document defines the evaluation methodology and prompt set. Fill in the output, latency, and provider columns after running the stack. Fabricated numbers have been intentionally omitted.

Stack under test (as described in [RUNBOOK.md](RUNBOOK.md)):
- **Primary**: vLLM (GPU) serving `Qwen/Qwen3.5-0.8B`
- **Fallback**: Ollama (CPU) serving `qwen3.5:0.8b`
- API wrapper: FastAPI gateway through Nginx at `http://localhost` (or direct local FastAPI at `http://localhost:8080`)

All timings should be measured as wall-clock from `POST /v1/chat/completions` to last byte (non-streaming), using `curl -w "%{time_total}"` or equivalent.

---

## Sample prompts

Run each prompt with `max_tokens=512`, `temperature=0.7`. Record the truncated output, measured latency, and which provider served the request (check the `X-LLM-Provider` response header).

| # | Prompt | Output (truncated) | Latency | Provider |
|---|--------|--------------------|---------|----------|
| 1 | `"What is the capital of Vietnam?"` | | | |
| 2 | `"Write a Python function that reverses a string."` | | | |
| 3 | `"Summarise the water cycle in two sentences."` | | | |
| 4 | `"Translate 'Good morning' into French, Spanish, and Japanese."` | | | |
| 5 | `"What is 17 × 34?"` | | | |
| 6 | `"List three pros and cons of microservices."` | | | |
| 7 | `"Write a haiku about a neural network."` | | | |
| 8 | `"Explain why gradient descent can get stuck in local minima."` | | | |

Prompt 8 (or any long-reasoning prompt) is a good candidate to run again after stopping vLLM (`docker compose stop vllm-qwen`) to confirm the Ollama fallback serves the request and the `X-LLM-Provider` header changes to `ollama`.

---

## Fallback trigger conditions

Document which scenario you used to demonstrate the fallback:

- [ ] Stopped vLLM container: `docker compose -f docker/docker-compose.yml stop vllm-qwen`
- [ ] Reduced `GPU_MEMORY_UTILIZATION` to force vLLM OOM exit
- [ ] Other: ___

---

## Latency profile

Fill in after measurement. Suggested method: run the smoke test 10 times for each scenario and note min/p50/p95.

| Scenario | p50 | p95 | Notes |
|----------|-----|-----|-------|
| vLLM (GPU) | | | `max_tokens=512`, `temperature=0.7` |
| Ollama (CPU) | | | Same parameters |
| Cold-start (first request after vLLM load) | | | CUDA kernel warm-up |

---

## Limitations of using a 0.8B SLM

These are known constraints of sub-1B parameter models generally, independent of measurement:

| Limitation | Expected behaviour |
|------------|--------------------|
| **Factual precision** | Confident-sounding but occasionally wrong on obscure facts; no retrieval augmentation. |
| **Multi-step arithmetic** | Correct for single operations; degrades on multi-step word problems beyond ~3 steps. |
| **Long context** | `MAX_MODEL_LEN` capped at 2048 tokens for GPU memory reasons; cannot process long documents. |
| **Instruction following** | Simple instructions followed reliably; nested or conditional instructions sometimes collapse. |
| **Code quality** | Short utility functions (≤ 20 lines) are generally correct; complex algorithms with edge cases produce plausible-looking but buggy code. |
| **No tool use / function calling** | The 0.8B variant does not reliably emit valid JSON for tool calls. |

These are expected constraints. The project is an **infrastructure and serving showcase** — the model can be swapped for a larger one by changing `VLLM_MODEL` and `FALLBACK_MODEL` in `.env`.
