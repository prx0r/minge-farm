# HERMES IN SANSKRITBENCHY — callable model client + reference

*2026-08-16 · How the lab calls the translation model, verified working. `hermes` v0.20.1 is installed at
`/usr/local/bin/hermes` and the model call WORKS end-to-end (tested: `namaste lokāḥ → "Homage to you,
O worlds."`). This is the crucial unlock — the lab can produce real translations and run the validation
proof without torch/GPU.*

---

## 1. VERIFIED: hermes is installed + callable

```bash
which hermes        # /usr/local/bin/hermes
hermes --version    # Hermes Agent v0.20.1 (2026.8.13)
```

**The model call works** (tested via `pipeline/model.py`):

```bash
cd /root/sanskritbenchy
PYTHONPATH=. python3 -c "
import sys; sys.path.insert(0,'pipeline')
from model import chat
print(chat('You are a Sanskrit translator. Output only the translation.', 'Translate: namaste lokāḥ', model='deepseek-v4-flash', timeout=90))
"
# → 'Homage to you, O worlds.'
```

## 2. HOW THE LAB CALLS THE MODEL

- **`pipeline/model.py`** — the client. Shells out to `hermes -z <prompt> -m deepseek-v4-flash
  --provider opencode-go`. **1M context, no token cap** (max_tokens is deliberately unenforced) — long
  IPVV passages are fine, no truncation needed.
- **`translate(model, source)`** in `experiment_lab.py` — the single-translation call.
- **`semantic_fidelity(model, ref, cand)`** — the LLM-as-judge quality axis (1-5 → 0.8).
- **`judge_rank_pairwise()`** in `validate_benchmark.py` — the WMT-style pairwise judge for Kendall's tau.

**The key call signature** (from `model.py`):
```python
from model import chat
chat(system, user, model="deepseek-v4-flash", timeout=90)
# timeout: pass a LARGE value (600+) for long passages — the earlier "0 candidates" on IPVV was a
# per-call timeout (default 90s), NOT a context limit.
```

## 3. WHY THIS UNBLOCKS THE LAB

- **Validation v2 (the Kendall's-tau proof) can now RUN** — it needs real candidate translations +
  judge calls, both of which `hermes` provides, no torch.
- **The Mitrasamgraha / IPVV gold** can be scored end-to-end today.
- **COMET/LoRA/lemmatization remain hardware-blocked** (need torch/GPU), but the core "does our
  semantic-judge beat chrF" proof does NOT — it just needs hermes, which is here.

## 4. HERMES REFERENCE (bundled)

- `hermes/README.md` — the full Hermes Agent readme (Nous Research).
- `hermes/docs/` — the agent docs (ADR, session-lifecycle, kanban, middleware, observability, security,
  rfcs, design).
- `hermes/providers/` — the model-provider config reference (opencode-go, etc.).

## 5. HOW TO RUN THE PROOF (with hermes)

```bash
cd /root/sanskritbenchy
# the Kendall's-tau validation (real model calls — small sample to be box-friendly)
PYTHONPATH=. timeout 300 python3 pipeline/validate_benchmark.py --n 2 --m 3 --test mitrasamgraha
```

> Box rule: this is an 8GB/4-core box with ~2GB free. Run **small** validation samples (n=2-3, m=3), one
> job at a time, background long runs. Never fire a big validation + a heavy job at once.

*Hermes is the execution kernel of the lab: it produces the translations and the judge signal that the
benchmark proves itself with. The docs are bundled here; the client is `pipeline/model.py`.*
