"""Type definitions for Slither MCP server."""

import hashlib
import json
import os
from typing import Annotated, Any, TypeAlias

from pydantic import BaseModel, Field, model_validator

# Cache schema version - increment when ProjectFacts structure changes
CACHE_SCHEMA_VERSION = "1.1.0"


class SlitherMCPError(Exception):
    """Base exception for Slither MCP errors."""

    pass


class PathTraversalError(SlitherMCPError):
    """Raised when a path traversal attempt is detected."""

    pass


class CacheCorruptionError(SlitherMCPError):
    """Raised when the cache file is corrupted or invalid."""

    pass


class SlitherAnalysisError(SlitherMCPError):
    """Raised when Slither analysis fails."""

    pass


class AnalysisTimeoutError(SlitherMCPError):
    """Raised when analysis exceeds the timeout limit."""

    pass


def validate_path_within_project(project_path: str, relative_path: str) -> str:
    """
    Validate that a relative path stays within the project directory.

    This prevents path traversal attacks where an attacker could use paths
    like '../../../etc/passwd' to escape the project directory.

    Args:
        project_path: Absolute path to the project root directory
        relative_path: Relative path to validate (e.g., 'src/Contract.sol')

    Returns:
        The normalized absolute path if valid

    Raises:
        PathTraversalError: If the path would escape the project directory
    """
    # Normalize project path to absolute, resolving symlinks (e.g., /tmp -> /private/tmp on macOS)
    project_abs = os.path.realpath(project_path)

    # Join and normalize the full path, resolving any symlinks
    full_path = os.path.realpath(os.path.join(project_abs, relative_path))

    # Check if the full path is still within the project directory
    # Use commonpath to handle edge cases properly
    try:
        common = os.path.commonpath([project_abs, full_path])
        if common != project_abs:
            raise PathTraversalError(
                f"Path traversal detected: '{relative_path}' escapes project directory"
            )
    except ValueError as e:
        # commonpath raises ValueError if paths are on different drives (Windows)
        raise PathTraversalError(
            f"Path traversal detected: '{relative_path}' is on a different drive"
        ) from e

    return full_path


def compute_content_checksum(content: str) -> str:
    """Compute SHA-256 checksum of content for cache validation."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


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

    @model_validator(mode="before")
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
                        if isinstance(parsed_value, dict | list):
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
    library_callees: Annotated[list[ExtFuncSig], Field(description="The library functions called")]
    has_low_level_calls: Annotated[
        bool, Field(description="Whether there are any low-level calls present")
    ]


class StateVariableModel(BaseModel):
    """Model for a state variable in a contract."""

    name: Annotated[str, Field(description="Name of the state variable")]
    type_str: Annotated[str, Field(description="Type of the variable as a string")]
    visibility: Annotated[str, Field(description="Visibility: public, internal, private")]
    is_constant: Annotated[bool, Field(description="Whether the variable is constant")]
    is_immutable: Annotated[bool, Field(description="Whether the variable is immutable")]
    line_number: Annotated[int | None, Field(description="Line number where declared")] = None


class EventParameter(BaseModel):
    """Model for an event parameter."""

    name: Annotated[str, Field(description="Parameter name")]
    type_str: Annotated[str, Field(description="Parameter type as a string")]
    indexed: Annotated[bool, Field(description="Whether the parameter is indexed")]


class EventModel(BaseModel):
    """Model for an event in a contract."""

    name: Annotated[str, Field(description="Name of the event")]
    parameters: Annotated[list[EventParameter], Field(description="Event parameters")]
    line_number: Annotated[int | None, Field(description="Line number where declared")] = None


class SourceLocation(BaseModel):
    """Location in source code where a detector finding occurs."""

    file_path: Annotated[str, Field(description="Path to the source file")]
    start_line: Annotated[int, Field(description="Starting line number")]
    end_line: Annotated[int, Field(description="Ending line number")]


class DetectorMetadata(BaseModel):
    """Metadata about a Slither detector."""

    name: Annotated[str, Field(description="Detector identifier (e.g., 'reentrancy-eth')")]
    description: Annotated[
        str, Field(description="Human-readable description of what the detector checks")
    ]
    impact: Annotated[str, Field(description="Impact level: High, Medium, Low, or Informational")]
    confidence: Annotated[str, Field(description="Confidence level: High, Medium, or Low")]


class DetectorResult(BaseModel):
    """Result from running a Slither detector."""

    detector_name: Annotated[
        str, Field(description="Name of the detector that produced this result")
    ]
    check: Annotated[str, Field(description="Description of what was checked")]
    impact: Annotated[str, Field(description="Impact level of this finding")]
    confidence: Annotated[str, Field(description="Confidence level of this finding")]
    description: Annotated[str, Field(description="Detailed description of the finding")]
    source_locations: Annotated[
        list[SourceLocation], Field(description="Source code locations related to this finding")
    ]


class ContractKey(BaseModel):
    # Note: We implement __hash__ manually instead of using frozen=True
    # to avoid JSON schema generation issues with some MCP clients
    contract_name: Annotated[str, Field(description="The name of the contract")]
    path: Annotated[
        str,
        Field(
            description="The short path of the contract's implementation file, relative to the project's project_directory"
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
    signature: Annotated[
        str,
        Field(
            description="The function's signature. e.g: transferFrom(address,address,uint256). DO NOT include the function's visibility or return type. Running keccak(signature) MUST return the function's ABI selector."
        ),
    ]
    contract_name: Annotated[
        str, Field(description="The name of the contract the function is implemented in")
    ]
    path: Annotated[
        str,
        Field(
            description="The short path of the contract's implementation file, relative to the project's project_directory"
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
        clean_path = self.path.replace("/", "-")
        return f"{self.contract_name}.{self.signature}@{clean_path}"

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
    arguments: Annotated[list[str], Field(description="The types accepted as arguments")]
    returns: Annotated[list[str], Field(description="The types returned by the function")]

    path: Annotated[str, Field(description="The full path to the file the function is defined")]
    line_start: Annotated[int, Field(description="The first line the function is defined on")]
    line_end: Annotated[int, Field(description="The last line the function is defined on")]
    callees: Annotated[FunctionCallees, Field(description="The functions called by this function")]


class ContractModel(BaseModel):
    name: Annotated[contractName, Field(description="The name of the contract")]
    key: ContractKey
    path: Annotated[str, Field(description="The full path to the file the contract is located in")]
    is_abstract: Annotated[bool, Field(description="Whether the contract is abstract")]
    is_fully_implemented: Annotated[
        bool, Field(description="Whether the contract is fully implemented")
    ]
    is_interface: Annotated[bool, Field(description="Whether the contract is an interface")]
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
    state_variables: Annotated[
        list[StateVariableModel],
        Field(description="State variables declared by this contract"),
    ] = []
    events: Annotated[
        list[EventModel],
        Field(description="Events declared by this contract"),
    ] = []

    def does_contract_contain_function(self, sig: FuncSig) -> bool:
        """Check if the contract contains a function with the given signature.

        Uses normalized matching to handle qualified type names like
        'IPoolManager.SwapParams' matching 'SwapParams'.
        """
        # Exact match first (fast path)
        if sig in self.functions_declared:
            return True
        if sig in self.functions_inherited:
            return True

        # Try normalized matching (slow path)
        normalized_sig = normalize_signature(sig)
        for declared_sig in self.functions_declared:
            if normalize_signature(declared_sig) == normalized_sig:
                return True
        for inherited_sig in self.functions_inherited:
            if normalize_signature(inherited_sig) == normalized_sig:
                return True

        return False

    def find_function_signature(self, sig: FuncSig) -> str | None:
        """Find the actual stored signature matching the given signature.

        Uses normalized matching to handle qualified type names.

        Returns:
            The actual signature key if found, None otherwise.
        """
        # Exact match first (fast path)
        if sig in self.functions_declared:
            return sig
        if sig in self.functions_inherited:
            return sig

        # Try normalized matching (slow path)
        normalized_sig = normalize_signature(sig)
        for declared_sig in self.functions_declared:
            if normalize_signature(declared_sig) == normalized_sig:
                return declared_sig
        for inherited_sig in self.functions_inherited:
            if normalize_signature(inherited_sig) == normalized_sig:
                return inherited_sig

        return None

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

    def get_full_inheritance(self, facts: "ProjectFacts") -> list[ContractKey]:
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
        Field(description="Mapping of detector name to list of findings from that detector"),
    ] = {}
    available_detectors: Annotated[
        list[DetectorMetadata],
        Field(description="List of all available Slither detectors with their metadata"),
    ] = []

    @model_validator(mode="before")
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
                    # Check both declared and inherited functions
                    has_implementation = model.functions_declared.get(
                        f
                    ) or model.functions_inherited.get(f)
                    if has_implementation:
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
                (
                    f"Contract not found: '{function_key.contract_name}' at '{function_key.path}'. "
                    f"Use search_contracts or list_contracts to find available contracts."
                ),
            )

        # Check if function exists in contract (with normalized matching)
        func_sig = function_key.signature
        qc = QueryContext(
            searched_calling_context=str(contract_key),
            searched_function=f"{function_key.contract_name}.{function_key.signature}",
            searched_contract=contract_key.contract_name,
        )

        # Use normalized matching to find the actual signature
        actual_sig = contract_model.find_function_signature(func_sig)
        if actual_sig is None:
            return (
                qc,
                None,
                None,
                (
                    f"Function '{func_sig}' not found in contract '{contract_key.contract_name}'. "
                    f"Use list_functions with this contract_key to see available functions, "
                    f"or search_functions to find functions by pattern."
                ),
            )

        # Return the function model using the actual signature
        if actual_sig in contract_model.functions_declared:
            return (
                qc,
                contract_model,
                contract_model.functions_declared[actual_sig],
                None,
            )
        else:
            return (
                qc,
                contract_model,
                contract_model.functions_inherited[actual_sig],
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
                (
                    f"Contract not found: '{calling_context.contract_name}' at '{calling_context.path}'. "
                    f"Use search_contracts or list_contracts to find available contracts."
                ),
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
                (
                    f"Contract '{function_contract_name}' is not in scope for '{calling_context.contract_name}'. "
                    f"Use get_contract to check the 'scopes' field for available contracts in context."
                ),
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
                (
                    f"Function '{func_sig}' not found in contract '{target_contractkey.contract_name}'. "
                    f"Use list_functions with this contract_key to see available functions, "
                    f"or search_functions to find functions by pattern."
                ),
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


def normalize_signature(sig: str) -> str:
    """Normalize a function signature by removing type prefixes.

    Converts signatures like 'swap(PoolKey,IPoolManager.SwapParams,bytes)'
    to 'swap(PoolKey,SwapParams,bytes)' for flexible matching.

    This handles the case where users specify qualified types
    (e.g., Interface.Type) but Slither may store them differently.

    Args:
        sig: A function signature like 'transfer(address,uint256)' or
             'swap(PoolKey,IPoolManager.SwapParams,bytes)'

    Returns:
        The normalized signature with type prefixes removed from parameters.
        The function name itself is never modified.
    """
    if "(" not in sig:
        return sig

    name, rest = sig.split("(", 1)
    params_str = rest.rstrip(")")

    if not params_str:
        return sig

    # Normalize each parameter type by removing prefix before last '.'
    normalized_params = []
    for param in params_str.split(","):
        param = param.strip()
        # Handle array types like "IPoolManager.SwapParams[]"
        suffix = ""
        if param.endswith("[]"):
            suffix = "[]"
            param = param[:-2]
        # Remove prefix like "IPoolManager." from "IPoolManager.SwapParams"
        if "." in param:
            param = param.split(".")[-1]
        normalized_params.append(param + suffix)

    return f"{name}({','.join(normalized_params)})"


def path_matches_exclusion(file_path: str, exclude_patterns: list[str]) -> bool:
    """Check if file_path should be excluded based on patterns.

    Supports:
    - Prefix matching: "lib/" matches "lib/foo.sol"
    - Component matching: "test/" matches "src/test/foo.sol"

    Args:
        file_path: The file path to check (e.g., "src/test/Contract.sol")
        exclude_patterns: List of path patterns to exclude (e.g., ["lib/", "test/"])

    Returns:
        True if the path matches any exclusion pattern, False otherwise.
    """
    normalized = file_path.replace("\\", "/")
    for pattern in exclude_patterns:
        pattern = pattern.rstrip("/")
        # Prefix match: "lib" matches "lib/foo.sol"
        if normalized.startswith(pattern + "/") or normalized == pattern:
            return True
        # Component match: "test" matches "src/test/foo.sol"
        if f"/{pattern}/" in f"/{normalized}/":
            return True
    return False


def find_matching_signature(target_sig: str, available_signatures: dict[str, Any]) -> str | None:
    """Find a matching signature using normalized comparison.

    First tries exact match, then falls back to normalized matching.

    Args:
        target_sig: The signature to find
        available_signatures: Dict of signature -> value to search

    Returns:
        The actual signature key if found, None otherwise
    """
    # Fast path: exact match
    if target_sig in available_signatures:
        return target_sig

    # Slow path: try normalized matching
    normalized_target = normalize_signature(target_sig)
    for sig in available_signatures:
        if normalize_signature(sig) == normalized_target:
            return sig

    return None
