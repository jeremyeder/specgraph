"""Prompt templates for the plan workflow."""

PLAN_SYSTEM_PROMPT = """You are a technical architect following the Spec-Driven Development methodology.

Your role is to create detailed technical implementation plans that translate high-level product specifications into concrete technical choices, architecture, and design artifacts.

Focus on:
- Technical architecture and design decisions
- Technology stack selection with rationale
- Data models and schemas
- API contracts and interfaces
- Implementation guidelines
- Traceability from technical choices back to requirements

Be specific and actionable. Every architectural choice should have clear reasoning."""

PLAN_USER_PROMPT = """Based on the following product specification, create a comprehensive technical plan:

## Product Specification
{specification}

## Technical Constraints/Preferences
{technical_constraints}

Generate a detailed technical plan that includes:

## Technology Stack
What technologies, frameworks, and libraries will be used? Include rationale for each choice.

## Architecture Overview
High-level system architecture and component design.

## Data Model
Key entities, their attributes, relationships, and validation rules.

## API Design
Core interfaces, endpoints, or contracts (if applicable).

## Implementation Approach
How should this be built? What's the recommended build sequence?

## Technical Risks & Mitigations
What technical challenges might arise and how to address them?

Write in clear, professional markdown. Be specific and actionable."""


def get_plan_prompt(specification: str, technical_constraints: str) -> str:
    """Get the formatted plan prompt.

    Args:
        specification: The product specification from the specify phase
        technical_constraints: Technical preferences or constraints

    Returns:
        Formatted prompt for the LLM
    """
    return PLAN_USER_PROMPT.format(
        specification=specification, technical_constraints=technical_constraints
    )
