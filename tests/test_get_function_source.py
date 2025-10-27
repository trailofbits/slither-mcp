"""Tests for get_function_source tool."""

import pytest
from unittest.mock import mock_open, patch
from slither_mcp.tools.get_function_source import (
    GetFunctionSourceRequest,
    get_function_source,
)
from slither_mcp.types import FunctionKey


class TestGetFunctionSourceHappyPath:
    """Test happy path scenarios for get_function_source."""

    def test_get_declared_function_source(self, project_facts, base_contract_key):
        """Test getting source code for a declared function."""
        mock_source = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

abstract contract BaseContract {
    uint256 private data;
    
    constructor() {
        data = 0;
    }
    function initialize() public {
        // initialization logic
        data = 42;
        emit Initialized(data);
    }

    function baseFunction() internal view returns (uint256) {
        return data;
    }
}
"""
        function_key = FunctionKey(
            signature="initialize()",
            contract_name="BaseContract",
            path="contracts/Base.sol"
        )
        request = GetFunctionSourceRequest(function_key=function_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_function_source(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.file_path == "contracts/Base.sol"
        assert response.line_start == 10
        assert response.line_end == 15
        # Lines 10-15 should be extracted (1-indexed)
        expected_code = """    function initialize() public {
        // initialization logic
        data = 42;
        emit Initialized(data);
    }

"""
        assert response.source_code == expected_code

    def test_get_single_line_function_source(self, project_facts, interface_a_key):
        """Test getting source code for a single-line function declaration."""
        mock_source = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface InterfaceA {
    function interfaceMethod() external;
}
"""
        function_key = FunctionKey(
            signature="interfaceMethod()",
            contract_name="InterfaceA",
            path="contracts/IInterface.sol"
        )
        request = GetFunctionSourceRequest(function_key=function_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_function_source(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.file_path == "contracts/IInterface.sol"
        assert response.line_start == 5
        assert response.line_end == 5
        assert response.source_code == "    function interfaceMethod() external;\n"

    def test_get_multi_line_function_with_params(self, project_facts, standalone_contract_key):
        """Test getting source code for a multi-line function with parameters."""
        mock_source = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract StandaloneContract {
    uint256 public value;
    address public owner;
    
    event ValueSet(uint256 indexed newValue);
    
    modifier nonReentrant() {
        require(!locked, "No reentrancy");
        locked = true;
        _;
        locked = false;
    }
    function standaloneFunction(uint256 _value, address _addr) public nonReentrant returns (bool) {
        require(_addr != address(0), "Invalid address");
        value = _value;
        owner = _addr;
        emit ValueSet(_value);
        return true;
    }

    bool private locked;
}
"""
        function_key = FunctionKey(
            signature="standaloneFunction(uint256,address)",
            contract_name="StandaloneContract",
            path="contracts/Standalone.sol"
        )
        request = GetFunctionSourceRequest(function_key=function_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_function_source(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.file_path == "contracts/Standalone.sol"
        assert response.line_start == 15
        assert response.line_end == 22
        # Lines 15-22 should be extracted (includes closing brace from modifier)
        expected_code = """    }
    function standaloneFunction(uint256 _value, address _addr) public nonReentrant returns (bool) {
        require(_addr != address(0), "Invalid address");
        value = _value;
        owner = _addr;
        emit ValueSet(_value);
        return true;
    }
"""
        assert response.source_code == expected_code

    def test_get_library_function_source(self, project_facts, library_b_key):
        """Test getting source code for a library function."""
        mock_source = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

library LibraryB {
    uint256 constant MAX = type(uint256).max;
    
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        require(a <= MAX - b, "Overflow");
        return a + b;
    }
}
"""
        function_key = FunctionKey(
            signature="add(uint256,uint256)",
            contract_name="LibraryB",
            path="contracts/Library.sol"
        )
        request = GetFunctionSourceRequest(function_key=function_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_function_source(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.file_path == "contracts/Library.sol"
        assert response.line_start == 7
        assert response.line_end == 10
        expected_code = """    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        require(a <= MAX - b, "Overflow");
        return a + b;
    }
"""
        assert response.source_code == expected_code

    def test_get_child_contract_declared_function(self, project_facts, child_contract_key):
        """Test getting source code for a function declared in a child contract."""
        mock_source = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./Base.sol";

contract ChildContract is BaseContract {
    address public owner;
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    function childFunction(address _addr) public payable onlyOwner {
        require(_addr != address(0), "Invalid");
        owner = _addr;
        // additional logic
        emit OwnerChanged(_addr);
    }

    event OwnerChanged(address indexed newOwner);
}
"""
        function_key = FunctionKey(
            signature="childFunction(address)",
            contract_name="ChildContract",
            path="contracts/Child.sol"
        )
        request = GetFunctionSourceRequest(function_key=function_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_function_source(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.file_path == "contracts/Child.sol"
        assert response.line_start == 12
        assert response.line_end == 18
        # Lines 12-18 should be extracted (includes closing brace from modifier)
        expected_code = """    }
    function childFunction(address _addr) public payable onlyOwner {
        require(_addr != address(0), "Invalid");
        owner = _addr;
        // additional logic
        emit OwnerChanged(_addr);
    }
"""
        assert response.source_code == expected_code

    def test_get_inherited_function_source(self, project_facts, base_contract_key):
        """Test getting source for an inherited function (returns the source from original contract)."""
        # When we request a function from a child contract that inherits it,
        # the FunctionModel in the inherited dict will point to the base contract's path
        mock_source = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

abstract contract BaseContract {
    uint256 private data;
    
    constructor() {
        data = 0;
    }
    function initialize() public {
        // initialization logic
        data = 42;
        emit Initialized(data);
    }


    function baseFunction() internal view returns (uint256) {
        return data;
    }
}
"""
        # Request baseFunction from the base contract
        function_key = FunctionKey(
            signature="baseFunction()",
            contract_name="BaseContract",
            path="contracts/Base.sol"
        )
        request = GetFunctionSourceRequest(function_key=function_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_function_source(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.file_path == "contracts/Base.sol"
        assert response.line_start == 17
        assert response.line_end == 20
        # Lines 17-20 includes the function and contract closing brace
        expected_code = """    function baseFunction() internal view returns (uint256) {
        return data;
    }
}
"""
        assert response.source_code == expected_code


class TestGetFunctionSourceEdgeCases:
    """Test edge cases for get_function_source."""

    def test_function_not_found_invalid_contract(self, project_facts):
        """Test getting source for a function in a non-existent contract."""
        function_key = FunctionKey(
            signature="nonExistent()",
            contract_name="NonExistentContract",
            path="contracts/NonExistent.sol"
        )
        request = GetFunctionSourceRequest(function_key=function_key)
        response = get_function_source(request, project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert "does not exist" in response.error_message
        assert response.source_code is None

    def test_function_not_found_invalid_signature(self, project_facts, base_contract_key):
        """Test getting source for a non-existent function in a valid contract."""
        function_key = FunctionKey(
            signature="nonExistentFunction()",
            contract_name="BaseContract",
            path="contracts/Base.sol"
        )
        request = GetFunctionSourceRequest(function_key=function_key)
        response = get_function_source(request, project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert "not implemented" in response.error_message
        assert response.source_code is None

    def test_source_file_not_found(self, project_facts, base_contract_key):
        """Test error when source file doesn't exist."""
        function_key = FunctionKey(
            signature="initialize()",
            contract_name="BaseContract",
            path="contracts/Base.sol"
        )
        request = GetFunctionSourceRequest(function_key=function_key)
        
        with patch("os.path.exists", return_value=False):
            response = get_function_source(request, project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert "Source file not found" in response.error_message
        assert "contracts/Base.sol" in response.error_message
        assert response.source_code is None

    def test_file_read_error(self, project_facts, base_contract_key):
        """Test error handling when file cannot be read."""
        function_key = FunctionKey(
            signature="initialize()",
            contract_name="BaseContract",
            path="contracts/Base.sol"
        )
        request = GetFunctionSourceRequest(function_key=function_key)
        
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", side_effect=IOError("Permission denied")):
                response = get_function_source(request, project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert "Error reading source file" in response.error_message
        assert response.source_code is None

    def test_line_range_exceeds_file_length(self, project_facts, base_contract_key):
        """Test error when function line range exceeds actual file length."""
        mock_source = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// This file only has 5 lines
"""
        function_key = FunctionKey(
            signature="initialize()",
            contract_name="BaseContract",
            path="contracts/Base.sol"
        )
        request = GetFunctionSourceRequest(function_key=function_key)
        
        # Function model says lines 10-15, but file only has 5 lines
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_function_source(request, project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert "exceeds file length" in response.error_message
        assert "4 lines" in response.error_message
        assert response.source_code is None

    def test_empty_project(self, empty_project_facts):
        """Test getting source from an empty project."""
        function_key = FunctionKey(
            signature="someFunction()",
            contract_name="SomeContract",
            path="contracts/Some.sol"
        )
        request = GetFunctionSourceRequest(function_key=function_key)
        response = get_function_source(request, empty_project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert response.source_code is None

    def test_contract_with_no_functions(self, project_facts, empty_contract_key):
        """Test getting source for a function in a contract with no functions."""
        function_key = FunctionKey(
            signature="someFunction()",
            contract_name="EmptyContract",
            path="contracts/Empty.sol"
        )
        request = GetFunctionSourceRequest(function_key=function_key)
        response = get_function_source(request, project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert response.source_code is None


class TestGetFunctionSourceWithComplexInheritance:
    """Test get_function_source with complex inheritance scenarios."""

    def test_get_function_from_grandchild(self, project_facts, grandchild_contract_key):
        """Test getting a function declared in a grandchild contract."""
        mock_source = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./Child.sol";

contract GrandchildContract is ChildContract {
    uint256 public level;
    
    constructor() {
        level = 3;
    }
    function grandchildFunction() external view returns (bool) {
        return level > 0;
    }
}
"""
        function_key = FunctionKey(
            signature="grandchildFunction()",
            contract_name="GrandchildContract",
            path="contracts/Grandchild.sol"
        )
        request = GetFunctionSourceRequest(function_key=function_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_function_source(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.file_path == "contracts/Grandchild.sol"
        assert response.line_start == 10
        assert response.line_end == 13
        # Lines 10-13 includes part of the constructor and the function start
        expected_code = """        level = 3;
    }
    function grandchildFunction() external view returns (bool) {
        return level > 0;
"""
        assert response.source_code == expected_code

    def test_get_overridden_function(self, project_facts, multi_inherit_contract_key):
        """Test getting an overridden function from a multi-inheritance contract."""
        mock_source = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./Base.sol";
import "./IInterface.sol";

contract MultiInheritContract is BaseContract, InterfaceA {
    function interfaceMethod() external override {
        // Implementation
        emit MethodCalled();
    }

    function multiFunction() private {
        // Private function
        uint256 x = 42;
    }
}
"""
        function_key = FunctionKey(
            signature="interfaceMethod()",
            contract_name="MultiInheritContract",
            path="contracts/Multi.sol"
        )
        request = GetFunctionSourceRequest(function_key=function_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_function_source(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.file_path == "contracts/Multi.sol"
        assert response.line_start == 8
        assert response.line_end == 11
        # Lines 8-11 includes the function
        expected_code = """    function interfaceMethod() external override {
        // Implementation
        emit MethodCalled();
    }
"""
        assert response.source_code == expected_code

    def test_get_private_function(self, project_facts, multi_inherit_contract_key):
        """Test getting a private function's source."""
        mock_source = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./Base.sol";
import "./IInterface.sol";

contract MultiInheritContract is BaseContract, InterfaceA {
    function interfaceMethod() external override {
        // Implementation
        emit MethodCalled();
    }

    function multiFunction() private {
        // Private function
        uint256 x = 42;
    }
}
"""
        function_key = FunctionKey(
            signature="multiFunction()",
            contract_name="MultiInheritContract",
            path="contracts/Multi.sol"
        )
        request = GetFunctionSourceRequest(function_key=function_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_function_source(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.file_path == "contracts/Multi.sol"
        assert response.line_start == 13
        assert response.line_end == 16
        expected_code = """    function multiFunction() private {
        // Private function
        uint256 x = 42;
    }
"""
        assert response.source_code == expected_code

