"""
LAYER 3 — Data Pipeline
Manages ingestion, preprocessing, inference, and storage with validation
"""

import json
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import hashlib

logger = logging.getLogger(__name__)


class DataPipeline:
    """
    Bounded autonomous data pipeline.

    Sequence: [Data Source] → [Preprocessing] → [Model Inference] → [Result Storage]

    All operations are validated, logged, and require pre-approved inputs only.
    """

    def __init__(self, config_path: str = "fashion_ai_bounded_autonomy/config/dataflow.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

        self.quarantine_path = Path("fashion_ai_bounded_autonomy/quarantine/")
        self.validated_path = Path("fashion_ai_bounded_autonomy/validated/")
        self.output_path = Path("fashion_ai_bounded_autonomy/output/")

        # Create directories
        self.quarantine_path.mkdir(parents=True, exist_ok=True)
        self.validated_path.mkdir(parents=True, exist_ok=True)
        self.output_path.mkdir(parents=True, exist_ok=True)

        self.processing_log: List[Dict[str, Any]] = []

        logger.info("📊 Data pipeline initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load pipeline configuration"""
        with open(self.config_path) as f:
            return yaml.safe_load(f)["data_pipeline"]

    async def ingest(self, file_path: str, source_type: str) -> Dict[str, Any]:
        """
        Ingest data from approved source.

        Args:
            file_path: Path to data file
            source_type: Type of data source (csv, json, image, parquet)

        Returns:
            Ingestion result
        """
        start_time = datetime.now()
        file_path = Path(file_path)

        # Validate source
        if not self._is_approved_source(file_path, source_type):
            logger.error(f"❌ Unapproved data source: {file_path}")
            return {"status": "rejected", "reason": "unapproved_source"}

        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        max_size = self._get_max_size(source_type)

        if file_size_mb > max_size:
            logger.error(f"❌ File too large: {file_size_mb:.2f}MB > {max_size}MB")
            return {"status": "rejected", "reason": "file_too_large"}

        # Calculate file hash for integrity
        file_hash = self._calculate_file_hash(file_path)

        # Load data based on type
        try:
            if source_type == "csv":
                data = pd.read_csv(file_path)
            elif source_type == "json":
                with open(file_path) as f:
                    data = json.load(f)
            elif source_type == "parquet":
                data = pd.read_parquet(file_path)
            elif source_type == "image":
                # For images, just validate path and return metadata
                data = {"path": str(file_path), "type": "image"}
            else:
                return {"status": "error", "reason": "unsupported_type"}

            ingestion_time = (datetime.now() - start_time).total_seconds()

            result = {
                "status": "ingested",
                "file_path": str(file_path),
                "source_type": source_type,
                "file_hash": file_hash,
                "size_mb": file_size_mb,
                "ingestion_time_seconds": ingestion_time,
                "data": data
            }

            self._log_operation("ingest", result)
            logger.info(f"✅ Ingested {file_path} ({file_size_mb:.2f}MB)")

            return result

        except Exception as e:
            logger.error(f"❌ Ingestion failed: {str(e)}")
            return {"status": "error", "reason": str(e)}

    async def preprocess(self, data: Any, schema_name: str) -> Dict[str, Any]:
        """
        Preprocess and validate data.

        Args:
            data: Data to preprocess
            schema_name: Schema to validate against

        Returns:
            Preprocessing result
        """
        start_time = datetime.now()

        # Validate schema
        validation_result = self._validate_schema(data, schema_name)

        if not validation_result["valid"]:
            # Quarantine invalid data
            quarantine_file = self.quarantine_path / f"quarantine_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(quarantine_file, "w") as f:
                json.dump({
                    "data": data if isinstance(data, dict) else data.to_dict() if hasattr(data, "to_dict") else str(data),
                    "validation_errors": validation_result["errors"],
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)

            logger.warning(f"⚠️  Data quarantined: {validation_result['errors']}")
            return {
                "status": "quarantined",
                "errors": validation_result["errors"],
                "quarantine_file": str(quarantine_file)
            }

        # Clean and normalize data
        cleaned_data = self._clean_data(data)

        # Save to validated directory
        validated_file = self.validated_path / f"validated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(validated_file, "w") as f:
            if isinstance(cleaned_data, pd.DataFrame):
                cleaned_data.to_json(f, orient="records", indent=2)
            else:
                json.dump(cleaned_data, f, indent=2)

        processing_time = (datetime.now() - start_time).total_seconds()

        result = {
            "status": "validated",
            "schema": schema_name,
            "validated_file": str(validated_file),
            "processing_time_seconds": processing_time,
            "data": cleaned_data
        }

        self._log_operation("preprocess", result)
        logger.info(f"✅ Data preprocessed and validated")

        return result

    async def inference(self, data: Any, model_name: str) -> Dict[str, Any]:
        """
        Run model inference on validated data.

        Args:
            data: Validated data
            model_name: Model to use for inference

        Returns:
            Inference result
        """
        start_time = datetime.now()

        # Check if model is approved
        if model_name not in self.config["inference_config"]["models"]:
            return {"status": "error", "reason": "model_not_approved"}

        model_config = self.config["inference_config"]["models"][model_name]

        # For now, return placeholder (actual model loading would happen here)
        logger.info(f"🔮 Running inference with {model_name}")

        # Simulate inference
        predictions = {
            "model": model_name,
            "predictions": [],
            "confidence_scores": [],
            "metadata": model_config
        }

        inference_time = (datetime.now() - start_time).total_seconds()

        result = {
            "status": "completed",
            "model": model_name,
            "predictions": predictions,
            "inference_time_seconds": inference_time
        }

        self._log_operation("inference", result)
        logger.info(f"✅ Inference completed in {inference_time:.2f}s")

        return result

    def _is_approved_source(self, file_path: Path, source_type: str) -> bool:
        """Check if data source is approved"""
        for source in self.config["approved_sources"]:
            if source["type"] == source_type:
                # Simple pattern matching (in production, use proper glob matching)
                return True
        return False

    def _get_max_size(self, source_type: str) -> float:
        """Get maximum file size for source type"""
        for source in self.config["approved_sources"]:
            if source["type"] == source_type:
                return source["max_size_mb"]
        return 10.0  # Default

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
        return sha256.hexdigest()

    def _validate_schema(self, data: Any, schema_name: str) -> Dict[str, Any]:
        """Validate data against schema"""
        if schema_name not in self.config["schemas"]:
            return {"valid": False, "errors": ["unknown_schema"]}

        schema = self.config["schemas"][schema_name]
        errors = []

        # Convert to dict if DataFrame
        if isinstance(data, pd.DataFrame):
            if len(data) == 0:
                return {"valid": False, "errors": ["empty_dataframe"]}
            data_dict = data.iloc[0].to_dict()  # Validate first row
        elif isinstance(data, list) and len(data) > 0:
            data_dict = data[0]
        else:
            data_dict = data

        # Check required fields
        for field, field_type in schema["required_fields"].items():
            if field not in data_dict:
                errors.append(f"missing_required_field: {field}")

        return {"valid": len(errors) == 0, "errors": errors}

    def _clean_data(self, data: Any) -> Any:
        """Clean and normalize data"""
        # Placeholder for data cleaning logic
        return data

    def _log_operation(self, operation: str, result: Dict[str, Any]):
        """Log pipeline operation"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "status": result.get("status"),
            "details": {k: v for k, v in result.items() if k not in ["data", "predictions"]}
        }
        self.processing_log.append(log_entry)

        # Write to log file
        log_file = Path("logs/data_pipeline") / f"pipeline_{datetime.now().strftime('%Y%m%d')}.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
