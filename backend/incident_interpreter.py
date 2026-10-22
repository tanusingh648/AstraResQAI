
import os
from typing import List, Literal

import dotenv
from google import genai
from pydantic import BaseModel, Field, ValidationError


dotenv.load_dotenv()


AgentType = Literal["rescue", "medical", "transport", "supply"]
Priority = Literal["low", "medium", "high", "critical"]


class IncidentTask(BaseModel):
    name: str = Field(description="Short name for a simulated response task")
    agent: AgentType = Field(
        description="Specialized agent responsible for proposing this task"
    )
    priority: Priority = Field(
        description="Priority explicitly supported by the incident description"
    )
    route_label: str = Field(
        description="Short fictional route or zone label, such as North Zone"
    )
    rationale: str = Field(
        description="Brief explanation of why this task is included"
    )


class IncidentDraft(BaseModel):
    scenario_name: str = Field(description="Name of the fictional scenario")
    summary: str = Field(description="Short summary of the described incident")
    tasks: List[IncidentTask] = Field(
        description="Tasks for the fictional response simulation"
    )
    assumptions: List[str] = Field(
        description="Assumptions made because details were not supplied"
    )
    clarification_questions: List[str] = Field(
        description="Questions about important missing or ambiguous details"
    )


class IncidentInterpreterError(Exception):
    """Raised when an incident description cannot be interpreted safely."""


SYSTEM_INSTRUCTIONS = """
You interpret incident descriptions for a fictional educational disaster
response simulation. This is not a real emergency service.

Convert the user's description into structured scenario data.
Only use the four agent types: rescue, medical, transport, supply.
Use short task names and fictional zone/route labels.
Do not invent real-world addresses, verified routes, casualty counts,
or claims that a real emergency has been assessed.
Do not present assumptions as confirmed facts.
If details are missing or ambiguous, record assumptions and ask
clarification questions. Never claim that a plan is safe for real use.
Return only data matching the supplied schema.
"""


def _validate_draft(draft: IncidentDraft) -> IncidentDraft:
    """Apply application-level checks after model/schema validation."""

    if not draft.tasks:
        raise IncidentInterpreterError(
            "Gemini returned no tasks. Please describe at least one "
            "simulated response need."
        )

    if len(draft.tasks) > 30:
        raise IncidentInterpreterError(
            "The generated scenario contains too many tasks (maximum 30). "
            "Please use a shorter or more focused description."
        )

    names = [task.name.strip().casefold() for task in draft.tasks]
    if any(not name for name in names):
        raise IncidentInterpreterError(
            "A generated task has an empty name. Please try again."
        )

    return draft


def interpret_incident(
    description: str,
    scenario_template: dict,
    client=None,
) -> dict:
    """
    Convert natural-language incident text into a scenario compatible
    with the existing AstraResQ AI coordinator.

    Pass client explicitly in tests to avoid network calls.
    """

    description = (description or "").strip()

    if len(description) < 10:
        raise IncidentInterpreterError(
            "Please enter a more detailed description (at least 10 characters)."
        )

    if len(description) > 4000:
        raise IncidentInterpreterError(
            "The description is too long. Keep it under 4,000 characters."
        )

    if not isinstance(scenario_template, dict):
        raise IncidentInterpreterError(
            "The scenario template must be a dictionary."
        )

    vehicles = scenario_template.get("vehicles", [])
    if not isinstance(vehicles, list):
        raise IncidentInterpreterError(
            "The scenario template has an invalid vehicle inventory."
        )

    if client is None:
        if not os.getenv("GEMINI_API_KEY"):
            raise IncidentInterpreterError(
                "Gemini API key not found. Add GEMINI_API_KEY to your "
                "project's .env file, then restart Streamlit."
            )

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    prompt = (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        "Interpret this fictional incident description:\n"
        f"{description}"
    )

    try:
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": IncidentDraft,
                "temperature": 0.2,
            },
        )

        # Prefer the SDK's parsed model when available. Otherwise validate
        # the returned JSON locally.
        parsed = getattr(response, "parsed", None)

        if isinstance(parsed, IncidentDraft):
            draft = parsed
        elif isinstance(parsed, dict):
            draft = IncidentDraft(**parsed)
        else:
            response_text = getattr(response, "text", None)
            if not response_text:
                raise IncidentInterpreterError(
                    "Gemini returned an empty response. Please try again."
                )

            # parse_raw works with both Pydantic v1 and v2.
            draft = IncidentDraft.parse_raw(response_text)

        draft = _validate_draft(draft)

    except IncidentInterpreterError:
        raise
    except ValidationError as error:
        raise IncidentInterpreterError(
            f"The generated scenario did not pass schema validation: {error}"
        ) from error
    except Exception as error:
        raise IncidentInterpreterError(
            "Gemini could not interpret this description. Check your API "
            "key, network connection, model availability, and API quota. "
            f"Technical detail: {error}"
        ) from error

    # Build a scenario using the format expected by the existing backend.
    # IDs and route IDs are generated locally rather than trusted from the LLM.
    tasks = []

    for index, task in enumerate(draft.tasks, start=1):
        route_id = f"R{index}"

        tasks.append({
            "id": f"T{index}",
            "name": task.name.strip(),
            "agent": task.agent,
            "route_id": route_id,
            "priority": task.priority,
            "rationale": task.rationale,
            "route_label": task.route_label.strip(),
        })

    return {
        "name": draft.scenario_name.strip(),
        "description": (
            "Fictional educational simulation generated from a "
            "natural-language incident description. "
            + draft.summary.strip()
        ),
        "blocked_routes": [],
        "vehicles": [dict(vehicle) for vehicle in vehicles],
        "tasks": tasks,
        "interpreter_metadata": {
            "assumptions": draft.assumptions,
            "clarification_questions": draft.clarification_questions,
            "source": "Gemini natural-language interpreter",
        },
    }
