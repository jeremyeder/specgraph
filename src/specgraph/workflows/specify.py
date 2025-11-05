"""Specify workflow - Generate product specifications using LangGraph."""

from pathlib import Path
from typing import TypedDict

from anthropic import Anthropic
from langgraph.graph import END, START, StateGraph

from specgraph.prompts.specify_prompts import (
    SPECIFY_SYSTEM_PROMPT,
    get_specify_prompt,
)
from specgraph.utils.file_manager import create_spec_directory, save_markdown


class SpecifyState(TypedDict):
    """State for the specify workflow."""

    feature_description: str
    specification: str
    spec_path: Path
    spec_number: int
    error: str | None


def analyze_input(state: SpecifyState) -> dict:
    """Analyze and validate the feature description.

    Args:
        state: Current workflow state

    Returns:
        Updated state with any validation errors
    """
    feature_desc = state.get("feature_description", "").strip()

    if not feature_desc:
        return {"error": "Feature description cannot be empty"}

    if len(feature_desc) < 10:
        return {"error": "Feature description is too short (minimum 10 characters)"}

    return {"error": None}


def generate_specification(state: SpecifyState) -> dict:
    """Generate product specification using Claude.

    Args:
        state: Current workflow state

    Returns:
        Updated state with generated specification
    """
    # Skip if there's an error
    if state.get("error"):
        return {}

    client = Anthropic()

    user_prompt = get_specify_prompt(state["feature_description"])

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SPECIFY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    specification = response.content[0].text

    return {"specification": specification}


def save_specification(state: SpecifyState) -> dict:
    """Save the specification to a file.

    Args:
        state: Current workflow state

    Returns:
        Updated state with spec path information
    """
    # Skip if there's an error
    if state.get("error"):
        return {}

    # Create spec directory
    spec_path, spec_number = create_spec_directory(state["feature_description"])

    # Save specification
    spec_file = spec_path / "specification.md"
    save_markdown(state["specification"], spec_file)

    return {"spec_path": spec_path, "spec_number": spec_number}


def should_continue(state: SpecifyState) -> str:
    """Determine if workflow should continue or end with error.

    Args:
        state: Current workflow state

    Returns:
        Next node name or END
    """
    if state.get("error"):
        return END
    return "generate"


def build_specify_workflow() -> StateGraph:
    """Build the specify workflow graph.

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(SpecifyState)

    # Add nodes
    workflow.add_node("analyze", analyze_input)
    workflow.add_node("generate", generate_specification)
    workflow.add_node("save", save_specification)

    # Add edges
    workflow.add_edge(START, "analyze")
    workflow.add_conditional_edges(
        "analyze", should_continue, {"generate": "generate", END: END}
    )
    workflow.add_edge("generate", "save")
    workflow.add_edge("save", END)

    return workflow.compile()


def run_specify(feature_description: str) -> SpecifyState:
    """Run the specify workflow.

    Args:
        feature_description: Description of the feature to specify

    Returns:
        Final workflow state
    """
    workflow = build_specify_workflow()

    initial_state: SpecifyState = {
        "feature_description": feature_description,
        "specification": "",
        "spec_path": Path(),
        "spec_number": 0,
        "error": None,
    }

    result = workflow.invoke(initial_state)
    return result
