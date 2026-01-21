"""Tool for analyzing events in a project."""

from typing import Annotated

from pydantic import BaseModel, Field

from slither_mcp.pagination import PaginatedRequest, apply_pagination
from slither_mcp.types import (
    ContractKey,
    EventModel,
    ProjectFacts,
)


class EventInfo(BaseModel):
    """Information about an event with contract context."""

    contract_key: Annotated[ContractKey, Field(description="Contract containing this event")]
    event: Annotated[EventModel, Field(description="Event details")]
    indexed_param_count: Annotated[int, Field(description="Number of indexed parameters")]


class AnalyzeEventsRequest(PaginatedRequest):
    """Request to analyze events in a project."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]
    contract_key: Annotated[
        ContractKey | None,
        Field(description="Optional, limit to specific contract"),
    ] = None
    name_filter: Annotated[
        str | None,
        Field(description="Optional, filter by event name (case-insensitive substring)"),
    ] = None


class AnalyzeEventsResponse(BaseModel):
    """Response containing event analysis."""

    success: bool
    events: Annotated[
        list[EventInfo],
        Field(description="List of events with their context"),
    ] = []
    total_count: Annotated[int, Field(description="Total number of events found")] = 0
    has_more: Annotated[
        bool, Field(description="True if there are more results beyond this page")
    ] = False
    summary: Annotated[
        dict[str, int],
        Field(description="Summary: events per contract"),
    ] = {}
    error_message: str | None = None


def analyze_events(
    request: AnalyzeEventsRequest, project_facts: ProjectFacts
) -> AnalyzeEventsResponse:
    """
    Analyze events across the project.

    Args:
        request: The analyze events request
        project_facts: The project facts containing contract data

    Returns:
        AnalyzeEventsResponse with event information
    """
    events: list[EventInfo] = []
    contract_event_counts: dict[str, int] = {}

    for contract_key, contract in project_facts.contracts.items():
        # Skip if filtering by contract and this isn't the target
        if request.contract_key and contract_key != request.contract_key:
            continue

        for event in contract.events:
            # Apply name filter if specified
            if request.name_filter:
                if request.name_filter.lower() not in event.name.lower():
                    continue

            indexed_count = sum(1 for p in event.parameters if p.indexed)

            info = EventInfo(
                contract_key=contract_key,
                event=event,
                indexed_param_count=indexed_count,
            )
            events.append(info)

            # Track counts per contract
            contract_name = contract_key.contract_name
            contract_event_counts[contract_name] = contract_event_counts.get(contract_name, 0) + 1

    # Sort by contract name, then by event name
    events.sort(key=lambda x: (x.contract_key.contract_name, x.event.name))

    # Apply pagination
    events_page, total_count, has_more = apply_pagination(events, request.offset, request.limit)

    return AnalyzeEventsResponse(
        success=True,
        events=events_page,
        total_count=total_count,
        has_more=has_more,
        summary=contract_event_counts,
    )
