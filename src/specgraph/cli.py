"""CLI interface for specgraph using Click."""

import os
import sys

import click

from specgraph.workflows.clarify import run_clarify
from specgraph.workflows.plan import run_plan
from specgraph.workflows.specify import run_specify
from specgraph.workflows.tasks import run_tasks


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Specgraph - Spec-Kit workflows using LangGraph.

    A minimal implementation of spec-kit's specify and plan phases.
    """
    # Check for Anthropic API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        click.echo(
            click.style(
                "Error: ANTHROPIC_API_KEY environment variable not set", fg="red"
            ),
            err=True,
        )
        click.echo("Set it with: export ANTHROPIC_API_KEY='your-api-key'", err=True)
        sys.exit(1)


@cli.command()
@click.argument("feature_description")
def specify(feature_description: str):
    """Generate a product specification for a feature.

    FEATURE_DESCRIPTION: A description of the feature you want to build.

    Example:
        acpctl specify "Build a photo album organizer with drag-and-drop"
    """
    click.echo(click.style("🔍 Generating specification...", fg="blue"))

    try:
        result = run_specify(feature_description)

        if result.get("error"):
            click.echo(click.style(f"❌ Error: {result['error']}", fg="red"), err=True)
            sys.exit(1)

        click.echo(click.style("✅ Specification generated!", fg="green"))
        click.echo(f"\nSpec Number: {result['spec_number']:03d}")
        click.echo(f"Location: {result['spec_path']}/specification.md")
        click.echo("\nNext step: acpctl plan '<technical constraints>'")

    except Exception as e:
        click.echo(click.style(f"❌ Error: {str(e)}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.argument("technical_constraints", required=False, default="")
def plan(technical_constraints: str):
    """Generate a technical plan from the latest specification.

    TECHNICAL_CONSTRAINTS: Optional technical preferences or constraints.

    Example:
        acpctl plan "Use Python with FastAPI, PostgreSQL database"
    """
    click.echo(click.style("🏗️  Generating technical plan...", fg="blue"))

    try:
        result = run_plan(technical_constraints)

        if result.get("error"):
            click.echo(click.style(f"❌ Error: {result['error']}", fg="red"), err=True)
            sys.exit(1)

        click.echo(click.style("✅ Technical plan generated!", fg="green"))
        click.echo(f"Location: {result['plan_file']}")

    except Exception as e:
        click.echo(click.style(f"❌ Error: {str(e)}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
def tasks():
    """Generate task breakdown from the latest specification and plan.

    Generates a detailed task list following GitHub's Spec-Kit conventions,
    organized into phases with specific file paths and parallel markers.

    Example:
        acpctl tasks
    """
    click.echo(click.style("📋 Generating task breakdown...", fg="blue"))

    try:
        result = run_tasks()

        if result.get("error"):
            click.echo(click.style(f"❌ Error: {result['error']}", fg="red"), err=True)
            sys.exit(1)

        click.echo(click.style("✅ Task breakdown generated!", fg="green"))
        click.echo(f"Location: {result['tasks_file']}")

    except Exception as e:
        click.echo(click.style(f"❌ Error: {str(e)}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
def clarify():
    """Clarify ambiguities in the latest specification.

    Analyzes the specification for unclear or underspecified areas,
    asks clarifying questions, and updates the spec with answers.

    Example:
        acpctl clarify
    """
    click.echo(click.style("🔍 Analyzing specification for ambiguities...", fg="blue"))

    try:
        # First run: generate questions
        result = run_clarify()

        if result.get("error"):
            click.echo(click.style(f"❌ Error: {result['error']}", fg="red"), err=True)
            sys.exit(1)

        questions = result.get("questions", [])

        if not questions:
            click.echo(
                click.style(
                    "✅ No clarifications needed - specification is clear!", fg="green"
                )
            )
            return

        # Display and collect answers for each question
        click.echo(
            click.style(
                f"\n📝 Found {len(questions)} area(s) that need clarification:\n",
                fg="yellow",
            )
        )

        answers = {}
        for question in questions:
            click.echo(click.style(f"\n[{question['category']}]", fg="cyan"))
            click.echo(f"Q{question['id']}: {question['question']}")
            click.echo(click.style(f"Context: {question['context']}", fg="dim"))
            click.echo(
                click.style(
                    f"Suggested: {question['suggested_answer']}", fg="dim", italic=True
                )
            )

            # Get user's answer (or use suggested answer if user presses enter)
            answer = click.prompt(
                click.style("\nYour answer (press Enter for suggested)", fg="green"),
                default=question["suggested_answer"],
                show_default=False,
            )

            answers[question["id"]] = answer

        # Second run: update specification with answers
        click.echo(
            click.style("\n📝 Updating specification with clarifications...", fg="blue")
        )

        result = run_clarify(answers)

        if result.get("error"):
            click.echo(click.style(f"❌ Error: {result['error']}", fg="red"), err=True)
            sys.exit(1)

        click.echo(
            click.style("✅ Specification updated with clarifications!", fg="green")
        )
        click.echo(f"Location: {result['spec_path']}/specification.md")

    except Exception as e:
        click.echo(click.style(f"❌ Error: {str(e)}", fg="red"), err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
