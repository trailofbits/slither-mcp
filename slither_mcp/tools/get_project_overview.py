"""Tool for getting an aggregate overview of a Solidity project."""

from typing import Annotated

from pydantic import BaseModel, Field

from slither_mcp.types import JSONStringTolerantModel, ProjectFacts


class ContractCounts(BaseModel):
    """Contract counts by type."""

    total: Annotated[int, Field(description="Total number of contracts")]
    concrete: Annotated[
        int, Field(description="Non-abstract, non-interface, non-library contracts")
    ]
    abstract: Annotated[int, Field(description="Abstract contracts")]
    interface: Annotated[int, Field(description="Interfaces")]
    library: Annotated[int, Field(description="Libraries")]


class FunctionCounts(BaseModel):
    """Function counts."""

    total_declared: Annotated[
        int, Field(description="Total functions declared across all contracts")
    ]
    total_inherited: Annotated[
        int, Field(description="Total inherited functions across all contracts")
    ]


class VisibilityDistribution(BaseModel):
    """Function visibility distribution."""

    public: int = 0
    external: int = 0
    internal: int = 0
    private: int = 0


class ComplexityDistribution(BaseModel):
    """Function complexity distribution by lines of code."""

    small: Annotated[int, Field(description="Functions with 1-10 lines")]
    medium: Annotated[int, Field(description="Functions with 11-30 lines")]
    large: Annotated[int, Field(description="Functions with 31-100 lines")]
    very_large: Annotated[int, Field(description="Functions with >100 lines")]


class DetectorFindingsByImpact(BaseModel):
    """Detector findings grouped by impact level."""

    high: int = 0
    medium: int = 0
    low: int = 0
    informational: int = 0


class TopDetector(BaseModel):
    """A detector with high finding count."""

    name: str
    finding_count: int
    impact: str


class ProjectOverview(BaseModel):
    """Aggregate statistics about a Solidity project."""

    contract_counts: ContractCounts
    function_counts: FunctionCounts
    visibility_distribution: VisibilityDistribution
    complexity_distribution: ComplexityDistribution
    detector_findings_by_impact: DetectorFindingsByImpact
    top_detectors: Annotated[
        list[TopDetector], Field(description="Top 5 detectors by finding count")
    ]


class GetProjectOverviewRequest(JSONStringTolerantModel):
    """Request to get project overview statistics."""

    path: Annotated[str, Field(description="Path to the Solidity project directory")]


class GetProjectOverviewResponse(BaseModel):
    """Response containing project overview."""

    success: bool
    overview: ProjectOverview | None = None
    error_message: str | None = None


def get_project_overview(
    request: GetProjectOverviewRequest, project_facts: ProjectFacts
) -> GetProjectOverviewResponse:
    """
    Get aggregate statistics about a Solidity project.

    Returns counts for contracts, functions, visibility distribution,
    complexity distribution, and detector findings.

    Args:
        request: The request with project path
        project_facts: The project facts containing all extracted data

    Returns:
        GetProjectOverviewResponse with overview statistics
    """
    try:
        # Contract counts
        total_contracts = len(project_facts.contracts)
        concrete = 0
        abstract = 0
        interface = 0
        library = 0

        for contract in project_facts.contracts.values():
            if contract.is_library:
                library += 1
            elif contract.is_interface:
                interface += 1
            elif contract.is_abstract:
                abstract += 1
            else:
                concrete += 1

        contract_counts = ContractCounts(
            total=total_contracts,
            concrete=concrete,
            abstract=abstract,
            interface=interface,
            library=library,
        )

        # Function counts and visibility/complexity distribution
        total_declared = 0
        total_inherited = 0
        visibility = VisibilityDistribution()
        complexity = ComplexityDistribution(small=0, medium=0, large=0, very_large=0)

        for contract in project_facts.contracts.values():
            total_declared += len(contract.functions_declared)
            total_inherited += len(contract.functions_inherited)

            # Process declared functions for visibility and complexity
            for func in contract.functions_declared.values():
                # Visibility
                vis = func.visibility.lower()
                if vis == "public":
                    visibility.public += 1
                elif vis == "external":
                    visibility.external += 1
                elif vis == "internal":
                    visibility.internal += 1
                elif vis == "private":
                    visibility.private += 1

                # Complexity by lines of code
                lines = func.line_end - func.line_start + 1
                if lines <= 10:
                    complexity.small += 1
                elif lines <= 30:
                    complexity.medium += 1
                elif lines <= 100:
                    complexity.large += 1
                else:
                    complexity.very_large += 1

        function_counts = FunctionCounts(
            total_declared=total_declared,
            total_inherited=total_inherited,
        )

        # Detector findings by impact
        findings_by_impact = DetectorFindingsByImpact()
        detector_counts: dict[str, tuple[int, str]] = {}  # name -> (count, impact)

        for detector_name, results in project_facts.detector_results.items():
            count = len(results)
            if count > 0:
                impact = results[0].impact.lower() if results else "informational"
                detector_counts[detector_name] = (count, impact)

                for result in results:
                    impact_level = result.impact.lower()
                    if impact_level == "high":
                        findings_by_impact.high += 1
                    elif impact_level == "medium":
                        findings_by_impact.medium += 1
                    elif impact_level == "low":
                        findings_by_impact.low += 1
                    else:
                        findings_by_impact.informational += 1

        # Top 5 detectors by finding count
        sorted_detectors = sorted(detector_counts.items(), key=lambda x: x[1][0], reverse=True)[:5]
        top_detectors = [
            TopDetector(name=name, finding_count=count, impact=impact)
            for name, (count, impact) in sorted_detectors
        ]

        overview = ProjectOverview(
            contract_counts=contract_counts,
            function_counts=function_counts,
            visibility_distribution=visibility,
            complexity_distribution=complexity,
            detector_findings_by_impact=findings_by_impact,
            top_detectors=top_detectors,
        )

        return GetProjectOverviewResponse(success=True, overview=overview)

    except Exception as e:
        return GetProjectOverviewResponse(
            success=False, error_message=f"Failed to generate project overview: {e}"
        )
