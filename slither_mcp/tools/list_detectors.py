"""Tool for listing available Slither detectors."""

from typing import Annotated, Optional
from pydantic import BaseModel, Field

from slither_mcp.types import (
    DetectorMetadata,
    ProjectFacts,
    JSONStringTolerantModel,
)


class ListDetectorsRequest(JSONStringTolerantModel):
    """Request to list available Slither detectors."""
    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    name_filter: Optional[str] = None


class ListDetectorsResponse(BaseModel):
    """Response containing list of available detectors."""
    success: bool
    detectors: list[DetectorMetadata]
    total_count: int
    error_message: str | None = None


def list_detectors(
    request: ListDetectorsRequest,
    project_facts: ProjectFacts
) -> ListDetectorsResponse:
    """
    List all available Slither detectors with their metadata.
    
    Args:
        request: The list detectors request with optional name filter
        project_facts: The project facts containing detector metadata
        
    Returns:
        ListDetectorsResponse with detector list or error
    """
    try:
        detectors = project_facts.available_detectors
        
        # Apply name filter if provided
        if request.name_filter:
            filter_lower = request.name_filter.lower()
            detectors = [
                d for d in detectors
                if filter_lower in d.name.lower() or filter_lower in d.description.lower()
            ]
        
        return ListDetectorsResponse(
            success=True,
            detectors=detectors,
            total_count=len(detectors)
        )
    except Exception as e:
        return ListDetectorsResponse(
            success=False,
            detectors=[],
            total_count=0,
            error_message=str(e)
        )

