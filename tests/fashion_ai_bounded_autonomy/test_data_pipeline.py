"""
Unit Tests for Data Pipeline
Tests data ingestion, validation, and processing
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import json
import pandas as pd

from fashion_ai_bounded_autonomy.data_pipeline import DataPipeline


@pytest.fixture
def temp_dirs():
    """
    Provide a temporary dataflow.yaml path with a minimal pipeline configuration for tests.
    
    The created YAML contains a minimal `data_pipeline` configuration including
    `approved_sources`, `schemas`, and `inference_config`. The fixture yields the
    path to the generated `dataflow.yaml` and removes the temporary directory and
    file after the test completes.
    
    Returns:
        str: Filesystem path to the generated `dataflow.yaml`.
    """
    temp_dir = tempfile.mkdtemp()
    config_dir = Path(temp_dir) / "config"
    config_dir.mkdir()
    
    # Create minimal config
    config = {
        "data_pipeline": {
            "approved_sources": [
                {"type": "csv", "max_size_mb": 10},
                {"type": "json", "max_size_mb": 5}
            ],
            "schemas": {
                "test_schema": {
                    "required_fields": {
                        "id": "string",
                        "name": "string"
                    }
                }
            },
            "inference_config": {
                "models": {
                    "test_model": {
                        "path": "test_model.pkl",
                        "type": "sklearn"
                    }
                }
            }
        }
    }
    
    config_path = config_dir / "dataflow.yaml"
    import yaml
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    yield str(config_path)
    shutil.rmtree(temp_dir)


@pytest.fixture
def pipeline(temp_dirs):
    """
    Create a DataPipeline configured from the provided temporary config path.
    
    Parameters:
        temp_dirs (str | pathlib.Path): Path to the generated dataflow.yaml configuration file used to initialize the pipeline.
    
    Returns:
        DataPipeline: An instance of DataPipeline initialized with the given config_path.
    """
    return DataPipeline(config_path=temp_dirs)


class TestDataPipelineInitialization:
    """Test data pipeline initialization"""

    def test_initialization(self, temp_dirs):
        """Test basic initialization"""
        pipeline = DataPipeline(config_path=temp_dirs)
        
        assert pipeline.quarantine_path.exists()
        assert pipeline.validated_path.exists()
        assert pipeline.output_path.exists()

    def test_config_loaded(self, pipeline):
        """Test that configuration is loaded"""
        assert "approved_sources" in pipeline.config
        assert "schemas" in pipeline.config


class TestDataIngestion:
    """Test data ingestion functionality"""

    @pytest.mark.asyncio
    async def test_ingest_csv(self, pipeline):
        """Test ingesting CSV file"""
        # Create test CSV
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.write("id,name\n1,test\n2,test2\n")
        temp_file.close()
        
        result = await pipeline.ingest(temp_file.name, "csv")
        
        assert result["status"] == "ingested"
        assert result["source_type"] == "csv"
        assert "file_hash" in result
        
        Path(temp_file.name).unlink()

    @pytest.mark.asyncio
    async def test_ingest_json(self, pipeline):
        """Test ingesting JSON file"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump({"test": "data"}, temp_file)
        temp_file.close()
        
        result = await pipeline.ingest(temp_file.name, "json")
        
        assert result["status"] == "ingested"
        assert result["source_type"] == "json"
        
        Path(temp_file.name).unlink()

    @pytest.mark.asyncio
    async def test_ingest_unsupported_type(self, pipeline):
        """Test ingesting unsupported file type"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write("test")
        temp_file.close()
        
        result = await pipeline.ingest(temp_file.name, "unsupported")
        
        assert result["status"] == "error"
        
        Path(temp_file.name).unlink()


class TestDataValidation:
    """Test data validation functionality"""

    @pytest.mark.asyncio
    async def test_preprocess_valid_data(self, pipeline):
        """Test preprocessing valid data"""
        data = {"id": "123", "name": "test"}
        
        result = await pipeline.preprocess(data, "test_schema")
        
        assert result["status"] == "validated"
        assert "validated_file" in result

    @pytest.mark.asyncio
    async def test_preprocess_invalid_data(self, pipeline):
        """Test preprocessing invalid data"""
        data = {"name": "test"}  # Missing required 'id' field
        
        result = await pipeline.preprocess(data, "test_schema")
        
        assert result["status"] == "quarantined"
        assert "errors" in result


class TestInference:
    """Test model inference functionality"""

    @pytest.mark.asyncio
    async def test_inference_approved_model(self, pipeline):
        """Test inference with approved model"""
        data = {"test": "data"}
        
        result = await pipeline.inference(data, "test_model")
        
        assert result["status"] == "completed"
        assert result["model"] == "test_model"

    @pytest.mark.asyncio
    async def test_inference_unapproved_model(self, pipeline):
        """Test inference with unapproved model"""
        data = {"test": "data"}
        
        result = await pipeline.inference(data, "unapproved_model")
        
        assert result["status"] == "error"


class TestFileHashCalculation:
    """Test file hash calculation"""

    def test_calculate_hash(self, pipeline):
        """Test file hash calculation"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        temp_file.write("test content")
        temp_file.close()
        
        hash1 = pipeline._calculate_file_hash(Path(temp_file.name))
        hash2 = pipeline._calculate_file_hash(Path(temp_file.name))
        
        assert hash1 == hash2  # Same file should produce same hash
        assert len(hash1) == 64  # SHA-256 produces 64 hex characters
        
        Path(temp_file.name).unlink()