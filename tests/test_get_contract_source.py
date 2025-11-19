"""Tests for get_contract_source tool."""

import os
import pytest
from unittest.mock import mock_open, patch
from slither_mcp.tools.get_contract_source import (
    GetContractSourceRequest,
    get_contract_source,
)
from slither_mcp.types import ContractKey


class TestGetContractSourceHappyPath:
    """Test happy path scenarios for get_contract_source."""

    def test_get_base_contract_source(self, test_path, project_facts, base_contract_key):
        """Test getting source code for BaseContract."""
        mock_source = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

abstract contract BaseContract {
    function initialize() public {
        // initialization logic
    }

    function baseFunction() internal view returns (uint256) {
        return 42;
    }
}
"""
        request = GetContractSourceRequest(path=test_path, contract_key=base_contract_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_contract_source(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.source_code == mock_source
        assert response.file_path == "contracts/Base.sol"

    def test_get_child_contract_source(self, test_path, project_facts, child_contract_key):
        """Test getting source code for ChildContract."""
        mock_source = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./Base.sol";

contract ChildContract is BaseContract {
    function childFunction(address _addr) public payable onlyOwner {
        // child function logic
    }
}
"""
        request = GetContractSourceRequest(path=test_path, contract_key=child_contract_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_contract_source(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.source_code == mock_source
        assert response.file_path == "contracts/Child.sol"

    def test_get_interface_source(self, test_path, project_facts, interface_a_key):
        """Test getting source code for an interface."""
        mock_source = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface InterfaceA {
    function interfaceMethod() external;
}
"""
        request = GetContractSourceRequest(path=test_path, contract_key=interface_a_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_contract_source(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.source_code == mock_source
        assert response.file_path == "contracts/IInterface.sol"

    def test_get_library_source(self, test_path, project_facts, library_b_key):
        """Test getting source code for a library."""
        mock_source = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

library LibraryB {
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        return a + b;
    }
}
"""
        request = GetContractSourceRequest(path=test_path, contract_key=library_b_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_contract_source(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.source_code == mock_source
        assert response.file_path == "contracts/Library.sol"

    def test_source_with_multiple_contracts(self, test_path, project_facts, base_contract_key):
        """Test getting source when file contains multiple contracts."""
        mock_source = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

abstract contract BaseContract {
    function initialize() public {
        // initialization logic
    }
}

contract AnotherContract {
    // Another contract in the same file
}
"""
        request = GetContractSourceRequest(path=test_path, contract_key=base_contract_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_contract_source(request, project_facts)

        # Should return the entire file content
        assert response.success is True
        assert response.error_message is None
        assert "abstract contract BaseContract" in response.source_code
        assert "contract AnotherContract" in response.source_code
        assert response.file_path == "contracts/Base.sol"

    def test_empty_source_file(self, test_path, project_facts, empty_contract_key):
        """Test getting source code from an empty file."""
        mock_source = ""
        request = GetContractSourceRequest(path=test_path, contract_key=empty_contract_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_contract_source(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.source_code == ""
        assert response.file_path == "contracts/Empty.sol"


class TestGetContractSourceEdgeCases:
    """Test edge cases for get_contract_source."""

    def test_nonexistent_contract(self, test_path, project_facts):
        """Test getting source for a contract that doesn't exist."""
        request = GetContractSourceRequest(path=test_path, 
            contract_key=ContractKey(
                contract_name="NonExistent",
                path="contracts/NonExistent.sol"
            )
        )
        response = get_contract_source(request, project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert "Contract not found" in response.error_message
        assert response.source_code is None
        assert response.file_path is None

    def test_source_file_not_found(self, test_path, project_facts, base_contract_key):
        """Test when the contract exists but the source file doesn't."""
        request = GetContractSourceRequest(path=test_path, contract_key=base_contract_key)
        
        # Mock os.path.exists to return True for project dir, False for source file
        def mock_exists(path):
            # Return True for project directory, False for source file
            return path == test_path
        
        with patch("os.path.exists", side_effect=mock_exists):
            response = get_contract_source(request, project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert "Source file not found" in response.error_message
        assert response.source_code is None
        assert response.file_path is None

    def test_file_read_error(self, test_path, project_facts, base_contract_key):
        """Test when reading the file raises an exception."""
        request = GetContractSourceRequest(path=test_path, contract_key=base_contract_key)
        
        # Mock file open to raise an exception
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with patch("os.path.exists", return_value=True):
                response = get_contract_source(request, project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert "Error reading source file" in response.error_message
        assert response.source_code is None
        assert response.file_path is None

    def test_empty_project(self, test_path, empty_project_facts):
        """Test getting source from an empty project."""
        request = GetContractSourceRequest(path=test_path, 
            contract_key=ContractKey(
                contract_name="SomeContract",
                path="contracts/Some.sol"
            )
        )
        response = get_contract_source(request, empty_project_facts)

        assert response.success is False
        assert response.error_message is not None
        assert "Contract not found" in response.error_message
        assert response.source_code is None
        assert response.file_path is None

    def test_unicode_in_source(self, test_path, project_facts, base_contract_key):
        """Test handling source files with Unicode characters."""
        mock_source = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Contract with Unicode: 你好, мир, 🚀
abstract contract BaseContract {
    string public greeting = "Hello 世界";
}
"""
        request = GetContractSourceRequest(path=test_path, contract_key=base_contract_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_contract_source(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert "你好" in response.source_code
        assert "мир" in response.source_code
        assert "🚀" in response.source_code
        assert "世界" in response.source_code

    def test_very_large_source_file(self, test_path, project_facts, base_contract_key):
        """Test handling a very large source file."""
        # Create a large mock source (simulate a big contract)
        mock_source = "// Large contract\n" + ("contract Line {}\n" * 10000)
        request = GetContractSourceRequest(path=test_path, contract_key=base_contract_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_contract_source(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert len(response.source_code) > 100000  # Should be large
        assert response.source_code == mock_source

    def test_source_with_special_characters(self, test_path, project_facts, base_contract_key):
        """Test source code with various special characters."""
        mock_source = """// Special chars: @#$%^&*()
pragma solidity ^0.8.0;

contract BaseContract {
    // Tabs\t\tand\tnewlines\n
    string special = "quotes ' \" and backslashes \\";
}
"""
        request = GetContractSourceRequest(path=test_path, contract_key=base_contract_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_contract_source(request, project_facts)

        assert response.success is True
        assert response.error_message is None
        assert response.source_code == mock_source


class TestGetContractSourceFilePathHandling:
    """Test file path handling scenarios."""

    def test_absolute_path_in_contract(self, test_path, project_facts, base_contract_key):
        """Test when contract model contains an absolute path."""
        # Modify the contract's path to be absolute
        contract = project_facts.contracts[base_contract_key]
        absolute_path = "/absolute/path/to/contracts/Base.sol"
        
        # Create a new contract model with absolute path
        from slither_mcp.types import ContractModel
        modified_contract = ContractModel(
            name=contract.name,
            key=contract.key,
            path=absolute_path,
            is_abstract=contract.is_abstract,
            is_fully_implemented=contract.is_fully_implemented,
            is_interface=contract.is_interface,
            is_library=contract.is_library,
            directly_inherits=contract.directly_inherits,
            scopes=contract.scopes,
            functions_declared=contract.functions_declared,
            functions_inherited=contract.functions_inherited,
        )
        
        # Replace in project_facts
        project_facts.contracts[base_contract_key] = modified_contract
        
        mock_source = "// Absolute path test"
        request = GetContractSourceRequest(path=test_path, contract_key=base_contract_key)
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_contract_source(request, project_facts)

        assert response.success is True
        assert response.file_path == absolute_path

    def test_relative_path_in_contract(self, test_path, project_facts, child_contract_key):
        """Test when contract model contains a relative path."""
        request = GetContractSourceRequest(path=test_path, contract_key=child_contract_key)
        mock_source = "// Relative path test"
        
        with patch("builtins.open", mock_open(read_data=mock_source)):
            with patch("os.path.exists", return_value=True):
                response = get_contract_source(request, project_facts)

        assert response.success is True
        assert response.file_path == "contracts/Child.sol"
        # Path should be relative as stored in the contract
        assert not os.path.isabs(response.file_path)

