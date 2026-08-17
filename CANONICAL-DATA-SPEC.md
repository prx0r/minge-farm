# CANONICAL DATA SPEC — every schema the lab writes, and its strict validator

*2026-08-16 · The canonical reference for every data file the lab produces. Each schema is the exact field
contract (field → type/format). The strict validator (`agent/validate_data.py`) enforces it deterministically
— a malformed record, missing field, or wrong type is caught. This is how we get EXACT validation: the spec
is the contract, the validator is the gate.*

---

## 1. HOW TO USE THE SPEC

- **Every schema** lives in `pipeline/schemas.py` (machine-readable) and is documented below (human-readable).
- **The gate:** `python3 agent/validate_data.py` validates every real data file against its schema. Exit 0 =
  all valid, 1 = violations. It's wired into `check.py --status`.
- **To validate one record in code:** `from schemas import validate_record; validate_record(rec, 'RUN_RECORD')`.

---

## 2. THE SCHEMAS (the exact contracts)

### 2.1 RUN_RECORD — `data/corpus/runs/<sha256>.json` (the content-addressed run record)
The provenance core. Every headline number is a run record here.

| Field | Type/format | Notes |
|---|---|---|
| `step` | string | the lab step (proof/verify/benchmark/...) |
| `run_signature` | sha256 (64-hex) | `sha256(gold‖code‖config)` — the reproducibility key |
| `out_hash` | sha256 (64-hex) | hash of (metrics ‖ raw) |
| `gold_hash` | sha256 (64-hex) | content-address of the fixed gold |
| `code_sha` | sha256 (64-hex) | hash of the eval/metric code |
| `config_sha` | sha256 (64-hex) | hash of the resolved config |
| `config` | dict | the run config (model, n, ...) |
| `metrics` | dict | the computed numbers |
| `git` | dict | `{commit, diff}` — code state |
| `ts` | ISO-8601 | timestamp |
| `nanopublication` | dict | `{assertion, evidence, provenance}` |
| `kind` | string | eigenius ladder: Declared/Observed/Derived/Verified (optional) |

### 2.2 EXPERIMENT — `data/corpus/registries/experiments.jsonl` (a logged translation experiment)
> Validated only on OUR records (those with `avg_chrF`) — the file mixes with another lane's.

| Field | Type | Notes |
|---|---|---|
| `experiment_id` | string | `EXP-<layer>-<config>-<hash>-<ts>` |
| `layer` | string | L2/T1/C1/... |
| `config_key` | string | l2-flash, etc. |
| `model` | string | mimo-v2.5 |
| `test` | string | mitrasamgraha |
| `data_hash` | string | content hash of the test set |
| `n` | int | number of verses |
| `date` | ISO-8601 | timestamp |
| `avg_chrF` | float | mean character-F |
| `avg_bleu1` | float | mean BLEU-1 |
| `rows` | list | per-verse rows |

### 2.3 AGENT_RUN — `data/corpus/registries/agent-runs.jsonl` (an orchestrator step)
| Field | Type |
|---|---|
| `step` | string |
| `ts` | ISO-8601 |

### 2.4 WATCHDOG — `data/corpus/registries/watchdog.jsonl` (a watchdog cycle)
| Field | Type |
|---|---|
| `ts` | ISO-8601 |

### 2.5 BENCHMARK_REGISTRY — `data/benchmark-registry.json` (the legitimate benchmark gold)
| Field | Type |
|---|---|
| `version` | string |
| `created` | ISO-8601 |
| `passages` | list of PASSAGE |
| `n_passages` | int |
| `decontamination` | dict |
| `lineage_requirements` | list |
| `manifest_hash` | sha256 |

### 2.6 PASSAGE — an entry in benchmark-registry.json `passages[]`
| Field | Type | Notes |
|---|---|---|
| `passage_id` | string | `<school>:<source>:<hash10>` |
| `hash` | sha256 | content-address |
| `source` | string | the Sanskrit |
| `school` | string | Pratyabhijñā/Nyāya/... |
| `period` | string | Tantric/Classical/... |
| `tier` | int | difficulty 1-4 |
| `genre` | string | sastra |
| `source_id` | string | the DCS file |
| `source_date` | string | provenance date |
| `license` | string | CC-BY 4.0 |
| `term_density` | float | specialist-term % |
| `n_terms` | int | count |

### 2.7 CHECKPOINT + CHECKPOINT_ENTRY — `data/checkpoints.json` (the vision→checkpoint DAG)
- `CHECKPOINT`: `{version: string, checkpoints: dict}`
- `CHECKPOINT_ENTRY` (each checkpoint): `{name, effect, gate, prereqs: list, status, ts}`

### 2.8 FINETUNE_PAIR — `data/finetune/*.jsonl` (a LoRA-ready register pair)
| Field | Type | Notes |
|---|---|---|
| `instruction` | string | the register instruction (plain/precise/...) |
| `input` | string | the Sanskrit |
| `output` | string | the register-target English |
| `register` | string | natural/plain/precise/literal |
| `source` | string | gold/render |

### 2.9 TRANSLATION_CLAIM — the proof/verify assertion
| Field | Type |
|---|---|
| `source` | string |
| `candidate` | string |
| `deterministic_gate` | string (PASS/BLOCKED) |
| `blocking` | list |
| `run_signature` | sha256 |

---

## 3. THE STRICT VALIDATOR (`agent/validate_data.py`)

```
python3 agent/validate_data.py          # exit 0 = all data valid, 1 = violations
python3 agent/validate_data.py --json   # machine-readable
```

What it checks (verified):
- **run records** → RUN_RECORD (every field, sha256 format, types).
- **registries** → their schemas; experiments.jsonl validated only on OUR records (discriminator).
- **benchmark-registry.json** → BENCHMARK_REGISTRY + every PASSAGE.
- **checkpoints.json** → CHECKPOINT + every CHECKPOINT_ENTRY.
- **finetune pairs** → FINETUNE_PAIR.

**Proven strictness:** a bad record with a wrong hash, missing field, and wrong type is caught with all
violations listed. The gate is deterministic — it can't be fooled by a plausible-looking record.

---

## 4. THE VALIDATION STACK (all the strict gates)

| Gate | Command | What it enforces |
|---|---|---|
| **Schema** | `agent/validate_data.py` | every data file matches its canonical schema |
| **Provenance** | `agent/verify.py --registry` | every run has a valid signature + nanopublication |
| **Golden** | `agent/audit.py --bench <name>` | recompute on fixed gold; fail on mismatch |
| **Proof** | `agent/run.py --step verify` | the Pāṭala proof gate + gold anti-hallucination |
| **Manifest** | `check.py --status` | every doc/script registered + resolves |

---

## 5. THE RULE

> **A data file is valid only if it matches its canonical schema; a headline number is real only if it
> traces to a valid run record on fixed gold.** `validate_data.py` makes the schema enforceable; `verify` +
> `audit` make the number honest. If it fails a gate, it isn't real.
