"""Prompt templates for the specify workflow."""

SPECIFY_SYSTEM_PROMPT = """You are a product specification expert following the Spec-Driven Development methodology.

Your role is to transform vague feature ideas into comprehensive Product Requirements Documents (PRDs) that define WHAT to build and WHY, without focusing on technical implementation details.

Focus on:
- User experience and user journeys
- Functional requirements
- Success criteria
- Edge cases and clarifications
- The "what" and "why" (NOT the "how")

Do NOT include:
- Technical stack decisions
- Implementation details
- Specific technologies or frameworks
- Architecture designs
"""

SPECIFY_USER_PROMPT = """Create a comprehensive product specification for the following feature:

{feature_description}

Generate a well-structured PRD that includes:

## Overview
Brief description of the feature and its purpose

## User Stories
Who will use this and what will they do?

## Functional Requirements
What must this feature do? Be specific.

## Success Criteria
How will we know this feature is successful?

## Edge Cases
What special cases or exceptions should we consider?

## Open Questions
What needs to be clarified before implementation?

Write in clear, professional markdown. Be thorough but concise."""


def get_specify_prompt(feature_description: str) -> str:
    """Get the formatted specify prompt.

    Args:
        feature_description: Description of the feature to specify

    Returns:
        Formatted prompt for the LLM
    """
    return SPECIFY_USER_PROMPT.format(feature_description=feature_description)
