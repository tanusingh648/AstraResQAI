
from backend.agents import create_agents


def test_four_agents_are_created():
    agents = create_agents()

    assert len(agents) == 4
    assert {agent.name for agent in agents} == {
        "Rescue Agent",
        "Medical Agent",
        "Transport Agent",
        "Supply Agent",
    }


def test_agents_propose_matching_tasks():
    agents = create_agents()

    scenario = {
        "blocked_routes": [],
        "vehicles": [
            {"id": "V1", "available": True},
            {"id": "V2", "available": True},
        ],
        "tasks": [
            {
                "id": "T1",
                "agent": "rescue",
                "route_id": "R1",
            },
            {
                "id": "T2",
                "agent": "medical",
                "route_id": "R2",
            },
        ],
    }

    proposals = [
        proposal
        for agent in agents
        for proposal in agent.propose_assignments(scenario)
    ]

    assert {p["task_id"] for p in proposals} == {"T1", "T2"}
    assert all(p["vehicle_id"] in {"V1", "V2"} for p in proposals)


def test_agents_skip_blocked_routes():
    agents = create_agents()

    scenario = {
        "blocked_routes": ["R1"],
        "vehicles": [
            {"id": "V1", "available": True},
        ],
        "tasks": [
            {
                "id": "T1",
                "agent": "rescue",
                "route_id": "R1",
            },
        ],
    }

    proposals = [
        proposal
        for agent in agents
        for proposal in agent.propose_assignments(scenario)
    ]

    assert proposals == []
