
from typing import Any

from backend.coordinator import coordinate_response
from backend.validator import validate_plan


def run_baseline(scenario: dict[str, Any]) -> dict[str, Any]:
    """Simple first-fit allocator used as a comparison baseline."""

    assignments = []
    used_vehicles = set()
    blocked_routes = set(scenario.get("blocked_routes", []))

    vehicles = {
        vehicle["id"]: vehicle
        for vehicle in scenario.get("vehicles", [])
    }

    for task in scenario.get("tasks", []):
        route_id = task.get("route_id")

        if route_id and route_id in blocked_routes:
            continue

        vehicle = next(
            (
                item
                for item in scenario.get("vehicles", [])
                if item.get("available", False)
                and item["id"] not in used_vehicles
            ),
            None,
        )

        if vehicle is None:
            continue

        assignments.append({
            "task_id": task["id"],
            "vehicle_id": vehicle["id"],
            "agent": "Baseline Allocator",
        })
        used_vehicles.add(vehicle["id"])

    validation = validate_plan(scenario, assignments)

    return {
        "assignments": assignments,
        "conflicts": [],
        "validation": validation,
    }


def calculate_metrics(result: dict[str, Any]) -> dict[str, int]:
    """Calculate comparable allocation metrics."""

    assignments = result["assignments"]
    validation = result["validation"]

    return {
        "assigned_tasks": len({
            item["task_id"] for item in assignments
        }),
        "unassigned_tasks": len(validation["warnings"]),
        "conflicts": len(result.get("conflicts", [])),
        "constraint_violations": len(validation["errors"]),
    }


def compare_planners(
    scenario: dict[str, Any],
) -> dict[str, Any]:
    """Compare the baseline and coordinated planner fairly."""

    baseline = run_baseline(scenario)
    coordinated = coordinate_response(scenario)

    return {
        "baseline": {
            "result": baseline,
            "metrics": calculate_metrics(baseline),
        },
        "multi_agent": {
            "result": coordinated,
            "metrics": calculate_metrics(coordinated),
        },
    }
