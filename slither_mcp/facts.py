"""Project facts generation from Slither analysis."""

import sys

from slither_mcp.callees import get_callees
from slither_mcp.types import (
    ContractKey,
    ContractModel,
    DetectorMetadata,
    DetectorResult,
    FuncSig,
    FunctionModel,
    ProjectFacts,
    SourceLocation,
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
        funcsInherited = get_modeled_functions(
            contract.functions_and_modifiers_inherited
        )

        # Populate contract scopes
        contract_scopes = []
        for _, scope in contract.file_scope.contracts.items():
            contract_scopes.append(get_contract_key(scope))
        # add self just in case
        contract_scopes.append(contract_key)

        ret[get_contract_key(contract)] = ContractModel(
            name=contract.name,
            key=contract_key,
            path=contract.file_scope.filename.absolute,
            is_abstract=contract.is_abstract,
            is_fully_implemented=contract.is_fully_implemented,
            is_interface=contract.is_interface,
            is_library=contract.is_library,
            directly_inherits=[get_contract_key(c) for c in contract.immediate_inheritance],
            scopes=contract_scopes,
            functions_declared=funcsDeclared,
            functions_inherited=funcsInherited,
        )
    return ret


def get_detector_metadata(slither) -> list[DetectorMetadata]:
    """
    Extract metadata for all available detectors.
    
    Args:
        slither: Slither or LazySlither object
        
    Returns:
        List of DetectorMetadata for all available detectors
    """
    metadata_list = []
    
    # Get all registered detectors from Slither
    for detector_class in slither.detector_classes:
        try:
            metadata = DetectorMetadata(
                name=detector_class.ARGUMENT,
                description=detector_class.HELP,
                impact=detector_class.IMPACT.name.capitalize(),
                confidence=detector_class.CONFIDENCE.name.capitalize()
            )
            metadata_list.append(metadata)
        except Exception as e:
            print(f"Warning: Could not extract metadata for detector: {e}", file=sys.stderr)
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
        if hasattr(element, 'source_mapping') and element.source_mapping:
            source_mapping = element.source_mapping
            if hasattr(source_mapping, 'lines') and source_mapping.lines:
                locations.append(SourceLocation(
                    file_path=str(source_mapping.filename.short),
                    start_line=source_mapping.lines[0],
                    end_line=source_mapping.lines[-1]
                ))
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
        print("Running Slither detectors...", file=sys.stderr)
        # Run all detectors
        detector_results = slither.run_detectors()
        print(f"Detectors completed, processing {len(detector_results)} results...", file=sys.stderr)
        
        for result in detector_results:
            if not result:
                continue
                
            try:
                # Extract detector information
                detector_name = result.get('check', 'unknown')
                impact = result.get('impact', 'Unknown').capitalize()
                confidence = result.get('confidence', 'Unknown').capitalize()
                description = result.get('description', '')
                
                # Extract source locations from elements
                source_locations = []
                elements = result.get('elements', [])
                
                for element in elements:
                    if isinstance(element, dict):
                        # Handle dictionary elements (common in detector output)
                        source_map = element.get('source_mapping', {})
                        if source_map:
                            lines = source_map.get('lines', [])
                            filename = source_map.get('filename_short', source_map.get('filename_relative', ''))
                            if lines and filename:
                                source_locations.append(SourceLocation(
                                    file_path=filename,
                                    start_line=lines[0],
                                    end_line=lines[-1]
                                ))
                    else:
                        # Handle object elements
                        locs = extract_source_locations(element)
                        source_locations.extend(locs)
                
                # Create detector result
                detector_result = DetectorResult(
                    detector_name=detector_name,
                    check=detector_name,
                    impact=impact,
                    confidence=confidence,
                    description=description,
                    source_locations=source_locations
                )
                
                # Add to results dictionary
                if detector_name not in results_by_detector:
                    results_by_detector[detector_name] = []
                results_by_detector[detector_name].append(detector_result)
                
            except Exception as e:
                print(f"Warning: Error processing detector result: {e}", file=sys.stderr)
                continue
        
        print(f"Processed results from {len(results_by_detector)} detectors", file=sys.stderr)
        
    except Exception as e:
        print(f"Warning: Error running detectors: {e}", file=sys.stderr)
    
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
        available_detectors=available_detectors
    )

