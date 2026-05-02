# SLM Evaluation — Qwen3.5-0.8B

> **Status: evaluation results captured.**
> All eight sample prompts have been tested against the primary vLLM path. Fallback, cold-start, warm-path, and CPU-only latency summaries have also been measured for the recommended prompt.

This evaluation measures the serving stack and gateway behavior. It does not evaluate model training or fine-tuning.

Stack under test (as described in [RUNBOOK.md](RUNBOOK.md)):

- **Primary**: vLLM (GPU) serving `Qwen/Qwen3.5-0.8B`
- **Fallback**: Ollama (CPU) serving `qwen3.5:0.8b`
- **Gateway**: FastAPI API wrapper behind Nginx at `http://localhost`
- **Direct API option**: FastAPI at `http://localhost:8080` only when running `uvicorn` locally or manually publishing the API port; the default Docker Compose path exposes Nginx at `http://localhost`

All timings should be measured as wall-clock time from `POST /v1/chat/completions` until the last response byte is received. Use non-streaming requests and record the value from `curl -w "%{time_total}"` or an equivalent client-side timer.

The recorded tables below are manual evidence from this machine and run. They are not automated benchmark guarantees; rerun the commands on the target hardware before quoting numbers elsewhere.

---

## 1. Evaluation goals

Use this document to prove four things:

1. The gateway can serve a successful OpenAI-compatible chat completion.
2. The response identifies which provider handled the request through `X-LLM-Provider`.
3. The vLLM GPU path and Ollama CPU fallback path both work.
4. The latency and model-quality trade-offs are documented honestly for a sub-1B model.

Record only results that you personally observe from the running stack. If a scenario cannot be tested on the available machine, mark it as `not tested` and explain why.

---

## 2. Prerequisites

Run commands from the repository root in Git Bash on Windows. Full setup, troubleshooting, and screenshot instructions are in [RUNBOOK.md](RUNBOOK.md) and [screenshots/README.md](screenshots/README.md).

Stacks used for this evaluation:

```bash
# GPU stack with fallback
docker compose -f docker/docker-compose.yml --profile fallback up --build -d

# CPU-only comparison stack
docker compose -f docker/docker-compose.cpu.yml up --build -d
```

Before measuring, confirm `curl -s http://localhost/v1/health -H 'X-API-Key: dev-balu-key' | jq` shows the expected active provider. Use `python -m json.tool` if `jq` is unavailable.

---

## 3. Request template

Use non-streaming requests with the same generation settings unless a scenario says otherwise:

- `max_tokens`: `512`
- `temperature`: `0.7`
- `stream`: omitted or `false`
- Auth header: `X-API-Key: dev-balu-key` when `API_KEYS` is enabled

Minimal timing request:

```bash
curl -sS -D /tmp/eval-headers.txt -o /tmp/eval-body.json \
  -w 'TIME_TOTAL=%{time_total}s\n' \
  http://localhost/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: dev-balu-key' \
  -d '{
    "model": "qwen3.5-0.8b",
    "messages": [
      {"role": "user", "content": "What is the capital of Vietnam?"}
    ],
    "max_tokens": 512,
    "temperature": 0.7
  }' && \
sed -n '1p;s/^x-llm-provider:[[:space:]]*/X-LLM-Provider: /Ip;s/^x-request-id:[[:space:]]*/x-request-id: /Ip' /tmp/eval-headers.txt && \
jq . /tmp/eval-body.json
```

Capture the HTTP status, `X-LLM-Provider`, `TIME_TOTAL`, assistant message, and any unusual timeout, `429`, `503`, or malformed response.

---

## 4. Sample prompt results

Run each prompt once against the healthy primary path first. Then rerun at least one reasoning prompt after triggering fallback.

Recorded primary-path results:


| #   | Prompt                                                           | Output (truncated)                                                                                  | Latency     | Provider | Notes                                                                                                                                                                                                                                                        |
| --- | ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ----------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | `"What is the capital of Vietnam?"`                              | `The capital of Vietnam is **Hanoi**.`                                                              | `0.753457s` | `vllm`   | Pass. `HTTP/1.1 200 OK`; request id `9f309bb4ea5912bf69e84245de867fb2`. The answer is factually correct, though it adds extra unsupported detail about population and institutions.                                                                          |
| 2   | `"Write a Python function that reverses a string."`              | `def reverse_string(s: str) -> str: return s[::-1]`                                                 | `1.718600s` | `vllm`   | Partial. `HTTP/1.1 200 OK`; request id `61d8ebee19a13ff12caee55310309af8`. The core code is syntactically valid, but the explanation incorrectly says strings can be reversed in place and suggests non-existent `str.__rev__`.                              |
| 3   | `"Summarise the water cycle in two sentences."`                  | `The water cycle is the continuous movement of water...`                                            | `1.172061s` | `vllm`   | Partial. `HTTP/1.1 200 OK`; request id `753ce8bb0282a018d7093cc7c007016e`. The content is accurate, but it returns one sentence instead of the requested two.                                                                                                |
| 4   | `"Translate 'Good morning' into French, Spanish, and Japanese."` | `French: "Bonjour"; Spanish: "Buenos días"; Japanese: "おはようございます"`                                  | `0.786431s` | `vllm`   | Pass. `HTTP/1.1 200 OK`; request id `56daa1a8f8982743c4ec6a583e32f750`. The answer provides correct translations in all requested languages.                                                                                                                 |
| 5   | `"What is 17 × 34?"`                                             | `Answer: 578`                                                                                       | `1.943797s` | `vllm`   | Partial. `HTTP/1.1 200 OK`; request id `bb5fed1f5582bf20cdb8214ab5b4079d`. The final arithmetic answer is correct, but the optional long multiplication block incorrectly shows `5100` for `17 * 30`.                                                        |
| 6   | `"List three pros and cons of microservices."`                   | `Scalability and Flexibility; Decoupling and Maintainability; Complexity and Deployment Hurdles...` | `3.080277s` | `vllm`   | Partial. `HTTP/1.1 200 OK`; request id `c2cc7143d9d8d05f4677e78a31726578`. The answer is relevant and structured, but it provides two pros and two cons instead of three pros and three cons.                                                                |
| 7   | `"Write a haiku about a neural network."`                        | `Silent neurons blink, / Data flows in a stream, / Code whispers in the dark.`                      | `0.416870s` | `vllm`   | Partial. `HTTP/1.1 200 OK`; request id `44376d83838e5426aa5ecfd3c6a99190`. The answer is relevant and three lines, but it does not follow a strict 5-7-5 syllable pattern.                                                                                   |
| 8   | `"Explain why gradient descent can get stuck in local minima."`  | `Gradient descent (GD) is a powerful optimization algorithm...`                                     | `4.373607s` | `vllm`   | Fail. `HTTP/1.1 200 OK`; request id `400ef0782aff04eea230ee466887a364`. The response hit `max_tokens=512` with `finish_reason: length`, was truncated mid-sentence, and contains incorrect claims about escaping local minima and gradients at local minima. |


Quality scoring guidance:

- **Pass**: The answer is correct enough for a demo and follows the requested format.
- **Partial**: The answer is usable but misses a detail, format constraint, or edge case.
- **Fail**: The answer is wrong, empty, unrelated, or not parseable.

When recording output, keep only the first one to three useful lines. Do not paste a full long completion unless the mistake is important to show.

---

## 5. Fallback validation

Prompt 8 is a good fallback test because it is long enough to show real generation while still being easy to judge.

Start from the GPU stack with the fallback profile enabled, confirm `/v1/health` is `ok`, then stop vLLM:

```bash
docker compose -f docker/docker-compose.yml --profile fallback up -d
curl -s http://localhost/v1/health -H 'X-API-Key: dev-balu-key' | jq
docker compose -f docker/docker-compose.yml stop vllm-qwen
curl -s http://localhost/v1/health -H 'X-API-Key: dev-balu-key' | jq
```

Expected fallback health result:

- Overall status is usually `degraded`.
- `primary.healthy` is `false`.
- `fallback.healthy` is `true`.
- Chat responses use `X-LLM-Provider: ollama`.

Observed fallback result:

- `HTTP/1.1 200 OK`
- `X-LLM-Provider: ollama`
- `x-request-id: 1b39f7ec404d0b2805a77e9b6502bf66`
- `TIME_TOTAL=46.850576s`
- Model: `qwen3.5:0.8b`
- Prompt: `"Explain why gradient descent can get stuck in local minima."`
- Result: fail. The request reached Ollama, but `choices[0].message.content` was empty, reasoning text was exposed in `choices[0].message.reasoning`, and the completion stopped at `finish_reason: length` after `512` completion tokens.

Restore vLLM when fallback testing is finished:

```bash
docker compose -f docker/docker-compose.yml start vllm-qwen
```

---

## 6. Latency profile

Run at least 10 requests for each scenario you can test and calculate min, p50, and p95. Use the same prompt and generation settings for all runs so the numbers are comparable.

Recommended prompt: `Explain why gradient descent can get stuck in local minima.`

Reusable timing pattern:

```bash
mkdir -p /tmp/slm-latency
rm -f "/tmp/slm-latency/${SCENARIO}-times.txt"

for i in {1..10}; do
  echo "$SCENARIO run $i" >&2
  curl -sS -o "/tmp/slm-latency/${SCENARIO}-body-$i.json" \
    -D "/tmp/slm-latency/${SCENARIO}-headers-$i.txt" \
    -w "%{time_total}\n" \
    http://localhost/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -H 'X-API-Key: dev-balu-key' \
    -d '{
      "model": "qwen3.5-0.8b",
      "messages": [
        {"role": "user", "content": "Explain why gradient descent can get stuck in local minima."}
      ],
      "max_tokens": 512,
      "temperature": 0.7
    }'
done | tee "/tmp/slm-latency/${SCENARIO}-times.txt"
```

Confirm the provider header from at least one measured response:

```bash
sed -n '1p;s/^x-llm-provider:[[:space:]]*/X-LLM-Provider: /Ip;s/^x-request-id:[[:space:]]*/x-request-id: /Ip' "/tmp/slm-latency/${SCENARIO}-headers-10.txt"
```

Summarize any timing file by changing `TIMES_FILE`:

```bash
TIMES_FILE=/tmp/slm-latency/vllm-warm-times.txt python - <<'PY'
import os
from pathlib import Path

path = Path(os.environ["TIMES_FILE"])
values = sorted(float(line.strip()) for line in path.read_text().splitlines() if line.strip())

def percentile(sorted_values, pct):
    if not sorted_values:
        return None
    index = round((len(sorted_values) - 1) * pct)
    return sorted_values[index]

print(f"count={len(values)}")
print(f"min={values[0]:.3f}s")
print(f"p50={percentile(values, 0.50):.3f}s")
print(f"p95={percentile(values, 0.95):.3f}s")
print(f"max={values[-1]:.3f}s")
PY
```

Scenario notes:

- `vllm-warm`: start the GPU stack, confirm `primary.healthy: true`, send one warm-up request, then measure.
- `vllm-cold`: restart `vllm-qwen` before each sample and wait until `primary.healthy` is true.
- `ollama-fallback`: start the GPU stack with fallback, stop `vllm-qwen`, confirm `primary.healthy: false` and `fallback.healthy: true`, then measure.
- `cpu-only`: start `docker/docker-compose.cpu.yml`, confirm `active_provider: "ollama"`, then measure.

Cold-start wait command used:

```bash
until curl -fsS http://localhost/v1/health -H 'X-API-Key: dev-balu-key' \
  | python -c 'import json,sys; data=json.load(sys.stdin); sys.exit(0 if data.get("primary", {}).get("healthy") else 1)'; do
  sleep 5
done
```

Observed latency summary:


| Scenario        | min     | p50     | p95     | Provider | Notes                                                                                       |
| --------------- | ------- | ------- | ------- | -------- | ------------------------------------------------------------------------------------------- |
| vLLM warm path  | 4.730s  | 4.811s  | 5.231s  | `vllm`   | `max_tokens=512`, `temperature=0.7`; exclude first cold request.                            |
| vLLM cold start | 40.983s | 49.410s | 55.621s | `vllm`   | First request after vLLM finishes loading; CUDA/kernel warm-up may affect latency.          |
| Ollama fallback | 40.173s | 46.138s | 59.216s | `ollama` | 10-run fallback profile after stopping vLLM; same prompt and request settings.              |
| CPU-only stack  | 35.060s | 37.771s | 70.072s | `ollama` | 10-run CPU-only compose profile; first request was slowest at `70.072s`.                    |


When interpreting latency, compare like-for-like scenarios. The warm vLLM path is the fastest steady-state path in this run. CPU-only Ollama is much slower than warm vLLM, but its `p50` is lower than the stopped-primary fallback profile. The CPU-only `p95` is the highest because the first request took `70.072s`. Non-streaming latency includes generation time, so output length and whether the response hit `max_tokens` strongly affect the result.

---

## 7. Evidence to save

Keep evidence in `docs/screenshots/` using the screenshot checklist in [screenshots/README.md](screenshots/README.md).

For this evaluation, save screenshots or terminal evidence for successful chat, healthy provider state, fallback/degraded state, Ollama provider header, latency summaries, FastAPI JSON logs, and Nginx access logs. Useful commands:

```bash
docker compose -f docker/docker-compose.yml logs api --tail=100
docker compose -f docker/docker-compose.yml logs nginx --tail=100
```

---

## 8. Limitations of using a 0.8B SLM

These are known constraints of sub-1B parameter models generally, independent of measurement:


| Limitation                                  | Expected behaviour                                                                             | How to evaluate                                                                                      |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Factual precision**                       | Confident-sounding but occasionally wrong on obscure facts; no retrieval augmentation.         | Ask simple facts and verify against trusted sources. Avoid using the model as the source of truth.   |
| **Multi-step arithmetic**                   | Correct for single operations; degrades on multi-step word problems beyond about three steps.  | Include one simple arithmetic prompt and one optional multi-step prompt. Record any reasoning error. |
| **Long context**                            | `MAX_MODEL_LEN` is capped for GPU memory reasons; long documents may be truncated or rejected. | Keep evaluation prompts short unless specifically testing context limits.                            |
| **Instruction following**                   | Simple instructions are followed more reliably than nested or conditional instructions.        | Check whether the answer obeys requested length, language, and format.                               |
| **Code quality**                            | Short utility functions are often plausible; complex algorithms with edge cases can be buggy.  | Run generated code or inspect it carefully before marking it as successful.                          |
| **No reliable tool use / function calling** | The 0.8B variant does not reliably emit strict JSON for tool calls.                            | Do not evaluate it as a production function-calling model.                                           |
| **Hallucination risk**                      | The model can invent package names, citations, APIs, or implementation details.                | Treat unsupported specifics as failures unless verified.                                             |


These are expected constraints. This project is an **infrastructure and serving showcase**: the gateway, health checks, fallback, logging, and rate limiting are the main production patterns. To swap models, update the matching download, serving, and wrapper settings in `.env`, especially `MODEL_ID`, `MODEL_LOCAL_DIR`, `VLLM_MODEL_PATH`, `PUBLIC_MODEL_NAME`, `VLLM_MODEL`, `OLLAMA_MODEL`, and `FALLBACK_MODEL`.

---

## 9. Final evaluation summary

Final answers based on the observed runs:


| Question                                         | Answer                                                                                                                                                                                                                                  |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Was the primary vLLM path tested?                | Yes, all eight sample prompts returned `HTTP/1.1 200 OK` with `X-LLM-Provider: vllm`.                                                                                                                                                   |
| Was the Ollama fallback path tested?             | Yes, prompt 8 returned `HTTP/1.1 200 OK` with `X-LLM-Provider: ollama` after stopping vLLM. The repeated fallback latency loop captured 10 requests.                                                                                    |
| Which prompt had the best answer?                | Prompt 1 currently has the cleanest recorded answer; it correctly answered `Hanoi`.                                                                                                                                                     |
| Which prompt had the weakest answer?             | Prompt 8 was weakest: it hit the token limit, was truncated, and included incorrect reasoning about local minima.                                                                                                                       |
| What was the fastest measured p50?               | vLLM warm path at `4.811s`.                                                                                                                                                                                                             |
| What was the slowest measured p95?               | CPU-only stack at `70.072s`, caused by the slow first request in the 10-run profile.                                                                                                                                                    |
| Any failures, timeouts, or rate limits observed? | No transport failures or timeouts were observed during the evaluation prompts. The separate rate-limit proof did observe `429` responses; prompt 8 failures were model-quality/token-limit failures, not transport failures.             |
| Overall conclusion                               | The gateway served all eight primary prompts through vLLM and routed to Ollama after stopping vLLM. Warm vLLM was fastest at `4.811s` p50; CPU-only and stopped-primary fallback were much slower.                                      |

Final conclusion: the stack is suitable as an infrastructure and serving showcase for a small local SLM. The gateway, provider headers, health checks, fallback routing, logging evidence, and latency methodology are demonstrated. Model quality remains limited, especially on longer reasoning prompts that hit the token limit.

