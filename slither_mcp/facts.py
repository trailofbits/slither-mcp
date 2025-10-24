"""Project facts generation from Slither analysis."""

from slither_mcp.callees import get_callees
from slither_mcp.types import (
    ContractKey,
    ContractModel,
    FuncSig,
    FunctionModel,
    ProjectFacts,
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
    return ProjectFacts(contracts=contracts, project_dir=project_dir)

