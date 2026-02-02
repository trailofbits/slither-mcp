"""Tests for artifacts module - saving and loading ProjectFacts."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from slither_mcp.artifacts import (
    _normalize_paths,
    load_project_facts,
    save_project_facts,
    artifacts_exist,
)
from slither_mcp.types import (
    CACHE_SCHEMA_VERSION,
    CacheCorruptionError,
    ContractKey,
    ContractModel,
    FunctionCallees,
    ProjectFacts,
    compute_content_checksum,
)


@pytest.fixture
def empty_callees():
    """Empty FunctionCallees for test contracts."""
    return FunctionCallees(
        internal_callees=[],
        external_callees=[],
        library_callees=[],
        has_low_level_calls=False,
    )


@pytest.fixture
def simple_contract(empty_callees):
    """Simple contract with relative path."""
    key = ContractKey(contract_name="SimpleContract", path="contracts/Simple.sol")
    return ContractModel(
        name="SimpleContract",
        key=key,
        path="contracts/Simple.sol",
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[key],
        functions_declared={},
        functions_inherited={},
    )


@pytest.fixture
def contract_with_absolute_path(empty_callees):
    """Contract with absolute path (simulating legacy facts)."""
    key = ContractKey(contract_name="AbsoluteContract", path="contracts/Absolute.sol")
    return ContractModel(
        name="AbsoluteContract",
        key=key,
        path="/test/project/contracts/Absolute.sol",  # Absolute path
        is_abstract=False,
        is_fully_implemented=True,
        is_interface=False,
        is_library=False,
        directly_inherits=[],
        scopes=[key],
        functions_declared={},
        functions_inherited={},
    )


class TestNormalizePaths:
    """Tests for _normalize_paths function."""

    def test_normalize_absolute_path(self, contract_with_absolute_path):
        """Test that absolute paths are converted to relative paths."""
        key = contract_with_absolute_path.key
        project_facts = ProjectFacts(
            contracts={key: contract_with_absolute_path},
            project_dir="/test/project",
        )

        # Before normalization, path is absolute
        assert os.path.isabs(project_facts.contracts[key].path)

        # Normalize paths
        normalized = _normalize_paths(project_facts)

        # After normalization, path should be relative
        assert not os.path.isabs(normalized.contracts[key].path)
        assert normalized.contracts[key].path == "contracts/Absolute.sol"

    def test_normalize_already_relative_path(self, simple_contract):
        """Test that relative paths are left unchanged."""
        key = simple_contract.key
        project_facts = ProjectFacts(
            contracts={key: simple_contract},
            project_dir="/test/project",
        )

        original_path = project_facts.contracts[key].path
        normalized = _normalize_paths(project_facts)

        # Path should remain unchanged
        assert normalized.contracts[key].path == original_path

    def test_normalize_mixed_paths(self, simple_contract, contract_with_absolute_path):
        """Test normalization with mix of absolute and relative paths."""
        key1 = simple_contract.key
        key2 = contract_with_absolute_path.key
        project_facts = ProjectFacts(
            contracts={
                key1: simple_contract,
                key2: contract_with_absolute_path,
            },
            project_dir="/test/project",
        )

        normalized = _normalize_paths(project_facts)

        # Relative path unchanged
        assert normalized.contracts[key1].path == "contracts/Simple.sol"
        # Absolute path converted
        assert normalized.contracts[key2].path == "contracts/Absolute.sol"

    def test_normalize_empty_project(self):
        """Test normalization of empty project facts."""
        project_facts = ProjectFacts(
            contracts={},
            project_dir="/test/project",
        )

        normalized = _normalize_paths(project_facts)

        assert len(normalized.contracts) == 0


class TestSaveAndLoadProjectFacts:
    """Tests for saving and loading ProjectFacts with path handling."""

    def test_save_and_load_roundtrip(self, simple_contract):
        """Test that save and load preserves data correctly."""
        key = simple_contract.key
        original = ProjectFacts(
            contracts={key: simple_contract},
            project_dir="/test/project",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            save_project_facts(original, tmpdir)

            loaded = load_project_facts(tmpdir)

            assert loaded is not None
            assert len(loaded.contracts) == 1
            assert loaded.contracts[key].name == "SimpleContract"
            assert loaded.contracts[key].path == "contracts/Simple.sol"

    def test_load_normalizes_absolute_paths(self, contract_with_absolute_path):
        """Test that loading normalizes absolute paths in cached facts."""
        key = contract_with_absolute_path.key

        with tempfile.TemporaryDirectory() as tmpdir:
            # Manually create a project_facts.json with absolute path
            # ContractKey uses format: ContractName@path!with!slashes
            contract_key_str = "AbsoluteContract@contracts!Absolute.sol"
            data = {
                "contracts": {
                    contract_key_str: {
                        "name": "AbsoluteContract",
                        "key": {"contract_name": "AbsoluteContract", "path": "contracts/Absolute.sol"},
                        "path": "/test/project/contracts/Absolute.sol",  # Absolute path (legacy bug)
                        "is_abstract": False,
                        "is_fully_implemented": True,
                        "is_interface": False,
                        "is_library": False,
                        "directly_inherits": [],
                        "scopes": ["AbsoluteContract@contracts!Absolute.sol"],
                        "functions_declared": {},
                        "functions_inherited": {},
                        "state_variables": [],
                        "events": [],
                    }
                },
                "project_dir": "/test/project",
                "detector_results": {},
                "available_detectors": [],
            }

            # Compute checksum for the data
            data_str = json.dumps(data, sort_keys=True)
            checksum = compute_content_checksum(data_str)

            cache_data = {
                "_pydantic_type": {
                    "is_list": False,
                    "model_name": "ProjectFacts"
                },
                "_cache_version": CACHE_SCHEMA_VERSION,
                "_checksum": checksum,
                "data": data,
            }

            file_path = Path(tmpdir) / "project_facts.json"
            with open(file_path, "w") as f:
                json.dump(cache_data, f)

            # Load should normalize paths
            loaded = load_project_facts(tmpdir)

            assert loaded is not None
            # Path should be relative now
            contract = list(loaded.contracts.values())[0]
            assert contract.path == "contracts/Absolute.sol"
            assert not os.path.isabs(contract.path)

    def test_load_nonexistent_raises_error(self):
        """Test that loading from nonexistent path raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                load_project_facts(tmpdir)

    def test_artifacts_exist_true(self, simple_contract):
        """Test artifacts_exist returns True when file exists."""
        key = simple_contract.key
        facts = ProjectFacts(
            contracts={key: simple_contract},
            project_dir="/test/project",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            save_project_facts(facts, tmpdir)
            assert artifacts_exist(tmpdir) is True

    def test_artifacts_exist_false(self):
        """Test artifacts_exist returns False when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert artifacts_exist(tmpdir) is False

    def test_load_corrupted_json_raises_error(self):
        """Test that loading corrupted JSON raises CacheCorruptionError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "project_facts.json"
            with open(file_path, "w") as f:
                f.write("{ invalid json }")

            with pytest.raises(CacheCorruptionError):
                load_project_facts(tmpdir)

    def test_load_legacy_format_raises_error(self, simple_contract):
        """Test that legacy format without version info raises CacheCorruptionError."""
        key = simple_contract.key

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create data without the _pydantic_type wrapper (legacy format)
            direct_data = {
                "contracts": {
                    str(key): {
                        "name": "SimpleContract",
                        "key": {"contract_name": "SimpleContract", "path": "contracts/Simple.sol"},
                        "path": "contracts/Simple.sol",
                        "is_abstract": False,
                        "is_fully_implemented": True,
                        "is_interface": False,
                        "is_library": False,
                        "directly_inherits": [],
                        "scopes": [str(key)],
                        "functions_declared": {},
                        "functions_inherited": {},
                    }
                },
                "project_dir": "/test/project",
                "detector_results": {},
                "available_detectors": [],
            }

            file_path = Path(tmpdir) / "project_facts.json"
            with open(file_path, "w") as f:
                json.dump(direct_data, f)

            # Legacy format without version info should raise error
            with pytest.raises(CacheCorruptionError):
                load_project_facts(tmpdir)

    def test_save_creates_artifacts_directory(self, simple_contract):
        """Test that save_project_facts creates the artifacts directory if missing."""
        key = simple_contract.key
        facts = ProjectFacts(
            contracts={key: simple_contract},
            project_dir="/test/project",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "nested" / "artifacts"
            assert not nested_dir.exists()

            save_project_facts(facts, str(nested_dir))

            assert nested_dir.exists()
            assert (nested_dir / "project_facts.json").exists()

    def test_roundtrip_preserves_detector_data(self, simple_contract):
        """Test that detector_results and available_detectors survive roundtrip."""
        from slither_mcp.types import DetectorMetadata, DetectorResult, SourceLocation

        key = simple_contract.key
        detector_results = {
            "test-detector": [
                DetectorResult(
                    detector_name="test-detector",
                    check="test-detector",
                    impact="High",
                    confidence="Medium",
                    description="Test finding",
                    source_locations=[
                        SourceLocation(file_path="contracts/Test.sol", start_line=10, end_line=15)
                    ],
                )
            ]
        }
        available_detectors = [
            DetectorMetadata(
                name="test-detector",
                description="A test detector",
                impact="High",
                confidence="Medium",
            )
        ]

        original = ProjectFacts(
            contracts={key: simple_contract},
            project_dir="/test/project",
            detector_results=detector_results,
            available_detectors=available_detectors,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            save_project_facts(original, tmpdir)
            loaded = load_project_facts(tmpdir)

            assert loaded is not None
            assert "test-detector" in loaded.detector_results
            assert len(loaded.detector_results["test-detector"]) == 1
            assert loaded.detector_results["test-detector"][0].impact == "High"
            assert len(loaded.available_detectors) == 1
            assert loaded.available_detectors[0].name == "test-detector"


class TestNormalizePathsEdgeCases:
    """Additional edge case tests for _normalize_paths."""

    def test_normalize_is_idempotent(self, contract_with_absolute_path):
        """Test that normalizing twice gives the same result."""
        key = contract_with_absolute_path.key
        project_facts = ProjectFacts(
            contracts={key: contract_with_absolute_path},
            project_dir="/test/project",
        )

        normalized_once = _normalize_paths(project_facts)
        normalized_twice = _normalize_paths(normalized_once)

        assert normalized_once.contracts[key].path == normalized_twice.contracts[key].path
        assert normalized_twice.contracts[key].path == "contracts/Absolute.sol"

    def test_normalize_path_outside_project_dir(self, empty_callees):
        """Test normalization when absolute path is outside project_dir."""
        key = ContractKey(contract_name="ExternalContract", path="contracts/External.sol")
        contract = ContractModel(
            name="ExternalContract",
            key=key,
            path="/completely/different/path/External.sol",  # Not under project_dir
            is_abstract=False,
            is_fully_implemented=True,
            is_interface=False,
            is_library=False,
            directly_inherits=[],
            scopes=[key],
            functions_declared={},
            functions_inherited={},
        )

        project_facts = ProjectFacts(
            contracts={key: contract},
            project_dir="/test/project",
        )

        # Should still work - relpath will create a path with ../
        normalized = _normalize_paths(project_facts)

        # Path should be relative (possibly with ../)
        assert not os.path.isabs(normalized.contracts[key].path)

    def test_normalize_with_trailing_slash_in_project_dir(self, empty_callees):
        """Test normalization handles trailing slash in project_dir."""
        key = ContractKey(contract_name="Contract", path="contracts/Contract.sol")
        contract = ContractModel(
            name="Contract",
            key=key,
            path="/test/project/contracts/Contract.sol",
            is_abstract=False,
            is_fully_implemented=True,
            is_interface=False,
            is_library=False,
            directly_inherits=[],
            scopes=[key],
            functions_declared={},
            functions_inherited={},
        )

        project_facts = ProjectFacts(
            contracts={key: contract},
            project_dir="/test/project/",  # Trailing slash
        )

        normalized = _normalize_paths(project_facts)

        assert normalized.contracts[key].path == "contracts/Contract.sol"

    def test_normalize_deeply_nested_path(self, empty_callees):
        """Test normalization of deeply nested absolute paths."""
        key = ContractKey(contract_name="DeepContract", path="src/contracts/deep/nested/Deep.sol")
        contract = ContractModel(
            name="DeepContract",
            key=key,
            path="/test/project/src/contracts/deep/nested/Deep.sol",
            is_abstract=False,
            is_fully_implemented=True,
            is_interface=False,
            is_library=False,
            directly_inherits=[],
            scopes=[key],
            functions_declared={},
            functions_inherited={},
        )

        project_facts = ProjectFacts(
            contracts={key: contract},
            project_dir="/test/project",
        )

        normalized = _normalize_paths(project_facts)

        assert normalized.contracts[key].path == "src/contracts/deep/nested/Deep.sol"
