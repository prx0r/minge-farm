# HERMES MCP / API — how a hermes agent calls sanskritbenchy

*2026-08-16 · The machine interface an agent uses to drive the lab. hermes runs the lab via a skill
(`skills/sanskrit-benchy`), kanban (board `sanskritbenchy`), cron (watchdog), and the orchestrator
(`agent/run.py`). This doc is the MCP/API reference — every call, its arguments, and what it returns.*

---

## 1. THE API SURFACE (what a hermes agent calls)

### 1.1 The orchestrator — `agent/run.py`
The single entry point for any lab step. Every call returns machine-readable output + logs a content-
addressed run record.

| Call | Arguments | Returns |
|---|---|---|
| `python3 agent/run.py --step validate` | `--n` `--m` `--test` (`mitrasamgraha`/`frontier:saamayik`/…) | Kendall's-tau table (chrF vs bleu vs semantic-judge) |
| `--step eval` | `--n` `--judge` | Mitrasamgraha eval (chrF/bleu/semantic) |
| `--step hypothesis` | `--rounds` `--n` `--test` | observe→hypothesize→test→keep loop |
| `--step proof` | `--source` `--candidate` | the deterministic Pāṭala proof gate (PASS/BLOCK + lineage) |
| `--step report` | — | the experiment leaderboard |
| `--step watchdog` | `--test` `--rounds` `--n` | a full autonomous cycle |

### 1.2 The provenance ledger — `pipeline/run_recorder.py`
- `run_recorder.RunRecorder().record(step, gold, config, metrics, raw, assertion)` → a content-addressed
  run record `{run_signature, out_hash, gold_hash, code_sha, config_sha, git, nanopublication}`.
- `run_signature(gold, config)` = `sha256(gold_hash || code_sha || config_sha)` — the reproducibility key.

### 1.3 The golden audit — `agent/audit.py` (the executable ONE RULE)
- `python3 agent/audit.py --list` → all content-addressed runs.
- `python3 agent/audit.py --bench <name> --record` → (re)compute + write the golden baseline.
- `python3 agent/audit.py --bench <name>` → recompute on fixed gold; **fail if it doesn't match the golden.**

### 1.4 The paper build — `agent/paper_build.py`
- `python3 agent/paper_build.py` → injects the real numbers from run records into a `.tex` and compiles.
  The PDF cannot state a number not in the log (number-inject templating).

### 1.5 The watchdog — `agent/watchdog.py`
- `python3 agent/watchdog.py --test <name>` → validate → hypothesize → report cycle, logged.

---

## 2. THE RECIPES (proven call sequences for common goals)

### Recipe A — "prove our metric beats chrF" (the first falsifiable number)
```bash
cd /root/sanskritbenchy
python3 agent/run.py --step validate --n 2 --m 3 --test mitrasamgraha   # tau on our gold
python3 agent/run.py --step validate --n 2 --m 3 --test frontier:saamayik  # external validation
python3 agent/audit.py --bench mitrasamgraha --record                    # freeze the golden baseline
```
→ read the tau in the output; if semantic/combined > chrF, that's the proof (log it as a nanopublication).

### Recipe B — "run the self-improvement loop"
```bash
cd /root/sanskritbenchy
python3 pipeline/hypothesis_lab.py --propose        # what failed + why (error families)
python3 agent/run.py --step hypothesis --rounds 1 --n 3   # test the hypotheses on fixed gold
python3 agent/run.py --step report                  # did tau/chrF improve?
```

### Recipe C — "prove a specific translation is faithful" (the Pāṭala proof)
```bash
cd /root/sanskritbenchy
python3 agent/run.py --step proof --source "śivāya namaḥ" --candidate "Homage to Shiva"
# → deterministic_gate: PASS + result_id (lineage) — the verifiable Pāṭala proof
```

### Recipe D — "generate the paper from the logged results"
```bash
cd /root/sanskritbenchy
python3 agent/run.py --step report                  # ensure experiments are logged
python3 agent/paper_build.py                        # inject real numbers → .tex → PDF
```

### Recipe E — "audit for theater" (the anti-fabrication check)
```bash
cd /root/sanskritbenchy
python3 agent/audit.py --list                       # every run has a content-addressed signature
python3 agent/audit.py --bench mitrasamgraha        # recompute on fixed gold; must match golden
```
> Any number that has no run record / fails the golden audit is flagged — that's the anti-theater guard.

---

## 3. THE HONEST RULES (the agent must follow)

1. **Never claim a result without a logged number on fixed gold.** Use `run_recorder` / `agent/run.py`.
2. **Every headline number must be a machine-computed value in a content-addressed run record** — never a
   number that only exists in LLM text. Run `audit.py` to enforce.
3. **Anti-circularity:** the scorer ≠ the generator. Use a deterministic recompute (golden audit) or a
   different model to verify a claim, not the same model that produced it.
4. **Box rules:** 8GB/4-core, ~2GB free. Small samples (n=2–3), one job at a time, background long runs.
5. **The crypto layer proves integrity, never quality.**
6. **Reuse, don't rebuild** (COMET, MTME, MQM, ezkl, risc0).

---

## 4. THE MECHANISMS STOLEN (verified — see `research/AGENTIC-SCIENCE-MECHANISMS.md`)

| Mechanism | Source (verified) | In sanskritbenchy |
|---|---|---|
| Content-addressed run record | DVC (hash inputs→outputs) | `run_recorder.py` |
| Golden-file audit | DVC run-cache / golden-file | `agent/audit.py` |
| Baseline-per-machine | AI-Scientist `run_0` | (to wire) |
| Nanopublication triples | sensein/ECO | `run_recorder.py` nanopublication |
| git+deps auto-capture | wandb Code-Saving | `run_recorder.py` git_state |
| Number-inject paper templating | AI-Scientist v1/v2 | `agent/paper_build.py` |
| Metric-grounded strategy search | AIDE / AI-Scientist-v2 | (roadmap) |
| Tournament over hypotheses | AI Co-Scientist | (roadmap) |
| Ensemble reviewer + anti-circularity | AI-Scientist | (roadmap) |
| Hydra composed-config-as-hash | Hydra | `config_sha()` in run_recorder |
