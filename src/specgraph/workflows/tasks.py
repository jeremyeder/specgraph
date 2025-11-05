"""Tasks workflow - Generate task breakdowns using LangGraph."""

from pathlib import Path
from typing import TypedDict

from anthropic import Anthropic
from langgraph.graph import END, START, StateGraph

from specgraph.prompts.tasks_prompts import TASKS_SYSTEM_PROMPT, get_tasks_prompt
from specgraph.utils.file_manager import find_latest_spec, save_markdown


class TasksState(TypedDict):
    """State for the tasks workflow."""

    spec_path: Path | None
    specification: str
    plan: str
    tasks: str
    tasks_file: Path | None
    error: str | None


def load_plan(state: TasksState) -> dict:
    """Load the specification and plan from the most recent spec directory.

    Args:
        state: Current workflow state

    Returns:
        Updated state with loaded specification and plan
    """
    # Find the latest spec directory
    spec_path = find_latest_spec()

    if not spec_path:
        return {"error": "No specifications found. Run 'acpctl specify' first."}

    spec_file = spec_path / "specification.md"
    plan_file = spec_path / "plan.md"

    if not spec_file.exists():
        return {
            "error": f"Specification file not found at {spec_file}. "
            "Run 'acpctl specify' first."
        }

    if not plan_file.exists():
        return {
            "error": f"Plan file not found at {plan_file}. " "Run 'acpctl plan' first."
        }

    try:
        specification = spec_file.read_text(encoding="utf-8")
        plan = plan_file.read_text(encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to read specification or plan: {str(e)}"}

    return {
        "spec_path": spec_path,
        "specification": specification,
        "plan": plan,
        "error": None,
    }


def generate_tasks(state: TasksState) -> dict:
    """Generate task breakdown using Claude.

    Args:
        state: Current workflow state

    Returns:
        Updated state with generated tasks
    """
    # Skip if there's an error
    if state.get("error"):
        return {}

    client = Anthropic()

    user_prompt = get_tasks_prompt(state["specification"], state["plan"])

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        system=TASKS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    tasks = response.content[0].text

    return {"tasks": tasks}


def save_tasks(state: TasksState) -> dict:
    """Save the tasks to a file.

    Args:
        state: Current workflow state

    Returns:
        Updated state with tasks file path
    """
    # Skip if there's an error
    if state.get("error"):
        return {}

    # Save tasks in the spec directory
    tasks_file = state["spec_path"] / "tasks.md"
    save_markdown(state["tasks"], tasks_file)

    return {"tasks_file": tasks_file}


def should_continue(state: TasksState) -> str:
    """Determine if workflow should continue or end with error.

    Args:
        state: Current workflow state

    Returns:
        Next node name or END
    """
    if state.get("error"):
        return END
    return "generate"


def build_tasks_workflow() -> StateGraph:
    """Build the tasks workflow graph.

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(TasksState)

    # Add nodes
    workflow.add_node("load", load_plan)
    workflow.add_node("generate", generate_tasks)
    workflow.add_node("save", save_tasks)

    # Add edges
    workflow.add_edge(START, "load")
    workflow.add_conditional_edges(
        "load", should_continue, {"generate": "generate", END: END}
    )
    workflow.add_edge("generate", "save")
    workflow.add_edge("save", END)

    return workflow.compile()


def run_tasks() -> TasksState:
    """Run the tasks workflow.

    Returns:
        Final workflow state
    """
    workflow = build_tasks_workflow()

    initial_state: TasksState = {
        "spec_path": None,
        "specification": "",
        "plan": "",
        "tasks": "",
        "tasks_file": None,
        "error": None,
    }

    result = workflow.invoke(initial_state)
    return result
