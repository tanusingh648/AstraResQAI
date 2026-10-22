
"""Deterministic priority ranking for fictional disaster simulations."""

PRIORITY_SCORES = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
}


def get_priority(task: dict) -> str:
    """Return a normalized priority, defaulting to medium."""
    priority = str(task.get("priority", "medium")).strip().lower()
    return priority if priority in PRIORITY_SCORES else "medium"


def priority_score(task: dict) -> int:
    """Higher scores are processed first."""
    return PRIORITY_SCORES[get_priority(task)]


def priority_reason(task: dict) -> str:
    """Explain the configured priority without inventing incident facts."""
    priority = get_priority(task)

    reasons = {
        "critical": "Marked critical in the scenario; review first.",
        "high": "Marked high priority in the scenario.",
        "medium": "Marked medium priority in the scenario.",
        "low": "Marked low priority in the scenario.",
    }

    return reasons[priority]


def rank_tasks(tasks: list[dict]) -> list[dict]:
    """
    Return tasks in descending priority order.

    Python's stable sort preserves the original order for equal priorities.
    The original task dictionaries and list are not modified.
    """
    return sorted(tasks, key=priority_score, reverse=True)
