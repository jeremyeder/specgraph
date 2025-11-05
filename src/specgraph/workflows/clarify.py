"""Clarify workflow - Generate and integrate clarifying questions using LangGraph."""

import json
from pathlib import Path
from typing import TypedDict

from anthropic import Anthropic
from langgraph.graph import END, START, StateGraph

from specgraph.prompts.clarify_prompts import (
    CLARIFY_SYSTEM_PROMPT,
    UPDATE_SYSTEM_PROMPT,
    get_analysis_prompt,
    get_update_prompt,
)
from specgraph.utils.file_manager import find_latest_spec, save_markdown


class ClarifyState(TypedDict):
    """State for the clarify workflow."""

    spec_path: Path | None
    specification: str
    questions: list[dict] | None
    answers: dict[int, str] | None
    updated_spec: str
    error: str | None


def load_specification(state: ClarifyState) -> dict:
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


def analyze_and_generate_questions(state: ClarifyState) -> dict:
    """Analyze specification and generate clarifying questions using Claude.

    Args:
        state: Current workflow state

    Returns:
        Updated state with generated questions
    """
    # Skip if there's an error
    if state.get("error"):
        return {}

    client = Anthropic()

    prompt = get_analysis_prompt(state["specification"])

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=CLARIFY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    # Parse the JSON response containing questions
    try:
        response_text = response.content[0].text
        # Extract JSON from markdown code blocks if present
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        questions_data = json.loads(response_text)
        questions = questions_data.get("questions", [])
    except (json.JSONDecodeError, KeyError) as e:
        return {"error": f"Failed to parse questions from Claude response: {str(e)}"}

    return {"questions": questions}


def update_specification(state: ClarifyState) -> dict:
    """Update specification with clarifications using Claude.

    Args:
        state: Current workflow state

    Returns:
        Updated state with modified specification
    """
    # Skip if there's an error or no answers
    if state.get("error") or not state.get("answers"):
        return {}

    # Build Q&A pairs from questions and answers
    qa_pairs = []
    for question in state["questions"]:
        question_id = question["id"]
        if question_id in state["answers"]:
            qa_pairs.append(
                {
                    "id": question_id,
                    "question": question["question"],
                    "answer": state["answers"][question_id],
                }
            )

    if not qa_pairs:
        return {"error": "No answers provided to update specification"}

    client = Anthropic()

    prompt = get_update_prompt(state["specification"], qa_pairs)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        system=UPDATE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    updated_spec = response.content[0].text

    # Remove markdown code fences if present
    if updated_spec.startswith("```markdown"):
        updated_spec = updated_spec[11:]  # Remove ```markdown
        if updated_spec.endswith("```"):
            updated_spec = updated_spec[:-3]  # Remove trailing ```
    elif updated_spec.startswith("```"):
        updated_spec = updated_spec[3:]  # Remove ```
        if updated_spec.endswith("```"):
            updated_spec = updated_spec[:-3]  # Remove trailing ```

    updated_spec = updated_spec.strip()

    return {"updated_spec": updated_spec}


def save_specification(state: ClarifyState) -> dict:
    """Save the updated specification to file.

    Args:
        state: Current workflow state

    Returns:
        Empty dict (no state updates needed)
    """
    # Skip if there's an error
    if state.get("error"):
        return {}

    # Save updated specification
    spec_file = state["spec_path"] / "specification.md"
    save_markdown(state["updated_spec"], spec_file)

    return {}


def should_continue_after_load(state: ClarifyState) -> str:
    """Determine if workflow should continue after loading.

    Args:
        state: Current workflow state

    Returns:
        Next node name or END
    """
    if state.get("error"):
        return END
    return "analyze"


def should_continue_after_analyze(state: ClarifyState) -> str:
    """Determine if workflow should continue after analyzing.

    Args:
        state: Current workflow state

    Returns:
        Next node name or END
    """
    if state.get("error"):
        return END
    # If no questions generated, end workflow
    if not state.get("questions"):
        return END
    # If we have answers, proceed to update
    if state.get("answers"):
        return "update"
    # Otherwise end (CLI will handle question/answer loop)
    return END


def should_continue_after_update(state: ClarifyState) -> str:
    """Determine if workflow should continue after updating.

    Args:
        state: Current workflow state

    Returns:
        Next node name or END
    """
    if state.get("error"):
        return END
    return "save"


def build_clarify_workflow() -> StateGraph:
    """Build the clarify workflow graph.

    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(ClarifyState)

    # Add nodes
    workflow.add_node("load", load_specification)
    workflow.add_node("analyze", analyze_and_generate_questions)
    workflow.add_node("update", update_specification)
    workflow.add_node("save", save_specification)

    # Add edges
    workflow.add_edge(START, "load")
    workflow.add_conditional_edges(
        "load", should_continue_after_load, {"analyze": "analyze", END: END}
    )
    workflow.add_conditional_edges(
        "analyze",
        should_continue_after_analyze,
        {"update": "update", END: END},
    )
    workflow.add_conditional_edges(
        "update", should_continue_after_update, {"save": "save", END: END}
    )
    workflow.add_edge("save", END)

    return workflow.compile()


def run_clarify(answers: dict[int, str] | None = None) -> ClarifyState:
    """Run the clarify workflow.

    Args:
        answers: Optional dict mapping question IDs to user answers.
                If not provided, workflow will only generate questions.

    Returns:
        Final workflow state
    """
    workflow = build_clarify_workflow()

    initial_state: ClarifyState = {
        "spec_path": None,
        "specification": "",
        "questions": None,
        "answers": answers,
        "updated_spec": "",
        "error": None,
    }

    result = workflow.invoke(initial_state)
    return result
