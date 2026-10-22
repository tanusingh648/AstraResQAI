
from backend.agents import (
    RescueAgent,
    MedicalAgent,
    TransportAgent,
    SupplyAgent,
)
from backend.validator import validate_plan
from backend.priority import rank_tasks, priority_reason, get_priority


def _get_agents():
    """Create the response-planning agents."""
    return [
        RescueAgent(),
        MedicalAgent(),
        TransportAgent(),
        SupplyAgent(),
    ]


def _get_field(item, field, default=None):
    """Read a field from either a dictionary or an object."""
    if isinstance(item, dict):
        return item.get(field, default)
    return getattr(item, field, default)


def _get_id(item):
    """Return an item's ID."""
    return _get_field(item, "id")


def coordinate_response(scenario):
    """
    Coordinate response assignments for a disaster scenario.

    Returns:
        assignments: accepted task-to-vehicle assignments
        conflicts: detected conflicts and reassignments
        decision_log: record of coordinator decisions
        validation: final plan validation result
        agent_count: number of agents used
        proposal_count: number of valid proposals collected
    """

    tasks = scenario.get("tasks", [])
    vehicles = scenario.get("vehicles", [])
    blocked_routes = set(scenario.get("blocked_routes", []) or [])

    tasks_by_id = {
        _get_id(task): task
        for task in tasks
        if _get_id(task) is not None
    }

    vehicles_by_id = {
        _get_id(vehicle): vehicle
        for vehicle in vehicles
        if _get_id(vehicle) is not None
    }

    conflicts = []
    decision_log = []
    final_assignments = []

    assigned_task_ids = set()
    allocated_vehicle_ids = set()

    # ---------------------------------------------------------
    # 1. Collect proposals from all response agents
    # ---------------------------------------------------------
    agents = _get_agents()
    proposals = []

    for agent in agents:
        try:
            agent_proposals = agent.propose_assignments(scenario) or []

            if isinstance(agent_proposals, dict):
                agent_proposals = [agent_proposals]

            for proposal in agent_proposals:
                if not isinstance(proposal, dict):
                    conflicts.append({
                        "type": "invalid_proposal",
                        "message": (
                            f"{type(agent).__name__} returned "
                            "a non-dictionary proposal."
                        ),
                    })
                    continue

                proposal = dict(proposal)
                proposal.setdefault(
                    "agent",
                    type(agent).__name__,
                )
                proposals.append(proposal)

        except Exception as exc:
            conflicts.append({
                "type": "agent_error",
                "agent": type(agent).__name__,
                "message": str(exc),
            })

            decision_log.append({
                "event": "agent_failed",
                "agent": type(agent).__name__,
                "reason": str(exc),
            })

    # ---------------------------------------------------------
    # 2. Rank tasks by priority
    # ---------------------------------------------------------
    ranked_tasks = rank_tasks(tasks) or []
    task_rank = {}

    for index, ranked_task in enumerate(ranked_tasks):
        if isinstance(ranked_task, (str, int)):
            task_id = ranked_task
        else:
            task_id = _get_id(ranked_task)

        if task_id is not None:
            task_rank[task_id] = index

    # Higher-ranked tasks are processed first.
    proposals.sort(
        key=lambda proposal: task_rank.get(
            proposal.get("task_id"),
            len(task_rank),
        )
    )

    # ---------------------------------------------------------
    # 3. Process proposals and resolve task conflicts
    # ---------------------------------------------------------
    for proposal in proposals:
        task_id = proposal.get("task_id")
        proposed_vehicle_id = proposal.get("vehicle_id")
        agent_name = proposal.get("agent", "Unknown agent")

        # Reject a proposal for a task that does not exist.
        if task_id not in tasks_by_id:
            conflicts.append({
                "type": "unknown_task",
                "task_id": task_id,
                "agent": agent_name,
                "message": f"Unknown task: {task_id}",
            })

            decision_log.append({
                "event": "proposal_rejected",
                "task_id": task_id,
                "agent": agent_name,
                "reason": "Task does not exist in the scenario.",
            })
            continue

        task = tasks_by_id[task_id]

        # A task must not receive more than one assignment.
        if task_id in assigned_task_ids:
            conflicts.append({
                "type": "duplicate_task",
                "task_id": task_id,
                "agent": agent_name,
                "message": f"Task {task_id} is already assigned.",
            })

            decision_log.append({
                "event": "proposal_rejected",
                "task_id": task_id,
                "agent": agent_name,
                "reason": "Task already has an assignment.",
            })
            continue

        # Reject tasks that use blocked routes.
        route_id = _get_field(task, "route_id")

        if route_id in blocked_routes:
            conflicts.append({
                "type": "blocked_route",
                "task_id": task_id,
                "route_id": route_id,
                "agent": agent_name,
                "message": (
                    f"Task {task_id} uses blocked route {route_id}."
                ),
            })

            decision_log.append({
                "event": "task_rejected",
                "task_id": task_id,
                "route_id": route_id,
                "reason": "The task route is blocked.",
            })
            continue

        # -----------------------------------------------------
        # 4. Select an available vehicle
        # -----------------------------------------------------
        selected_vehicle = None

        # First, try the vehicle requested by the agent.
        if proposed_vehicle_id is not None:
            proposed_vehicle = vehicles_by_id.get(
                proposed_vehicle_id
            )

            if (
                proposed_vehicle is not None
                and _get_field(
                    proposed_vehicle, "available", False
                )
                and proposed_vehicle_id not in allocated_vehicle_ids
            ):
                selected_vehicle = proposed_vehicle

        # If the requested vehicle is unavailable or already used,
        # find another available vehicle.
        if selected_vehicle is None:
            available_vehicles = [
                vehicle
                for vehicle in vehicles
                if _get_field(vehicle, "available", False)
                and _get_id(vehicle) is not None
                and _get_id(vehicle) not in allocated_vehicle_ids
            ]

            if available_vehicles:
                selected_vehicle = available_vehicles[0]

                # Record a genuine reassignment when a specific
                # vehicle was requested but another one was selected.
                if proposed_vehicle_id is not None:
                    reassignment = {
                        "type": "vehicle_reassigned",
                        "event": "vehicle_reassigned",
                        "task_id": task_id,
                        "requested_vehicle": proposed_vehicle_id,
                        "selected_vehicle": _get_id(
                            selected_vehicle
                        ),
                        "reassigned": True,
                        "reason": (
                            "The requested vehicle was unavailable "
                            "or had already been allocated."
                        ),
                    }

                    conflicts.append(reassignment)
                    decision_log.append(reassignment.copy())

        # No vehicle is available for this task.
        if selected_vehicle is None:
            conflicts.append({
                "type": "no_available_vehicle",
                "task_id": task_id,
                "agent": agent_name,
                "message": (
                    f"No available vehicle for task {task_id}."
                ),
            })

            decision_log.append({
                "event": "task_unassigned",
                "task_id": task_id,
                "agent": agent_name,
                "reason": "No available vehicle.",
            })
            continue

        # -----------------------------------------------------
        # 5. Determine task priority
        # -----------------------------------------------------
        try:
            priority = get_priority(task)
        except Exception:
            priority = _get_field(task, "priority", "normal")

        try:
            reason = priority_reason(task)
        except Exception:
            reason = "Priority determined from scenario data."

        # -----------------------------------------------------
        # 6. Create and record the assignment
        # -----------------------------------------------------
        vehicle_id = _get_id(selected_vehicle)

        assignment = {
            "task_id": task_id,
            "vehicle_id": vehicle_id,
            "agent": agent_name,
            "route_id": route_id,
            "priority": priority,
            "priority_reason": reason,
        }

        final_assignments.append(assignment)
        assigned_task_ids.add(task_id)
        allocated_vehicle_ids.add(vehicle_id)

        decision_log.append({
            "event": "task_assigned",
            "task_id": task_id,
            "vehicle_id": vehicle_id,
            "agent": agent_name,
            "priority": priority,
            "reason": reason,
        })

    # ---------------------------------------------------------
    # 7. Record tasks that remain unassigned
    # ---------------------------------------------------------
    for task in tasks:
        task_id = _get_id(task)

        if (
            task_id is not None
            and task_id not in assigned_task_ids
            and not any(
                entry.get("event") == "task_unassigned"
                and entry.get("task_id") == task_id
                for entry in decision_log
            )
        ):
            decision_log.append({
                "event": "task_unassigned",
                "task_id": task_id,
                "reason": (
                    "No valid assignment was produced for this task."
                ),
            })

    # ---------------------------------------------------------
    # 8. Validate the final assignment plan
    # ---------------------------------------------------------
    validation = validate_plan(
        scenario,
        final_assignments,
    )

    # ---------------------------------------------------------
    # 9. Return results for the dashboard and ConflictLab
    # ---------------------------------------------------------
    return {
        "assignments": final_assignments,
        "conflicts": conflicts,
        "decision_log": decision_log,
        "validation": validation,
        "agent_count": len(agents),
        "proposal_count": len(proposals),
    }
