"""
Unit tests for DataPipeline
Tests data ingestion, validation, and processing
"""

import json
from pathlib import Path
import shutil
import tempfile

import pandas as pd
import pytest

from fashion_ai_bounded_autonomy.data_pipeline import DataPipeline


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_config_path(temp_data_dir):
    """Create temporary config file"""
    config = {
        "data_pipeline": {
            "approved_sources": [
                {"type": "csv", "path_pattern": "*.csv", "max_size_mb": 10},
                {"type": "json", "path_pattern": "*.json", "max_size_mb": 5},
                {"type": "image", "path_pattern": "*.jpg", "max_size_mb": 2},
                {"type": "parquet", "path_pattern": "*.parquet", "max_size_mb": 20},
            ],
            "schemas": {"test_schema": {"required_fields": {"id": "string", "value": "number"}}},
            "inference_config": {"models": {"test_model": {"type": "classification", "version": "1.0"}}},
        }
    }

    config_path = temp_data_dir / "dataflow.yaml"
    import yaml

    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return str(config_path)


@pytest.fixture
def data_pipeline(temp_config_path):
    """Create DataPipeline instance"""
    return DataPipeline(config_path=temp_config_path)


class TestDataPipelineInitialization:
    """Test DataPipeline initialization"""

    def test_init_creates_directories(self, data_pipeline):
        """Test that initialization creates required directories"""
        assert data_pipeline.quarantine_path.exists()
        assert data_pipeline.validated_path.exists()
        assert data_pipeline.output_path.exists()

    def test_init_loads_config(self, data_pipeline):
        """Test that initialization loads configuration"""
        assert data_pipeline.config is not None
        assert "approved_sources" in data_pipeline.config


class TestIngestCSV:
    """Test CSV data ingestion"""

    @pytest.mark.asyncio
    async def test_ingest_valid_csv(self, data_pipeline, temp_data_dir):
        """Test ingesting valid CSV file"""
        # Create test CSV file
        csv_file = temp_data_dir / "test.csv"
        df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        df.to_csv(csv_file, index=False)

        result = await data_pipeline.ingest(str(csv_file), "csv")

        assert result["status"] == "ingested"
        assert result["source_type"] == "csv"
        assert "file_hash" in result

    @pytest.mark.asyncio
    async def test_ingest_csv_with_large_file(self, data_pipeline, temp_data_dir):
        """Test rejecting CSV file that exceeds size limit"""
        # Mock a large file by patching stat
        csv_file = temp_data_dir / "large.csv"
        csv_file.write_text("header\ndata")

        # Patch file size check
        import os

        original_stat = os.stat

        def mock_stat(path):
            result = original_stat(path)
            if "large.csv" in str(path):
                # Mock 100MB file
                class MockStat:
                    st_size = 100 * 1024 * 1024

                return MockStat()
            return result

        with pytest.mock.patch("os.stat", side_effect=mock_stat):
            result = await data_pipeline.ingest(str(csv_file), "csv")
            assert result["status"] == "rejected"
            assert result["reason"] == "file_too_large"


class TestIngestJSON:
    """Test JSON data ingestion"""

    @pytest.mark.asyncio
    async def test_ingest_valid_json(self, data_pipeline, temp_data_dir):
        """Test ingesting valid JSON file"""
        json_file = temp_data_dir / "test.json"
        data = {"items": [{"id": 1, "value": 100}]}
        with open(json_file, "w") as f:
            json.dump(data, f)

        result = await data_pipeline.ingest(str(json_file), "json")

        assert result["status"] == "ingested"
        assert result["source_type"] == "json"

    @pytest.mark.asyncio
    async def test_ingest_invalid_json(self, data_pipeline, temp_data_dir):
        """Test ingesting invalid JSON file"""
        json_file = temp_data_dir / "invalid.json"
        json_file.write_text("not valid json {")

        result = await data_pipeline.ingest(str(json_file), "json")

        assert result["status"] == "error"


class TestPreprocessing:
    """Test data preprocessing and validation"""

    @pytest.mark.asyncio
    async def test_preprocess_valid_data(self, data_pipeline):
        """Test preprocessing valid data"""
        data = pd.DataFrame({"id": ["1", "2"], "value": [10, 20]})

        result = await data_pipeline.preprocess(data, "test_schema")

        assert result["status"] == "validated"
        assert "validated_file" in result

    @pytest.mark.asyncio
    async def test_preprocess_invalid_data_quarantined(self, data_pipeline):
        """Test that invalid data is quarantined"""
        # Missing required field 'value'
        data = pd.DataFrame({"id": ["1", "2"]})

        result = await data_pipeline.preprocess(data, "test_schema")

        assert result["status"] == "quarantined"
        assert "errors" in result
        assert "quarantine_file" in result

    @pytest.mark.asyncio
    async def test_preprocess_empty_dataframe(self, data_pipeline):
        """Test preprocessing empty dataframe"""
        data = pd.DataFrame()

        result = await data_pipeline.preprocess(data, "test_schema")

        assert result["status"] == "quarantined"

    @pytest.mark.asyncio
    async def test_preprocess_dict_data(self, data_pipeline):
        """Test preprocessing dictionary data"""
        data = {"id": "1", "value": 10}

        result = await data_pipeline.preprocess(data, "test_schema")

        assert result["status"] == "validated"


class TestInference:
    """Test model inference"""

    @pytest.mark.asyncio
    async def test_inference_with_approved_model(self, data_pipeline):
        """Test inference with approved model"""
        data = pd.DataFrame({"id": [1, 2], "value": [10, 20]})

        result = await data_pipeline.inference(data, "test_model")

        assert result["status"] == "completed"
        assert result["model"] == "test_model"
        assert "predictions" in result

    @pytest.mark.asyncio
    async def test_inference_with_unapproved_model(self, data_pipeline):
        """Test that unapproved model is rejected"""
        data = pd.DataFrame({"id": [1, 2], "value": [10, 20]})

        result = await data_pipeline.inference(data, "unapproved_model")

        assert result["status"] == "error"
        assert result["reason"] == "model_not_approved"


class TestFileHashing:
    """Test file integrity hashing"""

    def test_calculate_file_hash(self, data_pipeline, temp_data_dir):
        """Test file hash calculation"""
        test_file = temp_data_dir / "test.txt"
        test_file.write_text("test content")

        hash1 = data_pipeline._calculate_file_hash(test_file)
        hash2 = data_pipeline._calculate_file_hash(test_file)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex characters

    def test_different_files_different_hashes(self, data_pipeline, temp_data_dir):
        """Test that different files produce different hashes"""
        file1 = temp_data_dir / "file1.txt"
        file2 = temp_data_dir / "file2.txt"

        file1.write_text("content 1")
        file2.write_text("content 2")

        hash1 = data_pipeline._calculate_file_hash(file1)
        hash2 = data_pipeline._calculate_file_hash(file2)

        assert hash1 != hash2


class TestSchemaValidation:
    """Test schema validation logic"""

    def test_validate_schema_valid_data(self, data_pipeline):
        """Test validating data against schema"""
        data = {"id": "123", "value": 456}

        result = data_pipeline._validate_schema(data, "test_schema")

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_schema_missing_field(self, data_pipeline):
        """Test validation with missing required field"""
        data = {"id": "123"}  # Missing 'value'

        result = data_pipeline._validate_schema(data, "test_schema")

        assert result["valid"] is False
        assert any("value" in str(e) for e in result["errors"])

    def test_validate_schema_unknown_schema(self, data_pipeline):
        """Test validation with unknown schema"""
        data = {"id": "123", "value": 456}

        result = data_pipeline._validate_schema(data, "nonexistent_schema")

        assert result["valid"] is False


class TestOperationLogging:
    """Test operation logging"""

    @pytest.mark.asyncio
    async def test_log_operation(self, data_pipeline, temp_data_dir):
        """Test that operations are logged"""
        csv_file = temp_data_dir / "test.csv"
        df = pd.DataFrame({"id": [1], "value": [10]})
        df.to_csv(csv_file, index=False)

        await data_pipeline.ingest(str(csv_file), "csv")

        assert len(data_pipeline.processing_log) > 0
        assert data_pipeline.processing_log[0]["operation"] == "ingest"


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_ingest_nonexistent_file(self, data_pipeline):
        """Test ingesting non-existent file"""
        with pytest.raises(FileNotFoundError):
            await data_pipeline.ingest("/nonexistent/file.csv", "csv")

    @pytest.mark.asyncio
    async def test_ingest_unsupported_type(self, data_pipeline, temp_data_dir):
        """Test ingesting unsupported file type"""
        file_path = temp_data_dir / "test.txt"
        file_path.write_text("test")

        result = await data_pipeline.ingest(str(file_path), "unsupported")

        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_preprocess_with_list_data(self, data_pipeline):
        """Test preprocessing list of dictionaries"""
        data = [{"id": "1", "value": 10}, {"id": "2", "value": 20}]

        result = await data_pipeline.preprocess(data, "test_schema")

        assert result["status"] == "validated"
