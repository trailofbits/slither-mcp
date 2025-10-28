"""Integration tests for Slither detector functionality.

These tests actually run Slither on real Solidity contracts to verify that
detectors are properly registered, run, and their results are correctly parsed.
"""

import os
import tempfile
import pytest
from pathlib import Path

from slither_mcp.slither_wrapper import LazySlither
from slither_mcp.facts import get_project_facts


# Test contracts with known issues
REENTRANCY_CONTRACT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ReentrancyVulnerable {
    mapping(address => uint256) public balances;
    
    function withdraw() public {
        uint256 amount = balances[msg.sender];
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] = 0;
    }
    
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }
}
"""

UNINITIALIZED_STORAGE_CONTRACT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract UninitializedStorage {
    struct Data {
        uint256 value;
        address owner;
    }
    
    Data[] public dataArray;
    
    function addData() public {
        Data storage newData;  // Uninitialized storage pointer
        newData.value = 100;
        newData.owner = msg.sender;
        dataArray.push(newData);
    }
}
"""

LOW_LEVEL_CALLS_CONTRACT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract LowLevelCalls {
    function sendEth(address payable recipient, uint256 amount) public {
        recipient.call{value: amount}("");
    }
    
    function delegateToImpl(address impl, bytes memory data) public {
        impl.delegatecall(data);
    }
}
"""

SOLC_VERSION_CONTRACT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;  // Using buggy version

contract SolcVersion {
    uint256 public value;
    
    function setValue(uint256 newValue) public {
        value = newValue;
    }
}
"""


@pytest.fixture
def temp_solidity_project():
    """Create a temporary directory with a Solidity contract."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def write_contract(project_dir: str, filename: str, content: str):
    """Write a Solidity contract to the project directory."""
    filepath = Path(project_dir) / filename
    filepath.write_text(content)
    return str(filepath)


class TestDetectorIntegration:
    """Integration tests for detector functionality."""
    
    def test_reentrancy_detector_finds_vulnerability(self, temp_solidity_project):
        """Test that reentrancy detector finds the vulnerability."""
        # Write contract with reentrancy vulnerability
        contract_file = write_contract(temp_solidity_project, "Reentrancy.sol", REENTRANCY_CONTRACT)
        
        # Run Slither and get facts (pass the specific file, not directory)
        lazy_slither = LazySlither(contract_file)
        facts = get_project_facts(temp_solidity_project, lazy_slither)
        
        # Verify detector results were collected
        assert len(facts.detector_results) > 0, "No detector results found"
        
        # Check for reentrancy-related detectors
        reentrancy_detectors = [
            'reentrancy-eth', 'reentrancy-benign', 
            'reentrancy-no-eth', 'reentrancy-events'
        ]
        
        found_reentrancy = False
        for detector_name in reentrancy_detectors:
            if detector_name in facts.detector_results:
                results = facts.detector_results[detector_name]
                if results:  # Has findings
                    found_reentrancy = True
                    # Verify result structure
                    result = results[0]
                    assert result.detector_name == detector_name
                    assert result.impact in ['High', 'Medium', 'Low', 'Informational']
                    assert result.confidence in ['High', 'Medium', 'Low']
                    assert len(result.description) > 0
                    assert len(result.source_locations) > 0
                    
                    # Verify source location has correct fields
                    location = result.source_locations[0]
                    assert location.file_path
                    assert location.start_line > 0
                    assert location.end_line >= location.start_line
                    break
        
        assert found_reentrancy, "Reentrancy detector did not find the vulnerability"
    
    def test_low_level_calls_detector(self, temp_solidity_project):
        """Test that low-level calls detector finds issues."""
        contract_file = write_contract(temp_solidity_project, "LowLevel.sol", LOW_LEVEL_CALLS_CONTRACT)
        
        lazy_slither = LazySlither(contract_file)
        facts = get_project_facts(temp_solidity_project, lazy_slither)
        
        # Check for low-level-calls detector
        assert 'low-level-calls' in facts.detector_results, "Low-level-calls detector did not run"
        
        results = facts.detector_results.get('low-level-calls', [])
        assert len(results) > 0, "Low-level-calls detector found no issues"
        
        # Verify at least one result mentions call or delegatecall
        descriptions = [r.description.lower() for r in results]
        has_call_mention = any('call' in desc for desc in descriptions)
        assert has_call_mention, "Detector results don't mention low-level calls"
    
    def test_solc_version_detector(self, temp_solidity_project):
        """Test that solc-version detector finds issues."""
        contract_file = write_contract(temp_solidity_project, "Version.sol", SOLC_VERSION_CONTRACT)
        
        lazy_slither = LazySlither(contract_file)
        facts = get_project_facts(temp_solidity_project, lazy_slither)
        
        # Check for solc-version detector
        assert 'solc-version' in facts.detector_results, "Solc-version detector did not run"
        
        results = facts.detector_results.get('solc-version', [])
        # This detector should find issues with ^0.8.0
        assert len(results) > 0, "Solc-version detector found no issues"
        
        # Verify result mentions version
        result = results[0]
        assert result.impact == 'Informational'
        assert '0.8' in result.description or 'version' in result.description.lower()
    
    def test_detector_metadata_populated(self, temp_solidity_project):
        """Test that detector metadata is properly populated."""
        contract_file = write_contract(temp_solidity_project, "Simple.sol", SOLC_VERSION_CONTRACT)
        
        lazy_slither = LazySlither(contract_file)
        facts = get_project_facts(temp_solidity_project, lazy_slither)
        
        # Verify available_detectors is populated
        assert len(facts.available_detectors) > 50, "Not enough detectors registered"
        
        # Check metadata structure
        detector = facts.available_detectors[0]
        assert detector.name
        assert detector.description
        assert detector.impact in ['High', 'Medium', 'Low', 'Informational']
        assert detector.confidence in ['High', 'Medium', 'Low']
    
    def test_multiple_detectors_find_issues(self, temp_solidity_project):
        """Test that multiple detectors can find issues in the same contract."""
        # Contract with multiple issues
        multi_issue_contract = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract MultipleIssues {
    uint256 public value;
    
    function withdraw() public {
        (bool success, ) = msg.sender.call{value: address(this).balance}("");
        require(success);
        value = 0;
    }
    
    function externalCall(address target) public {
        target.call("");
    }
}
"""
        contract_file = write_contract(temp_solidity_project, "Multi.sol", multi_issue_contract)
        
        lazy_slither = LazySlither(contract_file)
        facts = get_project_facts(temp_solidity_project, lazy_slither)
        
        # Should have multiple detectors with findings
        detectors_with_results = [name for name, results in facts.detector_results.items() if results]
        assert len(detectors_with_results) >= 2, f"Expected multiple detectors, got {len(detectors_with_results)}"
    
    def test_detector_results_have_unique_checks(self, temp_solidity_project):
        """Test that different detectors produce results with their correct check names."""
        contract_file = write_contract(temp_solidity_project, "Test.sol", LOW_LEVEL_CALLS_CONTRACT)
        
        lazy_slither = LazySlither(contract_file)
        facts = get_project_facts(temp_solidity_project, lazy_slither)
        
        # Verify that detector_name matches the key in detector_results
        for detector_name, results in facts.detector_results.items():
            for result in results:
                assert result.detector_name == detector_name, \
                    f"Result detector_name '{result.detector_name}' doesn't match key '{detector_name}'"
                assert result.check == detector_name, \
                    f"Result check '{result.check}' doesn't match detector_name '{detector_name}'"
    
    def test_detector_source_locations_are_valid(self, temp_solidity_project):
        """Test that source locations in results are valid."""
        contract_file = write_contract(temp_solidity_project, "Source.sol", REENTRANCY_CONTRACT)
        
        lazy_slither = LazySlither(contract_file)
        facts = get_project_facts(temp_solidity_project, lazy_slither)
        
        # Find any detector with results
        for detector_name, results in facts.detector_results.items():
            if not results:
                continue
            
            for result in results:
                if result.source_locations:
                    for location in result.source_locations:
                        # Verify location fields
                        assert location.file_path, "Source location missing file_path"
                        assert location.start_line > 0, "Invalid start_line"
                        assert location.end_line > 0, "Invalid end_line"
                        assert location.end_line >= location.start_line, \
                            f"end_line ({location.end_line}) < start_line ({location.start_line})"
                    
                    # Found at least one valid location, test passes
                    return
        
        pytest.fail("No detector results with source locations found")


class TestDetectorIntegrationErrorHandling:
    """Test error handling in detector integration."""
    
    def test_invalid_contract_graceful_failure(self, temp_solidity_project):
        """Test that invalid Solidity contracts are handled gracefully."""
        invalid_contract = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Invalid {
    // Syntax error - missing semicolon
    uint256 public value
    
    function test() public {
        value = 1;
    }
}
"""
        write_contract(temp_solidity_project, "Invalid.sol", invalid_contract)
        
        # Should raise an error during Slither initialization
        with pytest.raises(Exception):
            lazy_slither = LazySlither(temp_solidity_project)
            get_project_facts(temp_solidity_project, lazy_slither)
    
    def test_empty_project_has_no_detector_results(self, temp_solidity_project):
        """Test that empty projects produce empty detector results."""
        # Create an empty but valid contract
        empty_contract = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Empty {
    // No code
}
"""
        contract_file = write_contract(temp_solidity_project, "Empty.sol", empty_contract)
        
        lazy_slither = LazySlither(contract_file)
        facts = get_project_facts(temp_solidity_project, lazy_slither)
        
        # Should have detector metadata but minimal results
        assert len(facts.available_detectors) > 50
        
        # Most detectors should have no findings for empty contract
        # (though some like solc-version might still trigger)
        total_findings = sum(len(results) for results in facts.detector_results.values())
        # Should have very few findings for an empty contract
        assert total_findings < 10, f"Empty contract triggered too many detectors: {total_findings}"

