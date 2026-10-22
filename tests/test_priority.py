
from backend.priority import rank_tasks, get_priority, priority_reason


def test_critical_task_ranks_before_low_priority_task():
    tasks = [
        {"id": "T1", "priority": "low"},
        {"id": "T2", "priority": "critical"},
        {"id": "T3", "priority": "high"},
    ]

    ranked = rank_tasks(tasks)

    assert [task["id"] for task in ranked] == ["T2", "T3", "T1"]


def test_equal_priorities_preserve_original_order():
    tasks = [
        {"id": "T1", "priority": "high"},
        {"id": "T2", "priority": "high"},
    ]

    assert [task["id"] for task in rank_tasks(tasks)] == ["T1", "T2"]


def test_missing_priority_defaults_to_medium():
    task = {"id": "T1"}

    assert get_priority(task) == "medium"


def test_invalid_priority_defaults_to_medium():
    task = {"id": "T1", "priority": "urgent-now"}

    assert get_priority(task) == "medium"


def test_priority_reason_explains_configured_priority():
    task = {"id": "T1", "priority": "critical"}

    assert "critical" in priority_reason(task).lower()
