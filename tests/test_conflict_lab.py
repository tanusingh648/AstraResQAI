
from backend.conflict_lab import (
    calculate_metrics,
    compare_planners,
    run_baseline,
)


def sample_scenario():
    return {
        "blocked_routes": [],
        "vehicles": [
            {"id": "V1", "available": True},
            {"id": "V2", "available": True},
        ],
        "tasks": [
            {"id": "T1", "agent": "rescue", "route_id": "R1"},
            {"id": "T2", "agent": "medical", "route_id": "R2"},
        ],
    }


def test_baseline_assigns_tasks_when_resources_are_available():
    result = run_baseline(sample_scenario())

    assert len(result["assignments"]) == 2
    assert result["validation"]["valid"] is True


def test_baseline_skips_blocked_routes():
    scenario = sample_scenario()
    scenario["blocked_routes"] = ["R1"]

    result = run_baseline(scenario)

    assigned_task_ids = {
        item["task_id"] for item in result["assignments"]
    }
    assert "T1" not in assigned_task_ids


def test_metrics_count_unassigned_tasks():
    result = {
        "assignments": [
            {"task_id": "T1", "vehicle_id": "V1"}
        ],
        "conflicts": ["Example conflict"],
        "validation": {
            "errors": [],
            "warnings": ["T2 is not assigned."],
        },
    }

    metrics = calculate_metrics(result)

    assert metrics["assigned_tasks"] == 1
    assert metrics["unassigned_tasks"] == 1
    assert metrics["conflicts"] == 1
    assert metrics["constraint_violations"] == 0


def test_comparison_contains_both_planners():
    comparison = compare_planners(sample_scenario())

    assert "baseline" in comparison
    assert "multi_agent" in comparison
    assert comparison["baseline"]["metrics"]["assigned_tasks"] == 2
    assert comparison["multi_agent"]["metrics"]["assigned_tasks"] == 2
