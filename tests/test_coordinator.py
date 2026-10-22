
from backend.coordinator import coordinate_response


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


def test_coordinator_returns_valid_plan():
    result = coordinate_response(sample_scenario())

    assert result["validation"]["valid"] is True
    assert len(result["assignments"]) == 2

    # Both tasks must use different vehicles.
    vehicle_ids = [
        assignment["vehicle_id"]
        for assignment in result["assignments"]
    ]
    assert len(set(vehicle_ids)) == 2

    # A reassignment is recorded for ConflictLab.
    assert len(result["conflicts"]) == 1
    assert "reassigned" in result["conflicts"][0]



def test_coordinator_rejects_vehicle_conflicts():
    scenario = sample_scenario()

    # Only one available vehicle for two agents.
    scenario["vehicles"] = [
        {"id": "V1", "available": True},
    ]

    result = coordinate_response(scenario)

    assert len(result["assignments"]) == 1
    assert len(result["conflicts"]) == 1
    assert result["validation"]["valid"] is True


def test_coordinator_reports_unassigned_tasks():
    scenario = sample_scenario()
    scenario["vehicles"] = []

    result = coordinate_response(scenario)

    assert result["assignments"] == []
    assert result["validation"]["valid"] is True
    assert len(result["validation"]["warnings"]) == 2
