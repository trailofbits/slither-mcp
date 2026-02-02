"""Project facts generation from Slither analysis."""

import inspect
import sys

from slither.detectors import all_detectors as slither_detectors
from slither.detectors.abstract_detector import AbstractDetector

from slither_mcp.callees import get_callees
from slither_mcp.types import (
    ContractKey,
    ContractModel,
    DetectorMetadata,
    DetectorResult,
    EventModel,
    EventParameter,
    FuncSig,
    FunctionModel,
    ProjectFacts,
    SourceLocation,
    StateVariableModel,
    get_contract_key,
    get_func_sig,
)


def populate_function_facts(function) -> FunctionModel:
    """
    Extract function facts from a Slither FunctionContract.

    Args:
        function: Slither FunctionContract object

    Returns:
        FunctionModel with all function metadata
    """
    modifiers = []
    if function.is_virtual:
        modifiers.append("virtual")
    if function.is_fallback:
        modifiers.append("fallback")
    if function.is_override:
        modifiers.append("override")
    if function.view:
        modifiers.append("view")
    if function.pure:
        modifiers.append("pure")
    if function.payable:
        modifiers.append("payable")

    callees = get_callees(function)

    return FunctionModel(
        signature=get_func_sig(function),
        solidity_modifiers=modifiers,
        visibility=function.visibility,
        function_modifiers=[modifier.canonical_name for modifier in function.modifiers],
        returns=function.signature[-1],
        arguments=function.signature[1],
        line_start=function.source_mapping.lines[0],
        line_end=function.source_mapping.lines[-1],
        path=function.source_mapping.filename.short,
        callees=callees,
        implementation_contract=ContractKey(
            contract_name=function.canonical_name.split(".")[0],
            path=function.source_mapping.filename.short,
        ),
    )


def get_modeled_functions(function_contracts: list) -> dict[FuncSig, FunctionModel]:
    """
    Convert a list of Slither FunctionContracts to FunctionModels.

    Args:
        function_contracts: List of Slither FunctionContract objects

    Returns:
        Dictionary mapping function signatures to FunctionModels
    """
    models = {}
    for function in function_contracts:
        model = populate_function_facts(function)
        models[model.signature] = model
    return models


def extract_state_variables(contract) -> list[StateVariableModel]:
    """
    Extract state variables from a Slither contract.

    Args:
        contract: Slither Contract object

    Returns:
        List of StateVariableModel objects
    """
    state_vars = []
    for var in contract.state_variables_declared:
        try:
            line_number = None
            if hasattr(var, "source_mapping") and var.source_mapping:
                if hasattr(var.source_mapping, "lines") and var.source_mapping.lines:
                    line_number = var.source_mapping.lines[0]

            state_vars.append(
                StateVariableModel(
                    name=var.name,
                    type_str=str(var.type),
                    visibility=var.visibility,
                    is_constant=var.is_constant,
                    is_immutable=var.is_immutable,
                    line_number=line_number,
                )
            )
        except Exception as e:
            print(f"Warning: Could not extract state variable {var.name}: {e}", file=sys.stderr)
            continue
    return state_vars


def extract_events(contract) -> list[EventModel]:
    """
    Extract events from a Slither contract.

    Args:
        contract: Slither Contract object

    Returns:
        List of EventModel objects
    """
    events = []
    for event in contract.events_declared:
        try:
            line_number = None
            if hasattr(event, "source_mapping") and event.source_mapping:
                if hasattr(event.source_mapping, "lines") and event.source_mapping.lines:
                    line_number = event.source_mapping.lines[0]

            parameters = []
            # Slither events have elems attribute with the parameters
            if hasattr(event, "elems"):
                for param in event.elems:
                    parameters.append(
                        EventParameter(
                            name=param.name or "",
                            type_str=str(param.type),
                            indexed=param.indexed if hasattr(param, "indexed") else False,
                        )
                    )

            events.append(
                EventModel(
                    name=event.name,
                    parameters=parameters,
                    line_number=line_number,
                )
            )
        except Exception as e:
            print(f"Warning: Could not extract event {event.name}: {e}", file=sys.stderr)
            continue
    return events


def populate_contract_facts(contracts: list) -> dict[ContractKey, ContractModel]:
    """
    Extract contract facts from Slither contracts.

    Args:
        contracts: List of Slither Contract objects

    Returns:
        Dictionary mapping ContractKeys to ContractModels
    """
    ret = {}
    for contract in contracts:
        contract_key = get_contract_key(contract)
        funcsDeclared = get_modeled_functions(contract.functions_and_modifiers_declared)
        funcsInherited = get_modeled_functions(contract.functions_and_modifiers_inherited)

        # Populate contract scopes
        contract_scopes = []
        for _, scope in contract.file_scope.contracts.items():
            contract_scopes.append(get_contract_key(scope))
        # add self just in case
        contract_scopes.append(contract_key)

        # Extract state variables and events
        state_vars = extract_state_variables(contract)
        events = extract_events(contract)

        ret[get_contract_key(contract)] = ContractModel(
            name=contract.name,
            key=contract_key,
            path=contract.file_scope.filename.short,
            is_abstract=contract.is_abstract,
            is_fully_implemented=contract.is_fully_implemented,
            is_interface=contract.is_interface,
            is_library=contract.is_library,
            directly_inherits=[get_contract_key(c) for c in contract.immediate_inheritance],
            scopes=contract_scopes,
            functions_declared=funcsDeclared,
            functions_inherited=funcsInherited,
            state_variables=state_vars,
            events=events,
        )
    return ret


def get_detector_metadata(slither) -> list[DetectorMetadata]:
    """
    Extract metadata for all available detectors.

    Args:
        slither: Slither or LazySlither object (not used, but kept for consistency)

    Returns:
        List of DetectorMetadata for all available detectors
    """
    metadata_list = []

    # Get all detector classes from the slither.detectors.all_detectors module
    for name in dir(slither_detectors):
        # Skip private attributes and non-detector classes
        if name.startswith("_"):
            continue

        detector_class = getattr(slither_detectors, name)

        # Check if it's a class and a subclass of AbstractDetector
        if not (
            inspect.isclass(detector_class)
            and issubclass(detector_class, AbstractDetector)
            and detector_class is not AbstractDetector
        ):
            continue

        try:
            # Extract detector metadata
            metadata = DetectorMetadata(
                name=detector_class.ARGUMENT,
                description=detector_class.HELP,
                impact=detector_class.IMPACT.name.capitalize(),
                confidence=detector_class.CONFIDENCE.name.capitalize(),
            )
            metadata_list.append(metadata)
        except Exception as e:
            print(f"Warning: Could not extract metadata for detector {name}: {e}", file=sys.stderr)
            continue

    return metadata_list


def extract_source_locations(element) -> list[SourceLocation]:
    """
    Extract source locations from a Slither element.

    Args:
        element: A Slither element (could be various types with source_mapping)

    Returns:
        List of SourceLocation objects
    """
    locations = []

    try:
        if hasattr(element, "source_mapping") and element.source_mapping:
            source_mapping = element.source_mapping
            if hasattr(source_mapping, "lines") and source_mapping.lines:
                locations.append(
                    SourceLocation(
                        file_path=str(source_mapping.filename.short),
                        start_line=source_mapping.lines[0],
                        end_line=source_mapping.lines[-1],
                    )
                )
    except Exception as e:
        print(f"Warning: Could not extract source location: {e}", file=sys.stderr)

    return locations


def process_detector_results(slither) -> dict[str, list[DetectorResult]]:
    """
    Run all Slither detectors and process the results.

    Args:
        slither: Slither or LazySlither object

    Returns:
        Dictionary mapping detector names to their results
    """
    results_by_detector = {}

    try:
        # First, register all detectors
        print("Registering Slither detectors...", file=sys.stderr)
        detector_count = 0
        for name in dir(slither_detectors):
            if name.startswith("_"):
                continue
            detector_class = getattr(slither_detectors, name)
            if (
                inspect.isclass(detector_class)
                and issubclass(detector_class, AbstractDetector)
                and detector_class is not AbstractDetector
            ):
                slither.register_detector(detector_class)
                detector_count += 1

        print(f"Registered {detector_count} detectors", file=sys.stderr)

        # Run all detectors
        print("Running Slither detectors...", file=sys.stderr)
        detector_results = slither.run_detectors()
        print(f"Detectors completed, got {len(detector_results)} result sets", file=sys.stderr)

        # Process results - detector_results is a list of lists
        # Each element is a list of findings from one detector
        findings_count = 0
        for detector_findings in detector_results:
            # Skip empty results
            if not detector_findings:
                continue

            # detector_findings is a list of finding dictionaries
            for finding in detector_findings:
                if not finding or not isinstance(finding, dict):
                    continue

                try:
                    # Extract detector information
                    detector_name = finding.get("check", "unknown")
                    impact = finding.get("impact", "Unknown")
                    confidence = finding.get("confidence", "Unknown")
                    description = finding.get("description", "")

                    # Extract source locations from elements
                    source_locations = []
                    elements = finding.get("elements", [])

                    for element in elements:
                        if isinstance(element, dict):
                            # Handle dictionary elements (common in detector output)
                            source_map = element.get("source_mapping", {})
                            if source_map:
                                lines = source_map.get("lines", [])
                                filename = source_map.get(
                                    "filename_short", source_map.get("filename_relative", "")
                                )
                                if lines and filename:
                                    source_locations.append(
                                        SourceLocation(
                                            file_path=filename,
                                            start_line=lines[0],
                                            end_line=lines[-1],
                                        )
                                    )

                    # Create detector result
                    detector_result = DetectorResult(
                        detector_name=detector_name,
                        check=detector_name,
                        impact=impact,
                        confidence=confidence,
                        description=description,
                        source_locations=source_locations,
                    )

                    # Add to results dictionary
                    if detector_name not in results_by_detector:
                        results_by_detector[detector_name] = []
                    results_by_detector[detector_name].append(detector_result)
                    findings_count += 1

                except Exception as e:
                    print(f"Warning: Error processing detector finding: {e}", file=sys.stderr)
                    continue

        print(
            f"Processed {findings_count} findings from {len(results_by_detector)} detectors with results",
            file=sys.stderr,
        )

    except Exception as e:
        print(f"Warning: Error running detectors: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)

    return results_by_detector


def get_project_facts(project_dir: str, slither) -> ProjectFacts:
    """
    Generate ProjectFacts from a Slither analysis.

    Args:
        project_dir: Path to the project directory
        slither: Slither or LazySlither object

    Returns:
        ProjectFacts containing all contract and function metadata
    """
    contracts = populate_contract_facts(slither.contracts)

    # Extract detector metadata
    print("Extracting detector metadata...", file=sys.stderr)
    available_detectors = get_detector_metadata(slither)
    print(f"Found {len(available_detectors)} available detectors", file=sys.stderr)

    # Run detectors and collect results
    detector_results = process_detector_results(slither)

    return ProjectFacts(
        contracts=contracts,
        project_dir=project_dir,
        detector_results=detector_results,
        available_detectors=available_detectors,
    )
