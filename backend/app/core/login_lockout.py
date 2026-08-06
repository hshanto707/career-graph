"""Login rate-limit / lockout — B3 hardening (docs/current-status.md
Milestone 4).

An in-memory, per-process sliding-window failure counter keyed by
normalized email: after `MAX_ATTEMPTS` failed logins within
`WINDOW_SECONDS`, further attempts for that email are rejected with 429
until the window elapses, without needing to know whether the account
exists (mirrors `_INVALID_CREDENTIALS_MESSAGE`'s "never leak which case
occurred" principle in app/routers/auth.py).

Deliberately simple, not a production-grade distributed rate limiter: state
is per-process and lost on restart, and does not survive multiple backend
replicas sharing no common store. That's an explicit, honest scope
decision (this demonstrates the control exists per test-plan.md /
docs/current-status.md Milestone 4, not a claim of production-hardened
infra) -- a real deployment would back this with Redis or the same
Postgres instance already in use. A successful login clears the counter
for that email immediately.
"""
from __future__ import annotations

import time

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 300  # 5 minutes

_failures: dict[str, list[float]] = {}


def _prune(email: str, now: float) -> list[float]:
    recent = [t for t in _failures.get(email, []) if now - t < WINDOW_SECONDS]
    if recent:
        _failures[email] = recent
    else:
        _failures.pop(email, None)
    return recent


def seconds_until_unlocked(email: str) -> float:
    """0 if not currently locked out, else how many seconds remain."""
    now = time.time()
    recent = _prune(email, now)
    if len(recent) < MAX_ATTEMPTS:
        return 0.0
    oldest_in_window = min(recent)
    remaining = WINDOW_SECONDS - (now - oldest_in_window)
    return max(remaining, 0.0)


def record_failure(email: str) -> None:
    now = time.time()
    recent = _prune(email, now)
    recent.append(now)
    _failures[email] = recent


def record_success(email: str) -> None:
    _failures.pop(email, None)


def reset_all() -> None:
    """Test-only helper -- clears all lockout state between test cases so
    one test's failed-login attempts can't bleed into another's."""
    _failures.clear()
