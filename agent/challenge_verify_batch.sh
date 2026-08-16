#!/usr/bin/env bash
# agent/challenge_verify_batch.sh — run the full N1 challenge-set competence gate (T- < T+) as ONE
# backgrounded job, box-safe. Prints progress to a log + writes a content-addressed run record.
#
# Usage (do this only when `python3 agent/ramwatch.py` says SAFE):
#   setsid nohup bash agent/challenge_verify_batch.sh --n 196 > /tmp/sb-challenge-verify.log 2>&1 &
#   echo "PID $!"          # note it — you own it, kill by exact PID
#   ... do real work ...
#   tail -30 /tmp/sb-challenge-verify.log   # check on it later
set -u
cd /root/sanskritbenchy
export PYTHONPATH=.
N="${1:-196}"
echo "=== challenge-set competence gate (T- < T+) at $(date -u +%FT%TZ) ==="
echo "box: $(python3 agent/ramwatch.py 2>&1 | tail -1)"
echo "rows: $N"
echo
python3 agent/challenge_verify.py --n "$N"
code=$?
echo
echo "exit_code=$code (0 = gate PASSED, bad<good ≥90%)"
echo "=== done at $(date -u +%FT%TZ) ==="
exit $code
