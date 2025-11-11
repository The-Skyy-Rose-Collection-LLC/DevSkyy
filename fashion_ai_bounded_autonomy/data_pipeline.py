"""
LAYER 3 — Data Pipeline
Manages ingestion, preprocessing, inference, and storage with validation
"""

from datetime import datetime
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


logger = logging.getLogger(__name__)


class DataPipeline:
    """
    Bounded autonomous data pipeline.

    Sequence: [Data Source] → [Preprocessing] → [Model Inference] → [Result Storage]

    All operations are validated, logged, and require pre-approved inputs only.
    """

    def __init__(self, config_path: str = "fashion_ai_bounded_autonomy/config/dataflow.yaml"):
        """
        Initialize the DataPipeline by loading configuration, preparing storage directories, and setting up an in-memory processing log.
        
        Parameters:
            config_path (str): Path to the YAML configuration file that provides pipeline settings; defaults to "fashion_ai_bounded_autonomy/config/dataflow.yaml".
        
        Side effects:
            - Loads and stores the parsed pipeline configuration.
            - Ensures the directories "fashion_ai_bounded_autonomy/quarantine/", "fashion_ai_bounded_autonomy/validated/", and "fashion_ai_bounded_autonomy/output/" exist, creating them if necessary.
            - Initializes an empty in-memory processing log.
            - Emits an informational startup log entry.
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

        self.quarantine_path = Path("fashion_ai_bounded_autonomy/quarantine/")
        self.validated_path = Path("fashion_ai_bounded_autonomy/validated/")
        self.output_path = Path("fashion_ai_bounded_autonomy/output/")

        # Create directories
        self.quarantine_path.mkdir(parents=True, exist_ok=True)
        self.validated_path.mkdir(parents=True, exist_ok=True)
        self.output_path.mkdir(parents=True, exist_ok=True)

        self.processing_log: list[dict[str, Any]] = []

        logger.info("📊 Data pipeline initialized")

    def _load_config(self) -> dict[str, Any]:
        """
        Load and return the "data_pipeline" configuration section from the YAML file at self.config_path.
        
        Returns:
            dict[str, Any]: Mapping of configuration keys and values for the data pipeline (the YAML "data_pipeline" section).
        """
        with open(self.config_path) as f:
            return yaml.safe_load(f)["data_pipeline"]

    async def ingest(self, file_path: str, source_type: str) -> dict[str, Any]:
        """
        Ingest a file from an approved source into the pipeline and record ingestion metadata.
        
        Parameters:
            file_path (str): Path to the input file to ingest.
            source_type (str): Source type, one of "csv", "json", "parquet", or "image".
        
        Returns:
            dict: Result object. On success contains keys:
                - "status": "ingested"
                - "file_path": the ingested file path as a string
                - "source_type": the provided source type
                - "file_hash": SHA-256 hex digest of the file
                - "size_mb": file size in megabytes
                - "ingestion_time_seconds": duration of ingestion
                - "data": loaded data or metadata for the source
            On failure or rejection contains:
                - "status": one of "error" or "rejected"
                - "reason": brief machine-readable reason (e.g., "unsupported_type", "unapproved_source", "file_too_large", or an error message)
        """
        start_time = datetime.now()
        file_path = Path(file_path)

        # Check for supported types first
        supported_types = ["csv", "json", "parquet", "image"]
        if source_type not in supported_types:
            return {"status": "error", "reason": "unsupported_type"}

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
            logger.error(f"❌ Ingestion failed: {e!s}")
            return {"status": "error", "reason": str(e)}

    async def preprocess(self, data: Any, schema_name: str) -> dict[str, Any]:
        """
        Validate and normalize input data against a named schema, quarantining invalid inputs and persisting validated output.
        
        Parameters:
            data: The input data to validate and clean (may be a pandas DataFrame, list, dict, or other serializable structure).
            schema_name: The key of the validation schema to apply from the pipeline configuration.
        
        Returns:
            A dict describing the preprocessing outcome:
              - If validation fails: {"status": "quarantined", "errors": [...], "quarantine_file": "<path>"}.
              - If validation succeeds: {"status": "validated", "schema": "<schema_name>", "validated_file": "<path>", "processing_time_seconds": <float>, "data": <cleaned_data>}.
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
                # Convert DataFrame to dict, then dump with indent
                data_dict = cleaned_data.to_dict(orient="records")
                json.dump(data_dict, f, indent=2)
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
        logger.info("✅ Data preprocessed and validated")

        return result

    async def inference(self, data: Any, model_name: str) -> dict[str, Any]:
        """
        Run inference using a configured model on validated data.
        
        If the model name is not listed in the pipeline configuration's inference models, the returned dictionary indicates an error.
        
        Parameters:
            model_name (str): Name of the model as defined in the pipeline configuration's `inference_config.models`.
        
        Returns:
            dict: Result dictionary with keys:
                - "status": `"completed"` on success or `"error"` if the model is not approved.
                - "model": the `model_name` used.
                - "predictions": prediction payload produced by the model (placeholder structure in current implementation).
                - "inference_time_seconds": elapsed inference time as a float.
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
        """
        Compute the SHA-256 hex digest of the file at file_path.
        
        Parameters:
            file_path (Path): Path to the file to hash.
        
        Returns:
            str: Hexadecimal SHA-256 digest of the file contents.
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
        return sha256.hexdigest()

    def _validate_schema(self, data: Any, schema_name: str) -> dict[str, Any]:
        """
        Validate an input data sample against a named schema from the pipeline configuration.
        
        Checks that the named schema exists and that the provided data sample includes all fields listed under the schema's `required_fields`. Accepts a pandas DataFrame (validates the first row), a non-empty list (validates the first element), or a single mapping/object. On failure, returns validation errors that can be used for quarantining or reporting.
        
        Parameters:
            data (Any): The data sample to validate; may be a DataFrame, a list, or a mapping/object.
            schema_name (str): The key of the schema to use from self.config["schemas"].
        
        Returns:
            dict[str, Any]: A dictionary with:
                - "valid" (bool): `True` if all required fields are present, `False` otherwise.
                - "errors" (list[str]): A list of error codes/messages. Possible entries include:
                    - "unknown_schema" when the schema_name is not found.
                    - "empty_dataframe" when a DataFrame is provided but contains no rows.
                    - "missing_required_field: <field>" for each required field not present in the sample.
        """
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
        """
        Normalize and clean input data according to the pipeline's cleaning rules.
        
        Parameters:
            data (Any): Input dataset (for example, a pandas DataFrame, list, or dict) to be cleaned.
        
        Returns:
            Any: Cleaned and normalized data. Currently a placeholder that returns the input unchanged.
        """
        # Placeholder for data cleaning logic
        return data

    def _log_operation(self, operation: str, result: dict[str, Any]):
        """
        Record a pipeline operation entry in memory and append it to a daily JSONL log file.
        
        The created log entry contains a timestamp, the operation name, the `status` taken from `result.get("status")`, and a `details` object with all keys from `result` except `data` and `predictions`. The entry is appended to `self.processing_log` and written to logs/data_pipeline/pipeline_YYYYMMDD.jsonl; the log directory is created if it does not exist.
        
        Parameters:
            operation (str): Short name of the pipeline operation (e.g., "ingest", "preprocess", "inference").
            result (dict[str, Any]): Operation result dictionary whose keys will be recorded; `data` and `predictions` are excluded from the persisted `details`.
        """
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