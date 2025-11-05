"""Plan workflow - Generate technical plans using LangGraph."""

from pathlib import Path
from typing import TypedDict

from anthropic import Anthropic
from langgraph.graph import END, START, StateGraph

from specgraph.prompts.plan_prompts import PLAN_SYSTEM_PROMPT, get_plan_prompt
from specgraph.utils.file_manager import find_latest_spec, save_markdown


class PlanState(TypedDict):
    """State for the plan workflow."""

    technical_constraints: str
    spec_path: Path | None
    specification: str
    plan: str
    plan_file: Path | None
    error: str | None


def load_specification(state: PlanState) -> dict:
    """Load the specification from the most recent spec directory.

    Args:
        state: Current workflow state

    Returns:
        Updated state with loaded specification
    """
    # Find the latest spec directory
    spec_path = find_latest_spec()

    if not spec_path:
        return {"error": "No specifications found. Run 'acpctl specify' first."}

    spec_file = spec_path / "specification.md"

    if not spec_file.exists():
        return {
            "error": f"Specification file not found at {spec_file}. "
            "Run 'acpctl specify' first."
        }

    try:
        specification = spec_file.read_text(encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to read specification: {str(e)}"}

    return {
        "spec_path": spec_path,
        "specification": specification,
        "error": None,
    }


def generate_plan(state: PlanState) -> dict:
    """Generate technical plan using Claude.

    Args:
        state: Current workflow state

    Returns:
        Updated state with generated plan
    """
    # Skip if there's an error
    if state.get("error"):
        return {}

    client = Anthropic()

    user_prompt = get_plan_prompt(
        state["specification"], state.get("technical_constraints", "")
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=PLAN_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    plan = response.content[0].text

    return {"plan": plan}


def save_plan(state: PlanState) -> dict:
    """Save the plan to a file.

    Args:
        state: Current workflow state

    Returns:
        Updated state with plan file path
    """
    # Skip if there's an error
    if state.get("error"):
        return {}

    # Save plan in the spec directory
    plan_file = state["spec_path"] / "plan.md"
    save_markdown(state["plan"], plan_file)

    return {"plan_file": plan_file}


def should_continue(state: PlanState) -> str:
    """Determine if workflow should continue or end with error.

    Args:
        state: Current workflow state

    Returns:
        Next node name or END
    """
    if state.get("error"):
        return END
    return "generate"


def build_plan_workflow() -> StateGraph:
    """Build the plan workflow graph.

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(PlanState)

    # Add nodes
    workflow.add_node("load", load_specification)
    workflow.add_node("generate", generate_plan)
    workflow.add_node("save", save_plan)

    # Add edges
    workflow.add_edge(START, "load")
    workflow.add_conditional_edges(
        "load", should_continue, {"generate": "generate", END: END}
    )
    workflow.add_edge("generate", "save")
    workflow.add_edge("save", END)

    return workflow.compile()


def run_plan(technical_constraints: str = "") -> PlanState:
    """Run the plan workflow.

    Args:
        technical_constraints: Technical preferences or constraints

    Returns:
        Final workflow state
    """
    workflow = build_plan_workflow()

    initial_state: PlanState = {
        "technical_constraints": technical_constraints,
        "spec_path": None,
        "specification": "",
        "plan": "",
        "plan_file": None,
        "error": None,
    }

    result = workflow.invoke(initial_state)
    return result
