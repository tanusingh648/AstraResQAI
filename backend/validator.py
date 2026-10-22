from typing import Any

def validate_plan(
        scenario : dict[str,Any],
        assignments : list[dict[str,Any]],

) -> dict[str,Any] :
    errors: list[str] = []
    warnings: list[str] = []

    tasks = {
        task["id"]: task
        for task in scenario.get("tasks", [])
    }

    vehicles = {
        vehicle["id"]: vehicle
        for vehicle in scenario.get("vehicles", [])
    }

    blocked_routes = set(scenario.get("blocked_routes", []))
    assigned_vehicles: dict[str, str] = {}
    assigned_tasks: set[str] = set()

    for assignment in assignments:
        task_id = assignment.get("task_id")
        vehicle_id = assignment.get("vehicle_id")

        if task_id not in tasks:
            errors.append(f"Unknown task: {task_id}")
            continue

        if vehicle_id not in vehicles:
            errors.append(f"Unknown vehicle: {vehicle_id}")
            continue

        if task_id in assigned_tasks:
            errors.append(
                f"Task {task_id} has been assigned more than once."
            )
        else:
            assigned_tasks.add(task_id)

        if vehicle_id in assigned_vehicles:
            previous_task = assigned_vehicles[vehicle_id]
            errors.append(
                f"Vehicle {vehicle_id} is assigned to both "
                f"{previous_task} and {task_id}."
            )
        else:
            assigned_vehicles[vehicle_id] = task_id

        vehicle = vehicles[vehicle_id]
        task = tasks[task_id]

        if not vehicle.get("available", False):
            errors.append(
                f"Vehicle {vehicle_id} is unavailable."
            )

        route_id = task.get("route_id")
        if route_id and route_id in blocked_routes:
            errors.append(
                f"Task {task_id} uses blocked route {route_id}."
            )

    for task_id in tasks:
        if task_id not in assigned_tasks:
            warnings.append(f"Task {task_id} is not assigned.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "assigned_task_count": len(assigned_tasks),
        "assigned_vehicle_count": len(assigned_vehicles),
    }
