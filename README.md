# Specgraph

A minimal implementation of GitHub's [spec-kit](https://github.com/github/spec-kit) `/specify` and `/plan` phases using LangGraph workflows and Anthropic Claude.

## Overview

Specgraph implements specification-driven development workflows:

- **`acpctl specify`** - Transform feature ideas into comprehensive Product Requirements Documents (PRDs)
- **`acpctl plan`** - Generate technical implementation plans from specifications

## Installation

1. Create a virtual environment and install dependencies:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

2. Set up your Anthropic API key:

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

## Usage

### Generate a Specification

```bash
acpctl specify "Build a photo album organizer with drag-and-drop functionality"
```

This creates a directory structure like:
```
specs/001-build-photo-album-organizer/
└── specification.md
```

### Generate a Technical Plan

```bash
acpctl plan "Use Python with FastAPI, PostgreSQL database, and React frontend"
```

This adds to the specification directory:
```
specs/001-build-photo-album-organizer/
├── specification.md
└── plan.md
```

## Project Structure

```
specgraph/
├── src/specgraph/
│   ├── workflows/      # LangGraph workflow definitions
│   ├── prompts/        # Claude prompt templates
│   ├── utils/          # File management utilities
│   └── cli.py          # Click CLI interface
└── specs/              # Generated specifications (gitignored)
```

## Workflows

### Specify Workflow

**Graph**: `analyze_input` → `generate_specification` → `save_specification` → END

1. Validates feature description
2. Calls Claude to generate PRD with user stories, requirements, success criteria
3. Saves to `specs/NNN-feature-name/specification.md`

### Plan Workflow

**Graph**: `load_specification` → `generate_plan` → `save_plan` → END

1. Loads the latest specification
2. Calls Claude to generate technical plan with architecture, tech stack, data model
3. Saves to `specs/NNN-feature-name/plan.md`

## Development

Run linters before committing:

```bash
black src/
isort src/
```

## License

MIT
