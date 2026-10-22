
from copy import deepcopy
from typing import Any

from backend.coordinator import coordinate_response


def simulate_disruption(
    scenario: dict[str, Any],
    route_id: str,
) -> dict[str, Any]:
    """Simulate a blocked route and replan the response."""

    updated_scenario = deepcopy(scenario)
    blocked_routes = updated_scenario.setdefault("blocked_routes", [])

    if route_id not in {
        task.get("route_id")
        for task in updated_scenario.get("tasks", [])
    }:
        raise ValueError(f"Unknown route: {route_id}")

    if route_id not in blocked_routes:
        blocked_routes.append(route_id)

    original_result = coordinate_response(scenario)
    revised_result = coordinate_response(updated_scenario)

    original_assignments = {
        assignment["task_id"]: assignment["vehicle_id"]
        for assignment in original_result["assignments"]
    }

    revised_assignments = {
        assignment["task_id"]: assignment["vehicle_id"]
        for assignment in revised_result["assignments"]
    }

    revisions = []

    for task in updated_scenario.get("tasks", []):
        task_id = task["id"]
        old_vehicle = original_assignments.get(task_id)
        new_vehicle = revised_assignments.get(task_id)

        if old_vehicle != new_vehicle:
            revisions.append({
                "task_id": task_id,
                "previous_vehicle": old_vehicle,
                "new_vehicle": new_vehicle,
                "reason": (
                    f"Route {route_id} was blocked."
                    if task.get("route_id") == route_id
                    else "Assignment changed during replanning."
                ),
            })

    return {
        "disruption": {
            "type": "route_blocked",
            "route_id": route_id,
        },
        "original_plan": original_result,
        "revised_plan": revised_result,
        "revisions": revisions,
        "scenario": updated_scenario,
    }
