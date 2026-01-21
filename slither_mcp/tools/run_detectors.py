"""Tool for running Slither detectors and retrieving cached results."""

from typing import Annotated

from pydantic import BaseModel, Field

from slither_mcp.pagination import PaginatedRequest, apply_pagination
from slither_mcp.types import (
    DetectorResult,
    ProjectFacts,
)


class RunDetectorsRequest(PaginatedRequest):
    """Request to run detectors and retrieve results."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    detector_names: list[str] | None = None
    impact: list[str] | None = None
    confidence: list[str] | None = None


class RunDetectorsResponse(BaseModel):
    """Response containing detector results."""

    success: bool
    results: list[DetectorResult]
    total_count: int
    has_more: Annotated[
        bool, Field(description="True if there are more results beyond this page")
    ] = False
    error_message: str | None = None


def run_detectors(
    request: RunDetectorsRequest, project_facts: ProjectFacts
) -> RunDetectorsResponse:
    """
    Retrieve cached detector results with optional filtering.

    Filters can be applied by detector name, impact level, and confidence level.
    All filters are case-insensitive.

    Args:
        request: The run detectors request with optional filters
        project_facts: The project facts containing cached detector results

    Returns:
        RunDetectorsResponse with filtered results or error
    """
    try:
        all_results = []

        # Collect results from all detectors or filtered detectors
        if request.detector_names:
            # Filter by specific detector names (case-insensitive)
            detector_names_lower = [name.lower() for name in request.detector_names]
            for detector_name, results in project_facts.detector_results.items():
                if detector_name.lower() in detector_names_lower:
                    all_results.extend(results)
        else:
            # Include all detector results
            for results in project_facts.detector_results.values():
                all_results.extend(results)

        # Apply impact filter if provided
        if request.impact:
            impact_lower = [i.lower() for i in request.impact]
            all_results = [r for r in all_results if r.impact.lower() in impact_lower]

        # Apply confidence filter if provided
        if request.confidence:
            confidence_lower = [c.lower() for c in request.confidence]
            all_results = [r for r in all_results if r.confidence.lower() in confidence_lower]

        # Apply pagination
        all_results, total_count, has_more = apply_pagination(
            all_results, request.offset, request.limit
        )

        return RunDetectorsResponse(
            success=True, results=all_results, total_count=total_count, has_more=has_more
        )
    except Exception as e:
        return RunDetectorsResponse(
            success=False, results=[], total_count=0, has_more=False, error_message=str(e)
        )
