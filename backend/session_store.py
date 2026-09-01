"""
In-memory session store for conversation history.

Keyed by customer_id (from the authenticated JWT, never user-supplied),
so one customer can never see or influence another's history.

A real system would use Redis or a database so history survives server
restarts and works across multiple server instances - this in-memory
version resets whenever the FastAPI process restarts, which is fine for
a demo/learning project.
"""

MAX_TURNS = 10  # keep the last N exchanges per customer, to bound memory/cost

# { customer_id: [ {"role": "user"|"assistant", "content": str}, ... ] }
_sessions: dict[str, list[dict]] = {}


def get_history(customer_id: str) -> list[dict]:
    """Return the conversation history for a customer (empty list if new)."""
    return _sessions.get(customer_id, [])


def append_turn(customer_id: str, role: str, content: str) -> None:
    """Add one message to a customer's history, trimming to MAX_TURNS pairs."""
    history = _sessions.setdefault(customer_id, [])
    history.append({"role": role, "content": content})

    # Keep only the most recent MAX_TURNS * 2 messages (user + assistant pairs)
    if len(history) > MAX_TURNS * 2:
        _sessions[customer_id] = history[-MAX_TURNS * 2 :]


def clear_history(customer_id: str) -> None:
    """Clear a customer's history - e.g. on logout."""
    _sessions.pop(customer_id, None)