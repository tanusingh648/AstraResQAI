
import json
from copy import deepcopy
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from backend.coordinator import coordinate_response
from backend.simulator import simulate_disruption
from backend.conflict_lab import compare_planners
from backend.route_planner import (
    find_route,
    find_alternative_route,
    capture_camera_frame,
)


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
SCENARIO_PATH = BASE_DIR / "data" / "scenarios.json"

BG = "#07111F"
PANEL = "#0D1B2A"
PANEL_LIGHT = "#122438"
CYAN = "#35E7FF"
TEAL = "#37E6C1"
MUTED = "#91A7BC"
WHITE = "#EDF7FF"
RED = "#FF647C"
AMBER = "#FFC66D"

st.set_page_config(
    page_title="ASTRARESQ AI | Command Center",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# FUTURISTIC UI THEME
# =========================================================

st.markdown(
    f"""
    <style>
    @import url(
      'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Orbitron:wght@500;600;700;800&display=swap'
    );

    :root {{
        --bg: {BG};
        --panel: {PANEL};
        --cyan: {CYAN};
        --teal: {TEAL};
        --text: {WHITE};
        --muted: {MUTED};
    }}

    html, body, [data-testid="stAppViewContainer"] {{
        background:
            radial-gradient(
                ellipse at 15% 0%,
                rgba(20, 105, 145, 0.18),
                transparent 36%
            ),
            radial-gradient(
                ellipse at 100% 30%,
                rgba(30, 125, 120, 0.09),
                transparent 30%
            ),
            var(--bg);
        color: var(--text);
        font-family: 'Inter', sans-serif;
    }}

    [data-testid="stHeader"] {{
        background: rgba(7, 17, 31, 0.85);
    }}

    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #0B1928, #07111F);
        border-right: 1px solid rgba(53, 231, 255, 0.18);
    }}

    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 1.5rem;
    }}

    h1, h2, h3 {{
        color: var(--text) !important;
        letter-spacing: -0.5px;
    }}

    h1 {{
        font-family: 'Orbitron', sans-serif !important;
        font-size: clamp(1.5rem, 3vw, 2.3rem) !important;
    }}

    h2, h3 {{
        font-weight: 700 !important;
    }}

    p, label, .stCaption {{
        color: var(--muted);
    }}

    [data-testid="stMetric"] {{
        background: linear-gradient(
            145deg,
            rgba(18, 36, 56, 0.96),
            rgba(10, 25, 40, 0.96)
        );
        border: 1px solid rgba(53, 231, 255, 0.18);
        border-radius: 15px;
        padding: 18px 20px;
        box-shadow: 0 5px 24px rgba(0, 0, 0, 0.12);
        transition: border-color 0.2s, transform 0.2s;
    }}

    [data-testid="stMetric"]:hover {{
        border-color: rgba(53, 231, 255, 0.65);
        transform: translateY(-2px);
    }}

    [data-testid="stMetricLabel"] {{
        color: {MUTED} !important;
        font-size: 0.79rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    [data-testid="stMetricValue"] {{
        color: {CYAN} !important;
        font-family: 'Orbitron', sans-serif;
        font-size: clamp(1.3rem, 2.5vw, 2rem) !important;
    }}

    [data-testid="stDataFrame"] {{
        border: 1px solid rgba(53, 231, 255, 0.15);
        border-radius: 12px;
        overflow: hidden;
    }}

    div.stButton > button {{
        border-radius: 10px;
        border: 1px solid rgba(53, 231, 255, 0.4);
        background: linear-gradient(
            100deg,
            rgba(20, 108, 138, 0.35),
            rgba(24, 145, 128, 0.20)
        );
        color: {WHITE};
        font-weight: 600;
        transition: all 0.2s ease;
    }}

    div.stButton > button:hover {{
        border-color: {CYAN};
        color: {CYAN};
        box-shadow: 0 0 18px rgba(53, 231, 255, 0.15);
    }}

    div[data-baseweb="select"] > div {{
        background: #102235;
        border-color: rgba(53, 231, 255, 0.25);
        border-radius: 9px;
    }}

    [data-testid="stTabs"] button {{
        font-weight: 600;
    }}

    [data-testid="stTabs"] button[aria-selected="true"] {{
        color: {CYAN} !important;
        border-bottom-color: {CYAN} !important;
    }}

    hr {{
        border-color: rgba(53, 231, 255, 0.14);
    }}

    .hero {{
        padding: 26px 28px;
        border-radius: 18px;
        border: 1px solid rgba(53, 231, 255, 0.3);
        background:
            linear-gradient(
                115deg,
                rgba(15, 51, 73, 0.96),
                rgba(10, 30, 47, 0.97) 55%,
                rgba(9, 39, 43, 0.94)
            );
        position: relative;
        overflow: hidden;
        margin: 0 0 20px 0;
    }}

    .hero::after {{
        content: "";
        position: absolute;
        right: -50px;
        top: -90px;
        width: 240px;
        height: 240px;
        border-radius: 50%;
        border: 1px solid rgba(53, 231, 255, 0.16);
        box-shadow:
            0 0 0 25px rgba(53, 231, 255, 0.025),
            0 0 0 55px rgba(53, 231, 255, 0.02);
        pointer-events: none;
    }}

    .eyebrow {{
        font-size: 0.70rem;
        font-weight: 800;
        letter-spacing: 2.7px;
        color: {CYAN};
        text-transform: uppercase;
    }}

    .hero-title {{
        font-family: 'Orbitron', sans-serif;
        font-size: clamp(1.6rem, 3.5vw, 2.65rem);
        font-weight: 800;
        line-height: 1.2;
        margin: 9px 0;
        color: #F4FBFF;
    }}

    .hero-subtitle {{
        color: #A9C2D6;
        font-size: 0.91rem;
        max-width: 680px;
        line-height: 1.7;
    }}

    .status-pill {{
        display: inline-block;
        padding: 6px 11px;
        border-radius: 7px;
        border: 1px solid rgba(55, 230, 193, 0.4);
        background: rgba(55, 230, 193, 0.08);
        color: {TEAL};
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 1px;
        margin-top: 14px;
    }}

    .section-label {{
        color: {CYAN};
        font-size: 0.70rem;
        font-weight: 800;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 5px;
    }}

    .agent-card {{
        min-height: 160px;
        background: linear-gradient(145deg, #102438, #0A1725);
        border: 1px solid rgba(53, 231, 255, 0.18);
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 8px;
    }}

    .agent-icon {{
        font-size: 1.5rem;
        margin-bottom: 12px;
    }}

    .agent-name {{
        color: #EDF7FF;
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 7px;
    }}

    .agent-detail {{
        color: #91A7BC;
        font-size: 0.78rem;
        line-height: 1.6;
    }}

    .event-card {{
        background: rgba(13, 27, 42, 0.85);
        border-left: 3px solid {CYAN};
        border-radius: 5px 12px 12px 5px;
        padding: 12px 15px;
        margin: 9px 0;
    }}

    .event-title {{
        font-weight: 700;
        color: #EDF7FF;
        font-size: 0.88rem;
    }}

    .event-detail {{
        font-size: 0.78rem;
        color: #91A7BC;
        margin-top: 5px;
        line-height: 1.6;
    }}

    .footer {{
        text-align: center;
        color: #637C91;
        font-size: 0.75rem;
        padding: 24px 0 8px 0;
        letter-spacing: 0.5px;
    }}

    .disclaimer {{
        padding: 11px 14px;
        background: rgba(255, 198, 109, 0.06);
        border: 1px solid rgba(255, 198, 109, 0.22);
        border-radius: 10px;
        color: #EBCB97;
        font-size: 0.79rem;
        line-height: 1.6;
    }}

    @media (max-width: 700px) {{
        .hero {{
            padding: 20px;
        }}
        .hero-subtitle {{
            font-size: 0.82rem;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# PLOTLY THEME
# =========================================================

def style_chart(fig, height=330):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, sans-serif",
            color=MUTED,
            size=12,
        ),
        title_font=dict(
            family="Inter, sans-serif",
            size=15,
            color=WHITE,
        ),
        height=height,
        margin=dict(l=12, r=12, t=55, b=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        hoverlabel=dict(
            bgcolor=PANEL,
            font_color=WHITE,
        ),
    )
    return fig


# =========================================================
# DATA
# =========================================================

@st.cache_data
def load_scenario():
    with SCENARIO_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


try:
    base_scenario = load_scenario()
except (OSError, json.JSONDecodeError) as error:
    st.error(f"Could not load the scenario file: {error}")
    st.stop()


def build_demo_scenarios(base):
    """Build fictional demo presets from the project's existing scenario data."""
    presets = {}

    flood = deepcopy(base)
    flood["name"] = "Riverdale Flood Response"
    flood["description"] = (
        "Fictional flood-response exercise using the bundled scenario data."
    )
    presets["Riverdale Flood Response"] = flood

    coastal = deepcopy(base)
    coastal["name"] = "Coastal Storm Drill"
    coastal["description"] = (
        "Fictional coastal-storm exercise using simulated incidents and resources."
    )
    for task in coastal.get("tasks", []):
        task["name"] = f"Coastal storm drill — {task.get('name', task.get('id', 'Incident'))}"
    presets["Coastal Storm Drill"] = coastal

    urban = deepcopy(base)
    urban["name"] = "Urban Road Blockage Drill"
    urban["description"] = (
        "Fictional urban road-disruption exercise; priorities are demo settings."
    )
    demo_priorities = {"T1": "high", "T2": "critical", "T3": "high",
                       "T4": "medium", "T5": "critical", "T6": "medium"}
    for task in urban.get("tasks", []):
        task["name"] = f"Urban blockage drill — {task.get('name', task.get('id', 'Incident'))}"
        if task.get("id") in demo_priorities:
            task["priority"] = demo_priorities[task["id"]]
    presets["Urban Road Blockage Drill"] = urban
    return presets


scenario_presets = build_demo_scenarios(base_scenario)

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 4px 0 20px 0;">
            <div style="font-size: 2rem;">🚨</div>
            <div style="
                font-family: Orbitron, sans-serif;
                font-size: 1.15rem;
                font-weight: 800;
                color: {CYAN};
                letter-spacing: 1px;
                margin-top: 8px;
            ">ASTRARESQ AI</div>
            <div style="
                color: {MUTED};
                font-size: 0.68rem;
                letter-spacing: 1.5px;
                margin-top: 6px;
            ">RESPONSE COMMAND CENTER</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown(
        f'<div class="section-label">COMMAND NAVIGATION</div>',
        unsafe_allow_html=True,
    )

    active_page = st.radio(
        "Navigation",
        [
            "Overview",
            "Map & Routes",
            "AI Agents",
            "ConflictLab",
            "Decision Timeline",
            "Validation",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        '<div class="section-label">SIMULATION CONTROL</div>',
        unsafe_allow_html=True,
    )

    selected_scenario_name = st.selectbox(
        "Choose disaster scenario",
        options=list(scenario_presets.keys()),
        key="selected_scenario_name",
        help="Choose a fictional scenario for the educational demonstration.",
    )
    scenario = deepcopy(scenario_presets[selected_scenario_name])
    st.caption(scenario.get("description", "Fictional educational simulation."))

    # A scenario change invalidates results calculated for the previous scenario.
    previous_scenario_name = st.session_state.get("active_scenario_name")
    if previous_scenario_name != selected_scenario_name:
        st.session_state.simulation_result = None
        st.session_state.active_scenario_name = selected_scenario_name

    route_ids = sorted({
        task["route_id"]
        for task in scenario.get("tasks", [])
        if task.get("route_id")
    })

    selected_route = None

    if route_ids:
        selected_route = st.selectbox(
            "Select route to block",
            options=route_ids,
        )

        simulate_button = st.button(
            "⚡  RUN DISRUPTION TEST",
            use_container_width=True,
        )
    else:
        simulate_button = False
        st.warning("No routes found in the scenario.")

    if st.button(
        "↻  RESET SIMULATION",
        use_container_width=True,
    ):
        st.session_state.simulation_result = None
        st.rerun()

    st.markdown("---")
    st.caption("PROJECT · EKAGRAH")
    st.caption("MODE · EDUCATIONAL SIMULATION")
    st.caption("ENGINE · MULTI-AGENT COORDINATION")


# =========================================================
# SIMULATION STATE
# =========================================================

if "simulation_result" not in st.session_state:
    st.session_state.simulation_result = None

if simulate_button and selected_route:
    try:
        st.session_state.simulation_result = simulate_disruption(
            scenario,
            selected_route,
        )
    except ValueError as error:
        st.error(str(error))
    except Exception as error:
        st.error(
            f"Simulation failed: {error}. "
            "Check the terminal for diagnostic details."
        )

simulation_result = st.session_state.simulation_result

try:
    if simulation_result:
        active_scenario = simulation_result.get(
            "scenario",
            scenario,
        )
        original_plan = simulation_result["original_plan"]
        result = simulation_result["revised_plan"]
    else:
        active_scenario = scenario
        original_plan = None
        result = coordinate_response(active_scenario)

    comparison = compare_planners(active_scenario)

except Exception as error:
    st.error(f"Could not generate the response plan: {error}")
    st.stop()


# =========================================================
# NORMALIZE RESULTS
# =========================================================

assignments = result.get("assignments", [])
validation = result.get("validation", {})
conflicts = result.get("conflicts", [])
decision_log = result.get("decision_log", [])

tasks = active_scenario.get("tasks", [])
vehicles = active_scenario.get("vehicles", [])

total_tasks = len(tasks)

assigned_task_ids = {
    assignment.get("task_id")
    for assignment in assignments
}

assigned_tasks = len(assigned_task_ids)
unassigned_tasks = max(total_tasks - assigned_tasks, 0)

available_vehicles = sum(
    1
    for vehicle in vehicles
    if vehicle.get("available", False)
)

plan_valid = validation.get("valid", False)

# Handle different agent naming formats, e.g. "rescue" or "Rescue Agent".
def normalize_agent_name(name):
    value = str(name or "").strip().lower()
    value = value.replace("_", " ").replace("-", " ")

    for suffix in (" agent",):
        if value.endswith(suffix):
            value = value[:-len(suffix)]

    return value.strip()


agent_definitions = [
    ("🛟", "Rescue Agent", "rescue", "Rescue and rescue-task coordination"),
    ("✚", "Medical Agent", "medical", "Medical-support task coordination"),
    ("🚐", "Transport Agent", "transport", "Transport and evacuation tasks"),
    ("📦", "Supply Agent", "supply", "Supply and delivery tasks"),
]


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">EKAGRAH · INTELLIGENT RESPONSE NETWORK</div>
        <div class="hero-title">ASTRARESQ AI</div>
        <div class="hero-subtitle">
            A multi-agent command environment for simulated disaster response,
            resource allocation, disruption analysis and explainable planning.
        </div>
        <div class="status-pill">● SIMULATION ENVIRONMENT ACTIVE</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="disclaimer">
        ⚠ SIMULATION ONLY — This educational prototype does not provide
        real-world emergency dispatch, verified route safety, or operational
        emergency-response guidance.
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(f"**Active demo scenario:** {selected_scenario_name}")

if simulation_result:
    disruption = simulation_result.get("disruption", {})
    blocked_route = disruption.get("route_id", selected_route)

    st.warning(
        f"Disruption scenario active: route {blocked_route} is marked blocked. "
        "The revised plan reflects the current simulation."
    )

st.write("")

st.markdown(
    f'<div class="section-label">{"COMMAND OVERVIEW" if active_page == "Overview" else active_page.upper()}</div>',
    unsafe_allow_html=True,
)


# =========================================================
# TOP METRICS
# =========================================================

metric_cols = st.columns(4)

metric_cols[0].metric(
    "TOTAL TASKS",
    total_tasks,
)

metric_cols[1].metric(
    "ASSIGNED TASKS",
    assigned_tasks,
    delta=f"{assigned_tasks / total_tasks:.0%} coverage"
    if total_tasks else "No tasks",
)

metric_cols[2].metric(
    "AVAILABLE VEHICLES",
    available_vehicles,
)

metric_cols[3].metric(
    "PLAN STATUS",
    "VALID" if plan_valid else "REVIEW",
    delta="Constraint check passed" if plan_valid else "Check validation",
    delta_color="normal" if plan_valid else "inverse",
)

st.write("")


# =========================================================
# OVERVIEW PAGE
# =========================================================

if active_page == "Overview":

    left, right = st.columns([1.45, 1])

    with left:
        st.subheader("◈ Response Assignment Matrix")
        st.caption("Current allocation generated by the coordination engine.")

        if assignments:
            assignment_df = pd.DataFrame(assignments)

            rename_columns = {
                "task_id": "Task ID",
                "vehicle_id": "Vehicle ID",
                "agent": "Assigned Agent",
            }

            assignment_df = assignment_df.rename(
                columns=rename_columns
            )

            st.dataframe(
                assignment_df,
                width="stretch",
                hide_index=True,
            )
        else:
            st.warning("No assignments could be generated.")

    with right:
        st.subheader("◈ Task Coverage")
        st.caption("Assigned versus unassigned tasks.")

        coverage_df = pd.DataFrame({
            "Status": ["Assigned", "Unassigned"],
            "Tasks": [assigned_tasks, unassigned_tasks],
        })

        fig = px.pie(
            coverage_df,
            names="Status",
            values="Tasks",
            hole=0.68,
            color="Status",
            color_discrete_map={
                "Assigned": TEAL,
                "Unassigned": RED,
            },
        )

        fig.update_traces(
            textposition="inside",
            textinfo="label+value",
            marker=dict(
                line=dict(color=BG, width=3)
            ),
            hole=0.68,
        )

        fig.add_annotation(
            text=f"<b>{assigned_tasks}/{total_tasks}</b>",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=21, color=WHITE),
        )

        st.plotly_chart(
            style_chart(fig, 315),
            width="stretch",
        )

    # Priority-ranked task queue
    st.write("")
    st.subheader("◈ Priority-Ranked Task Queue")
    st.caption(
        "Tasks are ranked by their configured priority. These labels are "
        "illustrative simulation settings, not real-world emergency guidance."
    )

    priority_order = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }

    ranked_tasks = sorted(
        tasks,
        key=lambda task: priority_order.get(
            str(task.get("priority", "medium")).strip().lower(),
            2,
        ),
    )

    assignment_by_task = {
        assignment.get("task_id"): assignment
        for assignment in assignments
    }

    if ranked_tasks:
        queue_rows = []
        for rank, task in enumerate(ranked_tasks, start=1):
            priority = str(task.get("priority", "medium")).strip().lower()
            assignment = assignment_by_task.get(task.get("id"), {})
            queue_rows.append({
                "Rank": rank,
                "Task ID": task.get("id", "—"),
                "Task": task.get("name", "Unnamed task"),
                "Priority": priority.upper(),
                "Agent": assignment.get("agent", task.get("agent", "Unassigned")),
                "Vehicle": assignment.get("vehicle_id", "Unassigned"),
                "Assignment Status": (
                    "Assigned" if assignment else "Unassigned"
                ),
                "Why this rank?": {
                    "critical": "Configured as critical; ranked first among priority levels.",
                    "high": "Configured as high priority.",
                    "medium": "Configured as medium priority.",
                    "low": "Configured as low priority.",
                }.get(priority, "Unknown priority; treated as medium."),
            })

        st.dataframe(
            pd.DataFrame(queue_rows),
            width="stretch",
            hide_index=True,
        )

        first_task = ranked_tasks[0]
        first_priority = str(
            first_task.get("priority", "medium")
        ).strip().lower()
        first_assignment = assignment_by_task.get(first_task.get("id"), {})

        st.markdown("#### ◈ Why is this task first?")
        st.info(
            f"**{first_task.get('id', '—')} — "
            f"{first_task.get('name', 'Unnamed task')}**\n\n"
            f"Configured priority: **{first_priority.upper()}**. "
            "The queue orders tasks by configured priority: critical, high, "
            "medium, then low. Equal-priority tasks retain their scenario order. "
            + (
                f"The coordinator assigned vehicle "
                f"{first_assignment.get('vehicle_id')} to this task."
                if first_assignment
                else "This task is currently unassigned; check vehicle availability "
                     "and route constraints in the Validation and Decision Timeline pages."
            )
            + " This explanation reflects simulation rules, not an assessment "
              "of actual emergency severity."
        )
    else:
        st.info("No tasks are available to rank.")

    st.write("")
    st.subheader("◈ Agent Network")

    agent_cols = st.columns(4)

    for column, definition in zip(agent_cols, agent_definitions):
        icon, display_name, agent_key, description = definition

        agent_tasks = [
            assignment
            for assignment in assignments
            if normalize_agent_name(
                assignment.get("agent")
            ) == agent_key
        ]

        with column:
            st.markdown(
                f"""
                <div class="agent-card">
                    <div class="agent-icon">{icon}</div>
                    <div class="agent-name">{display_name}</div>
                    <div class="agent-detail">{description}</div>
                    <div style="
                        color: {CYAN};
                        font-family: Orbitron, sans-serif;
                        font-size: 1.5rem;
                        margin-top: 15px;
                    ">{len(agent_tasks):02d}
                    <span style="
                        font-family: Inter, sans-serif;
                        font-size: 0.7rem;
                        color: {MUTED};
                    ">ASSIGNED</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")
    st.subheader("◈ Planner Performance Snapshot")

    baseline = comparison["baseline"]["metrics"]
    multi = comparison["multi_agent"]["metrics"]

    perf_df = pd.DataFrame([
        {
            "Planner": "Baseline",
            "Assigned": baseline["assigned_tasks"],
            "Unassigned": baseline["unassigned_tasks"],
        },
        {
            "Planner": "Multi-Agent",
            "Assigned": multi["assigned_tasks"],
            "Unassigned": multi["unassigned_tasks"],
        },
    ])

    perf_fig = px.bar(
        perf_df,
        x="Planner",
        y=["Assigned", "Unassigned"],
        barmode="group",
        color_discrete_sequence=[TEAL, RED],
        labels={"value": "Tasks", "variable": "Outcome"},
    )

    st.plotly_chart(
        style_chart(perf_fig, 320),
        width="stretch",
    )


# =========================================================
# AI AGENTS PAGE
# =========================================================

elif active_page == "Map & Routes":

    st.subheader("◈ Interactive Road Network & Route Planning")
    st.caption(
        "Fictional schematic network for education. Distances are schematic units, "
        "not kilometres; this is not a real-world navigation or safety service."
    )

    try:
        with (BASE_DIR / "data" / "road_network.json").open("r", encoding="utf-8") as file:
            road_network = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        st.error(f"Could not load the road network: {error}")
        st.stop()

    road_nodes = {node["id"]: node for node in road_network.get("nodes", [])}
    road_lookup = {road["id"]: road for road in road_network.get("roads", [])}
    destinations = road_network.get("destinations", {})

    if "map_blocked_roads" not in st.session_state:
        st.session_state.map_blocked_roads = []

    control_left, control_right = st.columns(2)
    with control_left:
        destination_labels = {
            node_id: f"{node.get('name', node_id)} ({node_id})"
            for node_id, node in road_nodes.items()
            if node_id != "HQ"
        }
        destination_id = st.selectbox(
            "Destination zone",
            options=list(destination_labels),
            format_func=lambda value: destination_labels[value],
            key="route_destination",
        )
    with control_right:
        blocked_road_ids = st.multiselect(
            "Mark roads as blocked (map simulation only)",
            options=list(road_lookup),
            default=[road_id for road_id in st.session_state.map_blocked_roads if road_id in road_lookup],
            format_func=lambda value: f"{value} — {road_lookup[value].get('name', value)}",
            key="map_blocked_roads_widget",
        )
        st.session_state.map_blocked_roads = blocked_road_ids

    primary_route = find_route(road_network, "HQ", destination_id, blocked_road_ids)
    alternative_route = find_alternative_route(road_network, "HQ", destination_id, blocked_road_ids)

    if primary_route is None:
        st.error("No route is available in this schematic network with the selected blocked roads.")
    else:
        route_cols = st.columns(2)
        route_cols[0].metric("Primary route segments", len(primary_route["roads"]))
        route_cols[1].metric("Primary route distance", f"{primary_route['distance']:.2f} units")
        st.write(
            "**Primary route:** " + " → ".join(
                road_nodes[node_id].get("name", node_id) for node_id in primary_route["nodes"]
            )
        )
        if alternative_route:
            st.write(
                "**Alternative route:** " + " → ".join(
                    road_nodes[node_id].get("name", node_id) for node_id in alternative_route["nodes"]
                )
            )
            st.caption(
                f"Alternative distance: {alternative_route['distance']:.2f} schematic units. "
                "The alternative is a graph-based candidate, not a verified safe route."
            )
        else:
            st.info("No distinct alternative route was found for this selection.")

    # Interactive Plotly schematic: click/hover roads and nodes for details.
    map_fig = go.Figure()
    primary_road_set = set(primary_route["roads"]) if primary_route else set()
    alternative_road_set = set(alternative_route["roads"]) if alternative_route else set()
    blocked_road_set = set(blocked_road_ids)

    for road in road_network.get("roads", []):
        start = road_nodes[road["from"]]
        end = road_nodes[road["to"]]
        road_id = road["id"]
        if road_id in blocked_road_set:
            line_color, line_width, dash = RED, 4, "dash"
        elif road_id in primary_road_set:
            line_color, line_width, dash = TEAL, 5, "solid"
        elif road_id in alternative_road_set:
            line_color, line_width, dash = AMBER, 3, "dot"
        else:
            line_color, line_width, dash = "#49657C", 1.5, "solid"
        map_fig.add_trace(go.Scatter(
            x=[start["x"], end["x"]], y=[start["y"], end["y"]],
            mode="lines", name=road_id,
            line=dict(color=line_color, width=line_width, dash=dash),
            text=[f"{road_id}: {road.get('name', road_id)}"] * 2,
            hovertemplate="%{text}<extra></extra>",
            showlegend=False,
        ))

    map_fig.add_trace(go.Scatter(
        x=[node["x"] for node in road_network["nodes"]],
        y=[node["y"] for node in road_network["nodes"]],
        mode="markers+text",
        text=[node.get("name", node["id"]) for node in road_network["nodes"]],
        textposition="top center",
        customdata=[node["id"] for node in road_network["nodes"]],
        marker=dict(size=13, color=[TEAL if node["id"] == "HQ" else CYAN for node in road_network["nodes"]], line=dict(width=1, color=WHITE)),
        hovertemplate="%{text}<br>Node: %{customdata}<extra></extra>",
        name="Zones and junctions",
    ))
    map_fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(7,17,31,1)", font=dict(color=WHITE),
        height=560, margin=dict(l=15, r=15, t=20, b=15),
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
        legend=dict(orientation="h"),
    )
    st.plotly_chart(map_fig, width="stretch")
    st.markdown(
        f"<div class='disclaimer'>🟢 Primary route · 🟠 Alternative candidate · 🔴 Blocked road. "
        "This schematic uses fictional nodes and roads. It does not use live traffic, "
        "verified road closures, or geographic coordinates.</div>",
        unsafe_allow_html=True,
    )

    st.divider()
    st.subheader("◈ Authorized Camera Preview")
    st.caption(
        "Enter a camera stream URL only if you own it or have permission to access it. "
        "This milestone captures one preview frame when you click the button; it does not record video."
    )
    camera_url = st.text_input(
        "RTSP / RTSPS / HTTP(S) stream URL",
        type="password",
        placeholder="rtsp://camera-address/stream",
        help="Do not paste a camera URL you are not authorized to access. The URL is not saved to a project file.",
        key="authorized_camera_url",
    )
    if st.button("📷 Capture camera preview frame", key="capture_camera_frame_button"):
        if not camera_url.strip():
            st.warning("Enter an authorized camera stream URL first.")
        else:
            try:
                with st.spinner("Connecting to the authorized camera and capturing one frame..."):
                    frame = capture_camera_frame(camera_url)
                st.session_state.camera_preview_frame = frame
                st.success("Frame captured. No video was recorded or saved by this feature.")
            except (ValueError, RuntimeError) as error:
                st.error(str(error))
    if st.session_state.get("camera_preview_frame") is not None:
        st.image(st.session_state.camera_preview_frame, caption="Latest captured preview frame", width="stretch")
    st.info(
        "Camera detections are not implemented yet. The preview only displays a frame; it does not "
        "automatically detect fire, floodwater, damaged roads, people, or route safety."
    )


elif active_page == "AI Agents":

    st.subheader("◈ Specialized Agent Operations")
    st.caption(
        "Inspect each agent's current task allocation. "
        "Counts reflect the current simulated plan."
    )

    agent_cols = st.columns(2)

    for index, definition in enumerate(agent_definitions):
        icon, display_name, agent_key, description = definition

        agent_tasks = [
            assignment
            for assignment in assignments
            if normalize_agent_name(
                assignment.get("agent")
            ) == agent_key
        ]

        with agent_cols[index % 2]:
            with st.container(border=True):
                st.markdown(f"### {icon} {display_name}")
                st.caption(description)

                st.metric(
                    "Assigned tasks",
                    len(agent_tasks),
                )

                if agent_tasks:
                    st.dataframe(
                        pd.DataFrame(agent_tasks),
                        width="stretch",
                        hide_index=True,
                    )
                else:
                    st.info("No tasks assigned to this agent.")

    st.subheader("◈ Task-to-Agent Mapping")

    if tasks:
        task_df = pd.DataFrame(tasks)

        task_df["Assignment Status"] = task_df["id"].apply(
            lambda task_id: (
                "Assigned"
                if task_id in assigned_task_ids
                else "Unassigned"
            )
        )

        st.dataframe(
            task_df,
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("The scenario contains no tasks.")


# =========================================================
# CONFLICTLAB PAGE
# =========================================================

elif active_page == "ConflictLab":

    st.subheader("◈ Baseline vs Multi-Agent Planner")
    st.caption(
        "Both strategies are evaluated on the same active scenario. "
        "Metrics describe this simulation, not real-world performance."
    )

    baseline_result = comparison["baseline"]["result"]
    multi_result = comparison["multi_agent"]["result"]

    baseline_metrics = comparison["baseline"]["metrics"]
    multi_metrics = comparison["multi_agent"]["metrics"]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "BASELINE ASSIGNED",
        baseline_metrics["assigned_tasks"],
    )

    c2.metric(
        "MULTI-AGENT ASSIGNED",
        multi_metrics["assigned_tasks"],
        delta=(
            multi_metrics["assigned_tasks"]
            - baseline_metrics["assigned_tasks"]
        ),
    )

    c3.metric(
        "BASELINE CONFLICTS",
        baseline_metrics["conflicts"],
    )

    c4.metric(
        "MULTI-AGENT CONFLICTS",
        multi_metrics["conflicts"],
        delta=(
            multi_metrics["conflicts"]
            - baseline_metrics["conflicts"]
        ),
        delta_color="inverse",
    )

    st.write("")

    comparison_df = pd.DataFrame([
        {
            "Metric": "Assigned tasks",
            "Baseline": baseline_metrics["assigned_tasks"],
            "Multi-Agent": multi_metrics["assigned_tasks"],
        },
        {
            "Metric": "Unassigned tasks",
            "Baseline": baseline_metrics["unassigned_tasks"],
            "Multi-Agent": multi_metrics["unassigned_tasks"],
        },
        {
            "Metric": "Recorded conflicts",
            "Baseline": baseline_metrics["conflicts"],
            "Multi-Agent": multi_metrics["conflicts"],
        },
        {
            "Metric": "Constraint violations",
            "Baseline": baseline_metrics["constraint_violations"],
            "Multi-Agent": multi_metrics["constraint_violations"],
        },
    ])

    st.dataframe(
        comparison_df,
        width="stretch",
        hide_index=True,
    )

    left, right = st.columns(2)

    with left:
        st.markdown("#### Allocation Comparison")

        chart_df = pd.DataFrame([
            {
                "Planner": "Baseline",
                "Assigned": baseline_metrics["assigned_tasks"],
                "Unassigned": baseline_metrics["unassigned_tasks"],
            },
            {
                "Planner": "Multi-Agent",
                "Assigned": multi_metrics["assigned_tasks"],
                "Unassigned": multi_metrics["unassigned_tasks"],
            },
        ])

        fig = px.bar(
            chart_df,
            x="Planner",
            y=["Assigned", "Unassigned"],
            barmode="group",
            color_discrete_sequence=[TEAL, RED],
        )

        st.plotly_chart(
            style_chart(fig),
            width="stretch",
        )

    with right:
        st.markdown("#### Constraint Violations")

        violation_df = pd.DataFrame([
            {
                "Planner": "Baseline",
                "Violations": baseline_metrics["constraint_violations"],
            },
            {
                "Planner": "Multi-Agent",
                "Violations": multi_metrics["constraint_violations"],
            },
        ])

        fig = px.bar(
            violation_df,
            x="Planner",
            y="Violations",
            color="Planner",
            color_discrete_map={
                "Baseline": AMBER,
                "Multi-Agent": CYAN,
            },
        )

        st.plotly_chart(
            style_chart(fig),
            width="stretch",
        )

    with st.expander("Inspect baseline assignments"):
        st.dataframe(
            pd.DataFrame(baseline_result.get("assignments", [])),
            width="stretch",
            hide_index=True,
        )

    with st.expander("Inspect multi-agent assignments"):
        st.dataframe(
            pd.DataFrame(multi_result.get("assignments", [])),
            width="stretch",
            hide_index=True,
        )

    with st.expander("Inspect coordinator conflicts"):
        recorded_conflicts = multi_result.get("conflicts", [])

        if recorded_conflicts:
            for conflict in recorded_conflicts:
                st.markdown(
                    f"- {conflict}"
                )
        else:
            st.success("No conflicts were recorded.")

    st.caption(
        "A comparison result depends on the current scenario, "
        "resource availability, and planner implementation."
    )


# =========================================================
# DECISION TIMELINE PAGE
# =========================================================

elif active_page == "Decision Timeline":

    st.subheader("◈ Coordination Decision History")
    st.caption(
        "Events recorded by the coordinator for the current plan."
    )

    if decision_log:
        event_types = sorted({
            str(event.get("event", "unknown"))
            for event in decision_log
        })

        selected_events = st.multiselect(
            "Filter event types",
            options=event_types,
            default=event_types,
        )

        filtered_events = [
            event
            for event in decision_log
            if str(event.get("event", "unknown")) in selected_events
        ]

        st.metric("Recorded events", len(filtered_events))

        for index, event in enumerate(filtered_events, start=1):
            event_type = event.get("event", "unknown")
            task_id = event.get("task_id", "—")
            vehicle_id = event.get(
                "assigned_vehicle",
                event.get("proposed_vehicle", "—"),
            )
            reason = event.get("reason", "No reason recorded.")

            if event_type == "assignment_accepted":
                accent = TEAL
                icon = "✓"
            elif event_type == "reassignment":
                accent = AMBER
                icon = "↻"
            elif event_type in (
                "proposal_rejected",
                "assignment_rejected",
                "task_unassigned",
            ):
                accent = RED
                icon = "!"
            elif event_type == "plan_validated":
                accent = CYAN
                icon = "◈"
            else:
                accent = CYAN
                icon = "•"

            st.markdown(
                f"""
                <div class="event-card"
                     style="border-left-color: {accent};">
                    <div class="event-title">
                        <span style="color: {accent};">{icon}</span>
                        &nbsp; {index:02d} · {event_type.replace("_", " ").upper()}
                    </div>
                    <div class="event-detail">
                        Task: {task_id}
                        &nbsp; | &nbsp; Vehicle: {vehicle_id}
                    </div>
                    <div class="event-detail">{reason}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("View raw decision log"):
            st.dataframe(
                pd.DataFrame(filtered_events),
                width="stretch",
                hide_index=True,
            )

    else:
        st.info(
            "The coordinator did not return a decision log. "
            "Check that the active coordinator includes decision_log."
        )

    st.subheader("◈ Conflict Summary")

    if conflicts:
        for conflict in conflicts:
            st.warning(conflict)
    else:
        st.success("No coordinator conflicts were recorded.")


# =========================================================
# VALIDATION PAGE
# =========================================================

elif active_page == "Validation":

    st.subheader("◈ Constraint Validation Center")
    st.caption(
        "Validation results returned by the existing backend validator."
    )

    if plan_valid:
        st.success("✓ The current plan passed the constraint checks.")
    else:
        st.error("! The current plan did not pass all constraint checks.")

    errors = validation.get("errors", [])
    warnings = validation.get("warnings", [])

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Plan Status",
        "VALID" if plan_valid else "REVIEW",
    )

    c2.metric(
        "Reported Errors",
        len(errors),
    )

    c3.metric(
        "Reported Warnings",
        len(warnings),
    )

    st.write("")

    left, right = st.columns(2)

    with left:
        st.markdown("#### Validation Errors")

        if errors:
            for error in errors:
                st.error(str(error))
        else:
            st.success("No validation errors reported.")

    with right:
        st.markdown("#### Validation Warnings")

        if warnings:
            for warning in warnings:
                st.warning(str(warning))
        else:
            st.success("No validation warnings reported.")

    st.subheader("◈ Current Assignments")

    if assignments:
        st.dataframe(
            pd.DataFrame(assignments),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("There are no assignments to inspect.")


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
        ASTRARESQ AI &nbsp;·&nbsp; EKAGRAH (एकाग्र)
        <br><br>
        MULTI-AGENT DISASTER RESPONSE SIMULATION
        <br>
        EDUCATIONAL PROTOTYPE · NOT FOR REAL-WORLD DISPATCH
    </div>
    """,
    unsafe_allow_html=True,
)
