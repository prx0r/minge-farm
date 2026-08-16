# RETIRING A DEV PLAN — the repeatable process for closing a build plan honestly

*2026-08-16 · The one repeatable procedure for taking a dev plan from "active" to "retired" (done), so the
project never claims a plan is finished that isn't, and so the next plan starts from verified ground truth.
A plan is RETIRED only when every item's gate PASSES and every deliverable links to a real, validated file.
Read this before closing any dev plan.*

---

## 1. WHY (the problem this solves)

A dev plan (e.g. `DEV-PLAN-NO-GPU.md`) is a list of items with gates. Without a procedure, "done" is a
vague claim: a checkbox ticked, a file that exists. The anti-mess standard says **a number is real only
when it's a logged, content-addressed value on fixed gold, passed by a deterministic gate.** Retiring a plan
must apply the same standard to *the plan itself*. This doc makes the close-out deterministic and repeatable.

## 2. THE DEFINITION OF RETIRED (what "done" means)

A dev plan is **RETIRED** iff ALL of:
1. **Every item's gate PASSES** — a logged, content-addressed run record exists for each number the item claims.
2. **Every deliverable links to a real file** — each file the item says it built exists at the claimed path.
3. **The data validates** — `python3 agent/validate_data.py` exits 0 (0 violations).
4. **The gate is green** — `python3 check.py --status` PASS (docs registered, MANIFEST valid).
5. **Everything is committed** — `git status` clean; the close-out note itself is committed.
6. **A retire banner is added** — the plan gets a `> **RETIRED** — superseded by <next> · <date>` header, kept as history (never deleted).

If ANY of 1-5 fails, the plan is **NOT retired** — either the item is genuinely incomplete (keep it in the
next plan) or the claim is stale (fix the plan/claim, don't mark done).

## 3. THE RETIREMENT CHECKLIST (the exact repeatable steps)

```
cd /root/sanskritbenchy
# 1. box + gate first
python3 agent/ramwatch.py                  # SAFE
python3 check.py --status                  # PASS

# 2. reconcile EVERY item in the plan against reality:
#    for each item: (a) does the gate have a run record? (b) does each claimed file exist?
for f in <claimed files>; do [ -f "$f" ] && echo "OK $f" || echo "MISS $f"; done

# 3. the data + provenance gates
PYTHONPATH=. python3 agent/validate_data.py   # 0 violations
python3 agent/verify.py --registry           # every run valid + content-addressed

# 4. mark the plan retired (banner + item checkboxes), per the file standard:
#    > **RETIRED** — superseded by <next-plan> · <date>
#    tick every [ ] to [x] with the run-signature / file path as evidence

# 5. update the checkpoint DAG (only if a real checkpoint gate advanced) via pipeline/checkpoint.py
# 6. commit everything: the plan banner + any code + the handover delta
git add -A && git commit -m "retire <plan>: <what was validated, evidence>"
```

## 4. THE EVIDENCE CONVENTION (how to link "done" to files)

Every item you mark done must carry a **linkable evidence line**, not a bare checkmark:
```
- [x] <item> — **gate PASSED** run `<run_signature[:12]>` · file `pipeline/<module>.py`
```
- **A gate number** → its content-addressed run record (`data/corpus/runs/<sha>.json`).
- **A deliverable** → its real file path (relative to project root).
- **A data file** → the schema it validates against (`CANONICAL-DATA-SPEC.md`).

This is what makes a retired plan *auditable*: a reviewer can open the run record + the file and confirm the
claim is true, exactly like the ONE RULE requires for every headline number.

## 5. THE N-ITEM RULE (don't fake completion)

A plan with N items is retired when ALL N are done. **Do not retire a plan by silently dropping an
incomplete item.** If an item is blocked (e.g. needs GPU / human gold), it is **carried forward** into the
next plan with its gate unchanged — it is not marked done. The retire banner names what was carried forward.

## 6. THE OUTPUT (what a retirement produces)

1. A retired `DEV-PLAN-*.md` (banner + all `[x]` + evidence links), kept as timestamped history.
2. A **next `DEV-PLAN-*.md`** (the same file standard, new items = what's still open + new work).
3. A checkpoint-DAG update **only if** a real gate advanced.
4. A handover delta (§11) noting the retirement + the next plan.

## 7. THE ONE-LINE RULE

> **A dev plan is retired only when every item's gate has a logged run record, every claimed file exists and
> validates, the gate is green, and it's all committed — with the evidence linkable per item. Otherwise it's
> not done, and the unfinished items carry forward.**
