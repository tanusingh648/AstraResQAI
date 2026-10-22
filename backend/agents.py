
from typing import Any


class BaseAgent:
    """Base class for a simulated disaster-response agent."""

    def __init__(self, name: str, task_type: str):
        self.name = name
        self.task_type = task_type

    def propose_assignments(
        self,
        scenario: dict[str, Any],
    ) -> list[dict[str, str]]:
        """Propose assignments for tasks handled by this agent."""

        proposals = []

        vehicles = [
            vehicle
            for vehicle in scenario.get("vehicles", [])
            if vehicle.get("available", False)
        ]

        tasks = [
            task
            for task in scenario.get("tasks", [])
            if task.get("agent", "").lower() == self.task_type
        ]

        for task in tasks:
            if task.get("route_id") in scenario.get(
                "blocked_routes", []
            ):
                continue

            used_vehicle_ids = {
                proposal["vehicle_id"]
                for proposal in proposals
            }

            vehicle = next(
                (
                    item
                    for item in vehicles
                    if item["id"] not in used_vehicle_ids
                ),
                None,
            )

            if vehicle is None:
                break

            proposals.append(
                {
                    "task_id": task["id"],
                    "vehicle_id": vehicle["id"],
                    "agent": self.name,
                }
            )

        return proposals


class RescueAgent(BaseAgent):
    def __init__(self):
        super().__init__("Rescue Agent", "rescue")


class MedicalAgent(BaseAgent):
    def __init__(self):
        super().__init__("Medical Agent", "medical")


class TransportAgent(BaseAgent):
    def __init__(self):
        super().__init__("Transport Agent", "transport")


class SupplyAgent(BaseAgent):
    def __init__(self):
        super().__init__("Supply Agent", "supply")


def create_agents() -> list[BaseAgent]:
    """Create the four specialized simulation agents."""

    return [
        RescueAgent(),
        MedicalAgent(),
        TransportAgent(),
        SupplyAgent(),
    ]
