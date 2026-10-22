
import pytest

from backend.simulator import simulate_disruption


@pytest.fixture
def scenario():
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


def test_disruption_blocks_route_in_revised_scenario(scenario):
    result = simulate_disruption(scenario, "R1")

    assert "R1" in result["scenario"]["blocked_routes"]
    assert result["disruption"]["route_id"] == "R1"


def test_original_scenario_is_not_modified(scenario):
    simulate_disruption(scenario, "R1")

    assert scenario["blocked_routes"] == []


def test_blocked_route_task_is_not_assigned(scenario):
    result = simulate_disruption(scenario, "R1")

    revised_assignments = result["revised_plan"]["assignments"]

    assert all(
        assignment["task_id"] != "T1"
        for assignment in revised_assignments
    )


def test_unknown_route_raises_error(scenario):
    with pytest.raises(ValueError, match="Unknown route"):
        simulate_disruption(scenario, "R99")
