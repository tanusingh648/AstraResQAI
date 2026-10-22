
"""Coordinate multi-agent task proposals for disaster simulations."""

from backend.agents import (
    RescueAgent,
    MedicalAgent,
    TransportAgent,
    SupplyAgent,
)
from backend.validator import validate_plan
from backend.priority import (
    rank_tasks,
    priority_reason,
    get_priority,
)


def coordinate_response(scenario):
    """
    Coordinate response agents and create an assignment plan.

    Higher-priority tasks are processed first. The coordinator also
    handles duplicate proposals, unavailable vehicles, blocked routes,
    vehicle conflicts, and final plan validation.

    Args:
        scenario (dict): A fictional disaster simulation scenario.

    Returns:
        dict: Assignments, conflicts, decision log, validation,
              agent count, and proposal count.
    """

    # 1. Initialize all four specialized agents.
    agents = [
        RescueAgent(),
        MedicalAgent(),
        TransportAgent(),
        SupplyAgent(),
    ]

    # 2. Collect task proposals from every agent.
    proposals = []

    for agent in agents:
        agent_proposals = agent.propose_assignments(scenario)
        proposals.extend(agent_proposals)

    proposal_count = len(proposals)

    # 3. Initialize coordination state.
    final_assignments = []
    used_vehicles = set()
    assigned_tasks = set()
    conflicts = []
    decision_log = []

    tasks = scenario.get("tasks", [])
    vehicles = scenario.get("vehicles", [])

    tasks_by_id = {
        task["id"]: task
        for task in tasks
        if "id" in task
    }

    vehicles_by_id = {
        vehicle["id"]: vehicle
        for vehicle in vehicles
        if "id" in vehicle
    }

    blocked_routes = set(
        scenario.get("blocked_routes", [])
    )

    # 4. Rank tasks and create a stable priority order.
    # Critical > High > Medium > Low.
    # Equal priorities retain their original task order.
    ranked_tasks = rank_tasks(tasks)

    task_rank = {
        task["id"]: index
        for index, task in enumerate(ranked_tasks, start=1)
        if "id" in task
    }

    # Sort ONCE before processing proposals.
    # Unknown task proposals are placed at the end.
    proposals.sort(
        key=lambda proposal: task_rank.get(
            proposal.get("task_id"),
            len(task_rank) + 1,
        )
    )

    # 5. Process proposals in priority order.
    for proposal in proposals:
        task_id = proposal.get("task_id")
        proposed_vehicle_id = proposal.get("vehicle_id")

        # Reject proposals for tasks that do not exist.
        if task_id not in tasks_by_id:
            message = f"Unknown task '{task_id}'."
            conflicts.append(message)

            decision_log.append({
                "event": "proposal_rejected",
                "task_id": task_id,
                "proposed_vehicle": proposed_vehicle_id,
                "reason": "Task does not exist in the scenario.",
            })
            continue

        task = tasks_by_id[task_id]

        # Prevent multiple assignments for the same task.
        if task_id in assigned_tasks:
            message = (
                f"Duplicate proposal ignored for task {task_id}."
            )
            conflicts.append(message)

            decision_log.append({
                "event": "proposal_rejected",
                "task_id": task_id,
                "proposed_vehicle": proposed_vehicle_id,
                "priority": get_priority(task),
                "priority_rank": task_rank.get(task_id),
                "priority_reason": priority_reason(task),
                "reason": "Task has already been assigned.",
            })
            continue

        # Do not assign tasks whose routes are blocked.
        route_id = task.get("route_id")

        if route_id in blocked_routes:
            message = (
                f"Task {task_id} skipped because "
                f"route {route_id} is blocked."
            )
            conflicts.append(message)

            decision_log.append({
                "event": "proposal_rejected",
                "task_id": task_id,
                "proposed_vehicle": proposed_vehicle_id,
                "priority": get_priority(task),
                "priority_rank": task_rank.get(task_id),
                "priority_reason": priority_reason(task),
                "reason": f"Route {route_id} is blocked.",
            })
            continue

        # 6. Find available vehicles that have not been allocated.
        available_vehicles = [
            vehicle["id"]
            for vehicle in vehicles
            if vehicle.get("available", False)
            and vehicle["id"] not in used_vehicles
            and "id" in vehicle
        ]

        # Prefer the agent's proposed vehicle if it is usable.
        if (
            proposed_vehicle_id in available_vehicles
            and proposed_vehicle_id in vehicles_by_id
        ):
            selected_vehicle = proposed_vehicle_id
        else:
            # Otherwise, choose the first available vehicle.
            selected_vehicle = (
                available_vehicles[0]
                if available_vehicles
                else None
            )

        # 7. Handle cases where no vehicle remains available.
        if selected_vehicle is None:
            message = f"No available vehicle for task {task_id}."
            conflicts.append(message)

            decision_log.append({
                "event": "assignment_rejected",
                "task_id": task_id,
                "proposed_vehicle": proposed_vehicle_id,
                "assigned_vehicle": None,
                "priority": get_priority(task),
                "priority_rank": task_rank.get(task_id),
                "priority_reason": priority_reason(task),
                "reason": (
                    "No available, unallocated vehicle remains."
                ),
            })
            continue

        # 8. Record vehicle conflicts and reassignment.
        if selected_vehicle != proposed_vehicle_id:
            message = (
                f"Vehicle conflict for task {task_id}: "
                f"reassigned from {proposed_vehicle_id} "
                f"to {selected_vehicle}."
            )
            conflicts.append(message)

            decision_log.append({
                "event": "reassignment",
                "task_id": task_id,
                "proposed_vehicle": proposed_vehicle_id,
                "assigned_vehicle": selected_vehicle,
                "priority": get_priority(task),
                "priority_rank": task_rank.get(task_id),
                "priority_reason": priority_reason(task),
                "reason": (
                    "Proposed vehicle was unavailable, unknown, "
                    "or already allocated."
                ),
            })

        # 9. Accept the assignment.
        assignment = {
            "task_id": task_id,
            "vehicle_id": selected_vehicle,
            "agent": proposal.get(
                "agent",
                task.get("agent", "Unknown Agent"),
            ),
        }

        final_assignments.append(assignment)
        used_vehicles.add(selected_vehicle)
        assigned_tasks.add(task_id)

        decision_log.append({
            "event": "assignment_accepted",
            "task_id": task_id,
            "assigned_vehicle": selected_vehicle,
            "agent": assignment["agent"],
            "priority": get_priority(task),
            "priority_rank": task_rank.get(task_id),
            "priority_reason": priority_reason(task),
            "reason": (
                "Vehicle is available and has not been "
                "allocated to another task."
            ),
        })

    # 10. Record tasks that received no assignment.
    for task in ranked_tasks:
        task_id = task.get("id")

        if task_id is None or task_id in assigned_tasks:
            continue

        route_id = task.get("route_id")

        if route_id in blocked_routes:
            reason = (
                f"Task was not assigned because route "
                f"{route_id} is blocked."
            )
        else:
            reason = (
                "Task received no assignment during coordination."
            )

        decision_log.append({
            "event": "task_unassigned",
            "task_id": task_id,
            "priority": get_priority(task),
            "priority_rank": task_rank.get(task_id),
            "priority_reason": priority_reason(task),
            "reason": reason,
        })

    # 11. Validate the final assignment plan.
    validation = validate_plan(
        scenario,
        final_assignments,
    )

    decision_log.append({
        "event": "plan_validated",
        "valid": validation.get("valid", False),
        "reason": (
            "Final assignments were checked against "
            "scenario constraints."
        ),
    })

    # 12. Return the existing interface expected by the dashboard.
    return {
        "assignments": final_assignments,
        "conflicts": conflicts,
        "decision_log": decision_log,
        "validation": validation,
        "agent_count": len(agents),
        "proposal_count": proposal_count,
    }
