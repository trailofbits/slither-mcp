"""Artifact management for project facts."""

import json
import os
import sys
from pathlib import Path

from slither_mcp.types import (
    CACHE_SCHEMA_VERSION,
    CacheCorruptionError,
    ProjectFacts,
    compute_content_checksum,
)


def save_project_facts(project_facts: ProjectFacts, artifacts_dir: str) -> None:
    """
    Save ProjectFacts to JSON file in artifacts directory.

    The cache file includes:
    - Schema version for compatibility checking
    - Checksum for integrity validation
    - Type metadata for deserialization

    Args:
        project_facts: The ProjectFacts to save
        artifacts_dir: Directory to save artifacts in
    """
    # Ensure artifacts directory exists
    os.makedirs(artifacts_dir, exist_ok=True)

    # Serialize the data
    data_json = project_facts.model_dump(mode="json")
    data_str = json.dumps(data_json, sort_keys=True)
    checksum = compute_content_checksum(data_str)

    # Create the serializable data structure with type metadata, version, and checksum
    serializable_data = {
        "_pydantic_type": {"is_list": False, "model_name": "ProjectFacts"},
        "_cache_version": CACHE_SCHEMA_VERSION,
        "_checksum": checksum,
        "data": data_json,
    }

    # Save to project_facts.json
    file_path = Path(artifacts_dir) / "project_facts.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(serializable_data, f, indent=2, ensure_ascii=False)

    print(f"Saved project facts to: {file_path}", file=sys.stderr)


def _normalize_paths(project_facts: ProjectFacts) -> ProjectFacts:
    """
    Convert any absolute paths to relative paths for portability.

    Legacy cached facts may contain absolute paths in ContractModel.path.
    This function normalizes them to relative paths based on project_dir.

    Args:
        project_facts: The ProjectFacts to normalize

    Returns:
        The same ProjectFacts with normalized paths (mutated in place)
    """
    project_dir = project_facts.project_dir

    for contract_model in project_facts.contracts.values():
        path = contract_model.path
        # If path is absolute and starts with project_dir, make it relative
        if os.path.isabs(path):
            try:
                contract_model.path = os.path.relpath(path, project_dir)
            except ValueError:
                # On Windows, relpath fails if paths are on different drives
                # Fall back to keeping the original path
                pass

    return project_facts


def load_project_facts(artifacts_dir: str) -> ProjectFacts:
    """
    Load ProjectFacts from JSON file in artifacts directory.

    Args:
        artifacts_dir: Directory containing artifacts

    Returns:
        ProjectFacts if file exists and is valid

    Raises:
        FileNotFoundError: If cache file doesn't exist
        CacheCorruptionError: If cache is corrupted, invalid, or version mismatch
    """
    file_path = Path(artifacts_dir) / "project_facts.json"

    if not file_path.exists():
        raise FileNotFoundError(f"Cache file not found: {file_path}")

    try:
        with open(file_path, encoding="utf-8") as f:
            artifact_data = json.load(f)
    except json.JSONDecodeError as e:
        raise CacheCorruptionError(f"Cache file is not valid JSON: {e}") from e

    if not isinstance(artifact_data, dict):
        raise CacheCorruptionError("Cache file has invalid structure: expected dict")

    # Handle data with type metadata and version
    if "_pydantic_type" in artifact_data:
        # Check version compatibility
        cache_version = artifact_data.get("_cache_version")
        if cache_version != CACHE_SCHEMA_VERSION:
            raise CacheCorruptionError(
                f"Cache version mismatch: found '{cache_version}', expected '{CACHE_SCHEMA_VERSION}'. "
                f"Re-run analysis to regenerate cache."
            )

        # Validate checksum if present
        stored_checksum = artifact_data.get("_checksum")
        data = artifact_data.get("data")

        if data is None:
            raise CacheCorruptionError("Cache file missing 'data' field")

        if stored_checksum is not None:
            data_str = json.dumps(data, sort_keys=True)
            computed_checksum = compute_content_checksum(data_str)
            if computed_checksum != stored_checksum:
                raise CacheCorruptionError(
                    "Cache integrity check failed: checksum mismatch. "
                    "The cache file may have been corrupted. Re-run analysis to regenerate."
                )

        try:
            project_facts = ProjectFacts.model_validate(data)
            # Normalize any absolute paths for backward compatibility
            return _normalize_paths(project_facts)
        except Exception as e:
            raise CacheCorruptionError(f"Failed to parse cache data: {e}") from e

    # Fallback for legacy cache files without version/checksum
    # These are not trusted - require re-analysis
    raise CacheCorruptionError(
        "Legacy cache format detected without version info. Re-run analysis to regenerate cache."
    )


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
