"""Pāṭala model client — drives the translator model VIA THE HERMES AGENT.

Instead of calling the OpenAI-compatible API directly, we shell out to `hermes -z`
(the agent CLI), which handles model selection, retries, and reliability with its
own infrastructure. We keep ALL the Pāṭala logic here: the lean JSON schemas, the
capability mode (kept for compatibility), the contract-format repair, and parsing.

This means the pipeline's epistemic logic (contracts, schemas, audit) stays ours;
only the "call the model" step is delegated to hermes.
"""
from __future__ import annotations
from pathlib import Path
import json
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Optional

BASE_URL = "https://opencode.ai/zen/go/v1"
DEFAULT_MODEL = "deepseek-v4-flash"
HERMES_BIN = os.environ.get("HERMES_BIN", "hermes")


@dataclass
class ModelResult:
    content: str
    finish_reason: Optional[str] = None
    latency_ms: int = 0
    model: str = ""
    request_id: Optional[str] = None
    raw: Optional[Any] = None


class StageOutputError(Exception):
    """Raised when a core stage returns non-structured (prose) output that was
    required to be JSON. NOT a silent fallback — the state machine must surface it."""


def _killpg(proc: subprocess.Popen) -> None:
    """Kill the whole process group of a hermes child (F3) so a hung call can't orphan
    a `hermes -z` subprocess (as observed: killing the parent left an orphan running)."""
    try:
        gid = os.getpgid(proc.pid)
    except ProcessLookupError:
        return
    try:
        os.killpg(gid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        pass
    try:
        proc.wait(timeout=5)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(gid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    try:
        proc.wait(timeout=5)
    except Exception:
        pass


def _hermes_call(prompt: str, model: str = DEFAULT_MODEL, timeout: int = 120, _retries: int = 1,
                 session: Optional[str] = None) -> str:
    """Run hermes -z with the given prompt; return its stdout (the model response).

    The child runs in its OWN PROCESS GROUP (start_new_session=True); on timeout we
    SIGTERM→SIGKILL the whole group, so no orphaned hermes survives (F3).
    timeout: batch calls (many verses in one context) legitimately take minutes — pass a large
    timeout (600+). Default 120 is for short calls. timeout=0 disables the cap. Overridable via
    HERMES_TIMEOUT. One bounded retry on a timeout (a transient hang may succeed on retry);
    fail-closed beyond that — never block the whole queue.
    session: if given, continue a persistent Hermes session via `--resume SESSION` so the model
    retains the accumulated context across calls (the "long context essential + document as it goes"
    mechanism). Pass the session id returned by the previous call."""
    if timeout == 0:
        timeout = int(os.environ.get("HERMES_TIMEOUT", "0"))
    env = dict(os.environ)
    env.setdefault("HERMES_MODEL", model)
    # The `-z` one-shot must pass the model AND provider EXPLICITLY — config.yaml's provider
    # (opencode-go) is not picked up by `-z` for this model, causing "Provider 'deepseek' set in
    # config.yaml but no API key" / "HTTP 401: Model not supported" on every call. Match the
    # verified working invocation:
    #   hermes -z "<prompt>" -m deepseek-v4-flash --provider opencode-go
    provider = os.environ.get("HERMES_PROVIDER", "opencode-go")
    last = None
    for attempt in range(_retries + 1):
        proc = None
        try:
            cmd = [HERMES_BIN, "-z", prompt, "-m", model, "--provider", provider]
            if session:
                cmd += ["--resume", session]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                env=env, start_new_session=True, cwd=str(Path(__file__).resolve().parents[1]),
            )
            out, _ = proc.communicate(timeout=(timeout if timeout else None))
            return (out or "").strip()
        except subprocess.TimeoutExpired as e:
            last = e
            if proc is not None:
                _killpg(proc)
            if attempt < _retries:
                time.sleep(5)
                continue
            raise
    raise last  # pragma: no cover
    return out


def chat(system: str, user: str, model: str = DEFAULT_MODEL,
         temperature: float = 0.3, max_tokens=None, timeout: int = 120,
         response_format: Optional[dict] = None,
         seed: Optional[int] = None, session: Optional[str] = None) -> str:
    """A single model call via hermes -z. Returns just the text content.

    max_tokens is deliberately UNENFORCED: _hermes_call passes only the prompt +
    model to `hermes -z`, so there is NO token cap on the call. This lets one
    batch carry as many L0 records as possible in a single context. The param is
    kept for API compatibility only. timeout: pass a large value for batch calls.
    session: if given, continue a persistent Hermes session (context retained across calls)."""
    prompt = f"{system}\n\n{user}"
    if response_format is not None:
        prompt += "\n\nReturn ONLY the requested JSON object. No prose, no markdown fences, no commentary."
    return _hermes_call(prompt, model=model, timeout=timeout, session=session)


def chat_result(system: str, user: str, model: str = DEFAULT_MODEL,
                temperature: float = 0.3, max_tokens=None, timeout: int = 120,
                response_format: Optional[dict] = None,
                seed: Optional[int] = None) -> ModelResult:
    """A single model call via hermes -z returning a ModelResult with metadata."""
    t0 = time.time()
    content = chat(system, user, model=model, temperature=temperature,
                   max_tokens=max_tokens, timeout=timeout, response_format=response_format, seed=seed)
    latency = int((time.time() - t0) * 1000)
    return ModelResult(content=content, finish_reason="stop", latency_ms=latency, model=model)


def chat_agentic(system: str, user: str, skills: str = "", max_turns: int = 8,
                 timeout: int = 240, session: str | None = None) -> str:
    """A model call via AGENTIC `hermes chat` (file access + skills) — the CORRECT way.

    Per docs/global/HERMES-CALLING.md, `hermes -z` is blind (no file access, no tools, ~3.8% yield
    on translation). This is the additive fix: call Hermes as an AGENT so it can read the repo, the
    skills, and the reference maps itself.

    session: if given, continue a persistent Hermes session via `--resume SESSION` so context is
    retained across calls (the "long context essential + document as it goes" mechanism).

    Usage:
        from model import chat_agentic
        out = chat_agentic("You are a semantic judge.", "Classify: EQUIVALENT...")

    Reference: pipeline/agentic_translate.py (the working invocation).
    """
    import subprocess
    prompt = f"{system}\n\n{user}"
    provider = os.environ.get("HERMES_PROVIDER", "opencode-go")
    cmd = [HERMES_BIN, "chat", "-Q", "-q", prompt, "--yolo",
           "--max-turns", str(max_turns), "-m", DEFAULT_MODEL, "--provider", provider]
    if skills:
        cmd += ["--skills", skills]
    if session:
        cmd += ["--resume", session]
    # hermes may spawn a lingering grandchild; put it in its own process group so we can kill it
    proc = subprocess.Popen(cmd, cwd=str(Path(__file__).resolve().parents[1]), start_new_session=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        import signal as _signal
        try:
            os.killpg(os.getpgid(proc.pid), _signal.SIGKILL)
        except Exception:
            proc.kill()
        raise TimeoutError(f"chat_agentic timed out after {timeout}s")
    # extract the JSON object if present (hermes -Q may print reasoning before/after it)
    s, e = out.find("{"), out.rfind("}")
    if s >= 0 and e > s:
        return out[s:e + 1]
    return out.strip()


def _extract_json(raw: str) -> dict[str, Any]:
    """Strip fences and parse. Raises ValueError if no object is found."""
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]
    start, end = raw.find("{"), raw.rfind("}")
    if start >= 0 and end > start:
        return json.loads(raw[start:end + 1])
    raise ValueError("no JSON object found in model output")


def parse_json(raw: str, repair_fn=None) -> dict[str, Any]:
    """Parse a model output as JSON, stripping fences and finding the object block.
    If it fails and a repair_fn is given, it runs ONE bounded repair retry (the
    repair must itself return JSON — it never accepts prose)."""
    try:
        return _extract_json(raw)
    except Exception as first_err:
        if repair_fn is not None:
            repaired = repair_fn(raw)
            try:
                return _extract_json(repaired)
            except Exception as repair_err:
                raise ValueError(f"JSON repair failed: {repair_err} (original: {first_err})") from repair_err
        raise ValueError(str(first_err))


# ── structured-output capability (kept for compatibility; hermes handles it) ─

def structured_mode(model: str = DEFAULT_MODEL) -> str:
    """Hermes handles structured output; we report prompt_only (we rely on the
    lean contract + contract validation on our side)."""
    return "prompt_only"


def stage_format(stage: str, model: str = DEFAULT_MODEL) -> Optional[dict]:
    """No native response_format via hermes; rely on the lean contract + prompt."""
    return None


def stage_json_schema(stage: str) -> Optional[dict]:
    """Retained for reference/diagnostics; not sent to hermes."""
    return None


# ── semantic backoff helper (caller uses for empty/contract failures) ───────

def semantic_backoff(attempt: int, max_sleep: int = 20) -> None:
    """Jittered exponential backoff for semantic (empty/contract) retries."""
    import random as _r
    base = min(2 ** attempt, max_sleep)
    time.sleep(base + _r.uniform(0, 1))

