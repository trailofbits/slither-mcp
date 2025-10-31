"""Type definitions for Slither MCP server."""

import json
from typing import Any, Annotated, List
from pydantic import BaseModel, ConfigDict, Field, model_validator

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

contractName: TypeAlias = str
ExtFuncSig: TypeAlias = str
FuncSig: TypeAlias = str
solidityType: TypeAlias = str


class JSONStringTolerantModel(BaseModel):
    """
    Base model that handles JSON string deserialization for MCP compatibility.
    
    Some MCP clients (like Cursor/Claude Desktop) may send nested objects as
    JSON strings instead of parsed dictionaries. This base class automatically
    detects and parses such strings before Pydantic validation occurs.
    
    Usage:
        class MyRequest(JSONStringTolerantModel):
            nested_field: SomeModel
    
    This will accept both:
        - {"nested_field": {"key": "value"}}  # Normal dict
        - {"nested_field": '{"key": "value"}'}  # JSON string (auto-parsed)
    """
    
    @model_validator(mode='before')
    @classmethod
    def parse_json_strings(cls, data: Any) -> Any:
        """
        Recursively parse any JSON strings in the input data.
        
        This validator runs before Pydantic's normal validation, allowing us to
        convert JSON strings into dicts/lists that Pydantic can then validate
        against the model schema.
        """
        if isinstance(data, str):
            # The entire request might be a JSON string
            try:
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return data
        
        if isinstance(data, dict):
            # Check each field to see if it's a stringified JSON
            parsed = {}
            for key, value in data.items():
                if isinstance(value, str):
                    try:
                        parsed_value = json.loads(value)
                        # Only use parsed value if it's a dict/list
                        # (avoid parsing string values like "true" -> True)
                        if isinstance(parsed_value, (dict, list)):
                            parsed[key] = parsed_value
                        else:
                            parsed[key] = value
                    except (json.JSONDecodeError, TypeError):
                        parsed[key] = value
                else:
                    parsed[key] = value
            return parsed
        
        return data


class FunctionCallees(BaseModel):
    internal_callees: Annotated[
        list[ExtFuncSig], Field(description="The internal functions called")
    ]
    external_callees: Annotated[
        list[ExtFuncSig], Field(description="The external functions called")
    ]
    library_callees: Annotated[
        list[ExtFuncSig], Field(description="The library functions called")
    ]
    has_low_level_calls: Annotated[
        bool, Field(description="Whether there are any low-level calls present")
    ]


class SourceLocation(BaseModel):
    """Location in source code where a detector finding occurs."""
    file_path: Annotated[str, Field(description="Path to the source file")]
    start_line: Annotated[int, Field(description="Starting line number")]
    end_line: Annotated[int, Field(description="Ending line number")]


class DetectorMetadata(BaseModel):
    """Metadata about a Slither detector."""
    name: Annotated[str, Field(description="Detector identifier (e.g., 'reentrancy-eth')")]
    description: Annotated[str, Field(description="Human-readable description of what the detector checks")]
    impact: Annotated[str, Field(description="Impact level: High, Medium, Low, or Informational")]
    confidence: Annotated[str, Field(description="Confidence level: High, Medium, or Low")]


class DetectorResult(BaseModel):
    """Result from running a Slither detector."""
    detector_name: Annotated[str, Field(description="Name of the detector that produced this result")]
    check: Annotated[str, Field(description="Description of what was checked")]
    impact: Annotated[str, Field(description="Impact level of this finding")]
    confidence: Annotated[str, Field(description="Confidence level of this finding")]
    description: Annotated[str, Field(description="Detailed description of the finding")]
    source_locations: Annotated[
        list[SourceLocation],
        Field(description="Source code locations related to this finding")
    ]


class ContractKey(BaseModel):
    # Note: We implement __hash__ manually instead of using frozen=True
    # to avoid JSON schema generation issues with some MCP clients
    contract_name: Annotated[str, Field(description="The name of the contract")]
    path: Annotated[
        str,
        Field(
            description="The short path of the contract's implementation file, relative to the base directory"
        ),
    ]

    def __hash__(self):
        return hash((self.contract_name, self.path))

    def __eq__(self, other):
        if not isinstance(other, ContractKey):
            return False
        return self.contract_name == other.contract_name and self.path == other.path

    def __str__(self):
        pr = self.path.replace("/", "!")
        return f"{self.contract_name}@{pr}"

    @classmethod
    def from_string(cls, s: str) -> "ContractKey":
        """Parse a ContractKey from its string representation."""
        if "@" not in s:
            raise ValueError(f"Invalid ContractKey string format: {s}")
        contract_name, path = s.split("@", 1)
        return cls(contract_name=contract_name, path=path.replace("!", "/"))


class FunctionKey(BaseModel):
    # Note: We implement __hash__ manually instead of using frozen=True
    # to avoid JSON schema generation issues with some MCP clients
    signature: Annotated[str, Field(description="The function's signature. e.g: transferFrom(address,address,uint256). DO NOT include the function's visibility or return type. Running keccak(signature) MUST return the function's ABI selector.")]
    contract_name: Annotated[str, Field(description="The name of the contract the function is implemented in")]
    path: Annotated[
        str,
        Field(
            description="The short path of the contract's implementation file, relative to the base directory"
        ),
    ]

    def __hash__(self):
        return hash((self.signature, self.contract_name, self.path))

    def __eq__(self, other):
        if not isinstance(other, FunctionKey):
            return False
        return (
            self.contract_name == other.contract_name
            and self.path == other.path
            and self.signature == other.signature
        )

    def __str__(self):
        cleanPath = self.path.replace("/", "-")
        return f"{self.contract_name}.{self.signature}@{cleanPath}"

    @classmethod
    def from_string(cls, s: str) -> "FunctionKey":
        """Parse a FunctionKey from its string representation."""
        if "@" not in s or "." not in s:
            raise ValueError(f"Invalid ContractKey string format: {s}")
        full, path = s.split("@", 1)
        path = path.replace("-", "/")
        contract, sig = full.split(".")
        return cls(contract_name=contract, path=path, signature=sig)

    def get_context(self):
        return ContractKey(contract_name=self.contract_name, path=self.path)


class QueryContext(BaseModel):
    searched_calling_context: str | None = None
    searched_function: str | None = None
    searched_contract: str | None = None


class FunctionModel(BaseModel):
    signature: Annotated[FuncSig, Field(description="The function's signature")]
    implementation_contract: Annotated[
        ContractKey, Field(description="The contract this function is implemented in")
    ]
    solidity_modifiers: Annotated[
        list[str],
        Field(
            description="The modifiers for the function. May contain virtual, fallback, override, view, pure, and payable"
        ),
    ]
    visibility: Annotated[str, Field(description="The function's visibility")]
    function_modifiers: Annotated[
        list[str], Field(description="The custom modifiers decorating the function")
    ]
    arguments: Annotated[
        list[str], Field(description="The types accepted as arguments")
    ]
    returns: Annotated[
        list[str], Field(description="The types returned by the function")
    ]

    path: Annotated[
        str, Field(description="The full path to the file the function is defined")
    ]
    line_start: Annotated[
        int, Field(description="The first line the function is defined on")
    ]
    line_end: Annotated[
        int, Field(description="The last line the function is defined on")
    ]
    callees: Annotated[
        FunctionCallees, Field(description="The functions called by this function")
    ]


class ContractModel(BaseModel):
    name: Annotated[contractName, Field(description="The name of the contract")]
    key: ContractKey
    path: Annotated[
        str, Field(description="The full path to the file the contract is located in")
    ]
    is_abstract: Annotated[bool, Field(description="Whether the contract is abstract")]
    is_fully_implemented: Annotated[
        bool, Field(description="Whether the contract is fully implemented")
    ]
    is_interface: Annotated[
        bool, Field(description="Whether the contract is an interface")
    ]
    is_library: Annotated[bool, Field(description="Whether the contract is a library")]
    directly_inherits: Annotated[
        list[ContractKey],
        Field(description="The contracts that this one directly inherits from"),
    ]
    scopes: Annotated[
        list["ContractKey"],
        Field(description="The contracts in scope for this contract"),
    ]

    functions_declared: Annotated[
        dict[FuncSig, FunctionModel],
        Field(description="The functions declared by this contract"),
    ]
    functions_inherited: Annotated[
        dict[FuncSig, FunctionModel],
        Field(description="The functions inherited by this contract"),
    ]

    def does_contract_contain_function(self, sig: FuncSig) -> bool:
        if sig in self.functions_declared:
            return True
        if sig in self.functions_inherited:
            return True
        return False

    def is_contract_in_context(self, contract_name: str) -> bool:
        for scope in self.scopes:
            if scope.contract_name == contract_name:
                return True
        return False

    def get_function_call_context(self, function: ExtFuncSig) -> ContractKey:
        """Get the contract key for a function signature."""
        function_contract_name = function.split(".")[0]

        for contract in self.scopes:
            if contract.contract_name == function_contract_name:
                return contract
        raise ValueError(f"Contract '{function_contract_name}' not found in scopes")

    def get_full_inheritance(self, facts: "ProjectFacts") -> List[ContractKey]:
        inherited_contracts = set()
        for key in self.directly_inherits:
            model = facts.contracts[key]
            inherited_contracts.add(key)

            sub_inheritance = model.get_full_inheritance(facts)
            for item in sub_inheritance:
                inherited_contracts.add(item)
        return list(inherited_contracts)


class ProjectFacts(BaseModel):
    contracts: dict[ContractKey, ContractModel]
    project_dir: str
    detector_results: Annotated[
        dict[str, list[DetectorResult]],
        Field(
            default_factory=dict,
            description="Mapping of detector name to list of findings from that detector"
        )
    ]
    available_detectors: Annotated[
        list[DetectorMetadata],
        Field(
            default_factory=list,
            description="List of all available Slither detectors with their metadata"
        )
    ]

    @model_validator(mode='before')
    @classmethod
    def convert_string_keys_to_contract_keys(cls, data: Any) -> Any:
        """Convert string keys back to ContractKey objects during deserialization."""
        if isinstance(data, dict):
            # Convert contracts dictionary
            if "contracts" in data and isinstance(data["contracts"], dict):
                new_contracts = {}
                for key, value in data["contracts"].items():
                    if isinstance(key, str):
                        key = ContractKey.from_string(key)

                    # Convert scopes in each ContractModel if present
                    if isinstance(value, dict) and "scopes" in value:
                        scopes = value["scopes"]
                        if isinstance(scopes, list):
                            new_scopes = []
                            for scope in scopes:
                                if isinstance(scope, str):
                                    new_scopes.append(ContractKey.from_string(scope))
                                else:
                                    new_scopes.append(scope)
                            value["scopes"] = new_scopes

                    new_contracts[key] = value
                data["contracts"] = new_contracts
        return data

    def is_contract_in_context(self, context: ContractKey, contract_name: str) -> bool:
        context_contract = self.contracts.get(context)
        if not context_contract:
            return False

        for scope in context_contract.scopes:
            if scope.contract_name == contract_name:
                return True
        return False

    def resolve_function_implementations(
        self, contract_model: "ContractModel", signature: FuncSig
    ) -> list["ContractModel"]:
        """
        Find all contracts that implement a given function signature.
        
        This is used to find implementations of abstract functions or interface methods.
        
        Args:
            contract_model: The parent contract (abstract or interface)
            signature: The function signature to find implementations for
            
        Returns:
            List of ContractModels that implement the function
        """
        def get_contracts_implementing_function(
            parent_contract: "ContractModel", f: FuncSig
        ) -> list["ContractModel"]:
            children_with_implementation = []

            for _, model in self.contracts.items():
                if parent_contract.key in model.directly_inherits:
                    if model.functions_declared.get(f):
                        children_with_implementation.append(model)

                        # check for even deeper inherited contracts that override the implementation
                        children_with_implementation.extend(
                            get_contracts_implementing_function(model, f)
                        )
                    else:
                        # function not implemented here, so it's implemented in a derived contract
                        children_with_implementation.extend(
                            get_contracts_implementing_function(model, f)
                        )
            return children_with_implementation

        return get_contracts_implementing_function(contract_model, signature)

    def resolve_function_by_key(
        self, function_key: FunctionKey
    ) -> tuple[
        QueryContext,
        "ContractModel | None",
        FunctionModel | None,
        str | None,
    ]:
        """
        Resolve a function using a FunctionKey.
        
        Args:
            function_key: The FunctionKey identifying the function
            
        Returns:
            Tuple of (QueryContext, ContractModel, FunctionModel, error_message)
        """
        # Get the contract key from the function key
        contract_key = function_key.get_context()
        
        # Check if contract exists
        contract_model = self.contracts.get(contract_key)
        if not contract_model:
            return (
                QueryContext(
                    searched_calling_context=str(contract_key),
                    searched_function=f"{function_key.contract_name}.{function_key.signature}",
                ),
                None,
                None,
                f"The specified contract does not exist: '{function_key.contract_name}' at '{function_key.path}'",
            )
        
        # Check if function exists in contract
        func_sig = function_key.signature
        qc = QueryContext(
            searched_calling_context=str(contract_key),
            searched_function=f"{function_key.contract_name}.{function_key.signature}",
            searched_contract=contract_key.contract_name,
        )
        
        if not contract_model.does_contract_contain_function(func_sig):
            return (
                qc,
                None,
                None,
                f"The specified function '{func_sig}' is not implemented by the contract: '{contract_key.contract_name}'",
            )
        
        # Return the function model
        if func_sig in contract_model.functions_declared:
            return (
                qc,
                contract_model,
                contract_model.functions_declared[func_sig],
                None,
            )
        else:
            return (
                qc,
                contract_model,
                contract_model.functions_inherited[func_sig],
                None,
            )

    def resolve_function(
        self, ext_signature: ExtFuncSig, calling_context: ContractKey
    ) -> tuple[
        QueryContext,
        "ContractModel | None",
        FunctionModel | None,
        str | None,
    ]:
        """
        Resolve a function signature in a given calling context.
        
        Args:
            ext_signature: External function signature (e.g., 'ContractName.functionName(args)')
            calling_context: The contract context from which the function is called
            
        Returns:
            Tuple of (QueryContext, ContractModel, FunctionModel, error_message)
        """
        # Validate format
        if "." not in ext_signature:
            return (
                QueryContext(),
                None,
                None,
                f"Invalid external function signature format. Expected 'ContractName.functionSignature(args)', got: '{ext_signature}'",
            )

        # Check if context exists
        context_model = self.contracts.get(calling_context)
        if not context_model:
            return (
                QueryContext(searched_calling_context=str(calling_context)),
                None,
                None,
                f"The specified calling context does not exist. '{calling_context.contract_name}'",
            )

        # Check context for contract
        function_contract_name = get_contract_from_ext_func_sig(ext_signature)
        if not self.is_contract_in_context(calling_context, function_contract_name):
            return (
                QueryContext(
                    searched_calling_context=str(calling_context),
                    searched_function=ext_signature,
                ),
                None,
                None,
                f"The specified contract '{function_contract_name}' is not within the calling context: '{calling_context.contract_name}'",
            )

        # Check contract for function
        func_sig = ext_func_sig_to_func_sig(ext_signature)
        target_contractkey = context_model.get_function_call_context(ext_signature)
        target_contract_model = self.contracts[target_contractkey]

        qc = QueryContext(
            searched_calling_context=str(calling_context),
            searched_function=ext_signature,
            searched_contract=target_contractkey.contract_name,
        )
        if not target_contract_model.does_contract_contain_function(func_sig):
            return (
                qc,
                None,
                None,
                f"The specified function '{func_sig}' is not implemented by the contract: '{target_contractkey.contract_name}'",
            )

        if func_sig in target_contract_model.functions_declared:
            return (
                qc,
                target_contract_model,
                target_contract_model.functions_declared[func_sig],
                None,
            )
        else:
            return (
                qc,
                target_contract_model,
                target_contract_model.functions_inherited[func_sig],
                None,
            )


def get_contract_key(contract) -> ContractKey:
    """Get ContractKey from a slither contract object."""
    return ContractKey(
        contract_name=contract.name,
        path=contract.file_scope.filename.short,
    )


def get_func_sig(function_contract) -> FuncSig:
    """Get function signature from a slither function object."""
    funcName, args, returns = function_contract.signature
    return funcName + "(" + ",".join(args) + ")"


def ext_func_sig_to_func_sig(signature: ExtFuncSig) -> FuncSig:
    """Extract function signature from external function signature."""
    return ".".join(signature.split(".")[1:])


def get_contract_from_ext_func_sig(signature: ExtFuncSig) -> str:
    """Extract contract name from external function signature."""
    return signature.split(".")[0]

