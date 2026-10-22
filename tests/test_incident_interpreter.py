
import json

import pytest

from backend.incident_interpreter import (
    IncidentInterpreterError,
    interpret_incident,
)


class FakeResponse:
    def __init__(self, payload):
        self.text = json.dumps(payload)
        self.parsed = None


class FakeModels:
    def __init__(self, payload):
        self.payload = payload
        self.last_request = None

    def generate_content(self, **kwargs):
        self.last_request = kwargs
        return FakeResponse(self.payload)


class FakeClient:
    def __init__(self, payload):
        self.models = FakeModels(payload)


@pytest.fixture
def scenario_template():
    return {
        "name": "Original scenario",
        "description": "Test template",
        "blocked_routes": [],
        "vehicles": [
            {"id": "V1", "available": True},
            {"id": "V2", "available": True},
        ],
        "tasks": [],
    }


@pytest.fixture
def valid_payload():
    return {
        "scenario_name": "Fictional River Flood",
        "summary": "A fictional flood simulation with rescue and medical tasks.",
        "tasks": [
            {
                "name": "Rescue at North Zone",
                "agent": "rescue",
                "priority": "critical",
                "route_label": "North Zone",
                "rationale": "The description requests a simulated rescue.",
            },
            {
                "name": "Medical Support at East Zone",
                "agent": "medical",
                "priority": "high",
                "route_label": "East Zone",
                "rationale": "The description requests medical support.",
            },
        ],
        "assumptions": ["All locations are fictional."],
        "clarification_questions": ["Should another zone be included?"],
    }


def test_interpreter_builds_compatible_scenario(
    scenario_template, valid_payload
):
    client = FakeClient(valid_payload)

    result = interpret_incident(
        "Simulate a flood with rescue needs in the north and medical needs east.",
        scenario_template,
        client=client,
    )

    assert result["name"] == "Fictional River Flood"
    assert len(result["tasks"]) == 2
    assert result["tasks"][0]["id"] == "T1"
    assert result["tasks"][0]["route_id"] == "R1"
    assert result["tasks"][0]["agent"] == "rescue"
    assert result["tasks"][1]["agent"] == "medical"
    assert result["vehicles"] == scenario_template["vehicles"]
    assert result["blocked_routes"] == []


def test_interpreter_preserves_original_template(
    scenario_template, valid_payload
):
    original = json.loads(json.dumps(scenario_template))

    interpret_incident(
        "Create a fictional flood simulation with rescue tasks.",
        scenario_template,
        client=FakeClient(valid_payload),
    )

    assert scenario_template == original


def test_interpreter_rejects_short_description(scenario_template):
    with pytest.raises(IncidentInterpreterError):
        interpret_incident(
            "Flood",
            scenario_template,
            client=FakeClient({}),
        )


def test_interpreter_rejects_invalid_agent(
    scenario_template, valid_payload
):
    invalid_payload = json.loads(json.dumps(valid_payload))
    invalid_payload["tasks"][0]["agent"] = "firefighter"

    with pytest.raises(IncidentInterpreterError):
        interpret_incident(
            "Create a fictional response simulation with rescue tasks.",
            scenario_template,
            client=FakeClient(invalid_payload),
        )


def test_interpreter_rejects_empty_task_list(
    scenario_template, valid_payload
):
    empty_payload = json.loads(json.dumps(valid_payload))
    empty_payload["tasks"] = []

    with pytest.raises(IncidentInterpreterError):
        interpret_incident(
            "Create a fictional response simulation.",
            scenario_template,
            client=FakeClient(empty_payload),
        )


def test_interpreter_rejects_too_many_tasks(
    scenario_template, valid_payload
):
    large_payload = json.loads(json.dumps(valid_payload))
    large_payload["tasks"] = (
        large_payload["tasks"] * 16
    )

    with pytest.raises(IncidentInterpreterError):
        interpret_incident(
            "Create a fictional response simulation with many tasks.",
            scenario_template,
            client=FakeClient(large_payload),
        )
