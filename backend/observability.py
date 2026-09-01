"""
Lightweight observability layer.

Tracks latency and call counts per agent/tool, in memory.
"""

import time
from contextlib import contextmanager

_agent_stats: dict[str, dict] = {}
_tool_stats: dict[str, dict] = {}


def _record(store: dict, name: str, latency_ms: float, errored: bool) -> None:
    entry = store.setdefault(name, {"calls": 0, "total_latency_ms": 0.0, "errors": 0})
    entry["calls"] += 1
    entry["total_latency_ms"] += latency_ms
    if errored:
        entry["errors"] += 1


@contextmanager
def track_agent_call(agent_name: str):
    start = time.perf_counter()
    errored = False
    try:
        yield
    except Exception:
        errored = True
        raise
    finally:
        latency_ms = (time.perf_counter() - start) * 1000
        _record(_agent_stats, agent_name, latency_ms, errored)


@contextmanager
def track_tool_call(tool_name: str):
    start = time.perf_counter()
    errored = False
    try:
        yield
    except Exception:
        errored = True
        raise
    finally:
        latency_ms = (time.perf_counter() - start) * 1000
        _record(_tool_stats, tool_name, latency_ms, errored)


def get_metrics() -> dict:
    def _summarize(store: dict) -> dict:
        summary = {}
        for name, stats in store.items():
            avg_ms = stats["total_latency_ms"] / stats["calls"] if stats["calls"] else 0
            summary[name] = {
                "calls": stats["calls"],
                "errors": stats["errors"],
                "avg_latency_ms": round(avg_ms, 2),
            }
        return summary

    return {
        "agents": _summarize(_agent_stats),
        "tools": _summarize(_tool_stats),
    }