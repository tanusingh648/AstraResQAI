
import json
from pathlib import Path

from backend.validator import validate_plan


ROOT = Path(__file__).resolve().parents[1]


def load_scenario():
    with (ROOT / "data" / "scenarios.json").open(
        encoding="utf-8"
    ) as file:
        return json.load(file)


def test_valid_assignments_pass():
    scenario = load_scenario()
    assignments = [
        {"task_id": "T1", "vehicle_id": "V1"},
        {"task_id": "T2", "vehicle_id": "V2"},
    ]

    result = validate_plan(scenario, assignments)

    assert result["valid"] is True
    assert result["errors"] == []


def test_duplicate_vehicle_assignment_fails():
    scenario = load_scenario()
    assignments = [
        {"task_id": "T1", "vehicle_id": "V1"},
        {"task_id": "T2", "vehicle_id": "V1"},
    ]

    result = validate_plan(scenario, assignments)

    assert result["valid"] is False
    assert any(
        "assigned to both" in error
        for error in result["errors"]
    )


def test_unavailable_vehicle_fails():
    scenario = load_scenario()
    assignments = [
        {"task_id": "T6", "vehicle_id": "V4"},
    ]

    result = validate_plan(scenario, assignments)

    assert result["valid"] is False
    assert any(
        "unavailable" in error
        for error in result["errors"]
    )


def test_blocked_route_fails():
    scenario = load_scenario()
    scenario["blocked_routes"] = ["R1"]

    assignments = [
        {"task_id": "T1", "vehicle_id": "V1"},
    ]

    result = validate_plan(scenario, assignments)

    assert result["valid"] is False
    assert any(
        "blocked route" in error
        for error in result["errors"]
    )


def test_unknown_task_fails():
    scenario = load_scenario()
    assignments = [
        {"task_id": "UNKNOWN", "vehicle_id": "V1"},
    ]

    result = validate_plan(scenario, assignments)

    assert result["valid"] is False
    assert any(
        "Unknown task" in error
        for error in result["errors"]
    )
