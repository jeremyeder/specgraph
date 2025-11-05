"""File management utilities for creating and organizing specifications."""

import re
from pathlib import Path
from typing import Tuple


def get_next_spec_number(specs_dir: Path = Path("specs")) -> int:
    """Get the next available specification number.

    Args:
        specs_dir: Directory containing specifications

    Returns:
        Next available spec number (e.g., 1, 2, 3...)
    """
    if not specs_dir.exists():
        return 1

    existing_specs = [d for d in specs_dir.iterdir() if d.is_dir()]
    if not existing_specs:
        return 1

    # Extract numbers from directory names like "001-feature-name"
    numbers = []
    for spec_dir in existing_specs:
        match = re.match(r"^(\d+)-", spec_dir.name)
        if match:
            numbers.append(int(match.group(1)))

    return max(numbers) + 1 if numbers else 1


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug.

    Args:
        text: Text to convert

    Returns:
        Slugified text (e.g., "My Feature" -> "my-feature")
    """
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and underscores with hyphens
    text = re.sub(r"[\s_]+", "-", text)
    # Remove non-alphanumeric characters except hyphens
    text = re.sub(r"[^a-z0-9-]", "", text)
    # Remove multiple consecutive hyphens
    text = re.sub(r"-+", "-", text)
    # Strip leading/trailing hyphens
    text = text.strip("-")
    # Limit length
    return text[:50]


def create_spec_directory(
    feature_name: str, specs_dir: Path = Path("specs")
) -> Tuple[Path, int]:
    """Create a new specification directory.

    Args:
        feature_name: Name of the feature
        specs_dir: Base specifications directory

    Returns:
        Tuple of (spec_directory_path, spec_number)
    """
    specs_dir.mkdir(parents=True, exist_ok=True)

    spec_number = get_next_spec_number(specs_dir)
    slug = slugify(feature_name)
    dir_name = f"{spec_number:03d}-{slug}"

    spec_path = specs_dir / dir_name
    spec_path.mkdir(parents=True, exist_ok=True)

    return spec_path, spec_number


def save_markdown(content: str, file_path: Path) -> None:
    """Save markdown content to a file.

    Args:
        content: Markdown content to save
        file_path: Path where file should be saved
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def find_latest_spec(specs_dir: Path = Path("specs")) -> Path | None:
    """Find the most recently created specification directory.

    Args:
        specs_dir: Directory containing specifications

    Returns:
        Path to latest spec directory, or None if no specs exist
    """
    if not specs_dir.exists():
        return None

    existing_specs = [d for d in specs_dir.iterdir() if d.is_dir()]
    if not existing_specs:
        return None

    # Sort by spec number (extracted from directory name)
    def get_spec_number(spec_dir: Path) -> int:
        match = re.match(r"^(\d+)-", spec_dir.name)
        return int(match.group(1)) if match else 0

    return max(existing_specs, key=get_spec_number)
