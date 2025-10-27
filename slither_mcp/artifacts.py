"""Artifact management for project facts."""

import json
import os
import sys
from pathlib import Path

from slither_mcp.types import ProjectFacts


def save_project_facts(project_facts: ProjectFacts, artifacts_dir: str) -> None:
    """
    Save ProjectFacts to JSON file in artifacts directory.
    
    Args:
        project_facts: The ProjectFacts to save
        artifacts_dir: Directory to save artifacts in
    """
    # Ensure artifacts directory exists
    os.makedirs(artifacts_dir, exist_ok=True)
    
    # Create the serializable data structure with type metadata
    serializable_data = {
        "_pydantic_type": {
            "is_list": False,
            "model_name": "ProjectFacts"
        },
        "data": project_facts.model_dump(mode="json")
    }
    
    # Save to project_facts.json
    file_path = Path(artifacts_dir) / "project_facts.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(serializable_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved project facts to: {file_path}", file=sys.stderr)


def load_project_facts(artifacts_dir: str) -> ProjectFacts | None:
    """
    Load ProjectFacts from JSON file in artifacts directory.
    
    Args:
        artifacts_dir: Directory containing artifacts
        
    Returns:
        ProjectFacts if file exists and is valid, None otherwise
    """
    file_path = Path(artifacts_dir) / "project_facts.json"
    
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            artifact_data = json.load(f)
        
        # Handle data with type metadata
        if isinstance(artifact_data, dict) and "_pydantic_type" in artifact_data:
            data = artifact_data["data"]
            return ProjectFacts.model_validate(data)
        
        # Fallback: try to parse as direct ProjectFacts
        return ProjectFacts.model_validate(artifact_data)
        
    except Exception as e:
        print(f"Error loading project facts from {file_path}: {e}", file=sys.stderr)
        return None


def artifacts_exist(artifacts_dir: str) -> bool:
    """
    Check if project_facts.json exists in artifacts directory.
    
    Args:
        artifacts_dir: Directory to check for artifacts
        
    Returns:
        True if project_facts.json exists, False otherwise
    """
    file_path = Path(artifacts_dir) / "project_facts.json"
    return file_path.exists()

