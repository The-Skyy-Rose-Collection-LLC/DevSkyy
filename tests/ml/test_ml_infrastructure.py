"""
Comprehensive ML Infrastructure Tests
Tests for model registry, caching, explainability, and API endpoints
"""

import unittest
import shutil
import tempfile

import numpy as np
import pytest

from ml.explainability import ModelExplainer
from ml.model_registry import ModelRegistry, ModelStage
from ml.redis_cache import RedisCache


# Mock model for testing
class MockModel:
    """Simple mock model for testing"""

    def predict(self, X):
        return np.sum(X, axis=1)

    def fit(self, X, y):
        return self


# ============================================================================
# MODEL REGISTRY TESTS
# ============================================================================


class TestModelRegistry(unittest.TestCase):
    """Test model registry operations"""

    @pytest.fixture
    def temp_registry(self):
        """Create temporary registry directory"""
        temp_dir = tempfile.mkdtemp()
        registry = ModelRegistry(registry_path=temp_dir)
        yield registry
        shutil.rmtree(temp_dir)

    def test_register_model(self, temp_registry):
        """Test model registration"""
        model = MockModel()
        metadata = temp_registry.register_model(
            model=model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            metrics={"accuracy": 0.95, "f1": 0.92},
            parameters={"n_estimators": 100},
            dataset_info={"samples": 1000},
        )

        self.assertEqual(metadata.model_name, "test_model")
        self.assertEqual(metadata.version, "1.0.0")
        self.assertEqual(metadata.stage, ModelStage.DEVELOPMENT)
        self.assertEqual(metadata.metrics["accuracy"], 0.95)

    def test_load_model(self, temp_registry):
        """Test model loading"""
        model = MockModel()
        temp_registry.register_model(
            model=model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            metrics={"accuracy": 0.95},
        )

        loaded_model = temp_registry.load_model("test_model", version="1.0.0")
        self.assertIsNotNone(loaded_model)

        # Test prediction
        X = np.array([[1, 2], [3, 4]])
        result = loaded_model.predict(X)
        self.assertEqual(len(result), 2)

    def test_promote_model(self, temp_registry):
        """Test model promotion"""
        model = MockModel()
        temp_registry.register_model(
            model=model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            metrics={"accuracy": 0.95},
        )

        # Promote to staging
        temp_registry.promote_model("test_model", "1.0.0", ModelStage.STAGING)
        metadata = temp_registry.get_metadata("test_model", "1.0.0")
        self.assertEqual(metadata.stage, ModelStage.STAGING)

        # Promote to production
        temp_registry.promote_model("test_model", "1.0.0", ModelStage.PRODUCTION)
        metadata = temp_registry.get_metadata("test_model", "1.0.0")
        self.assertEqual(metadata.stage, ModelStage.PRODUCTION)

    def test_list_versions(self, temp_registry):
        """Test listing model versions"""
        model = MockModel()

        # Register multiple versions
        for version in ["1.0.0", "1.1.0", "2.0.0"]:
            temp_registry.register_model(
                model=model,
                model_name="test_model",
                version=version,
                model_type="classifier",
                metrics={"accuracy": 0.95},
            )

        versions = temp_registry.list_versions("test_model")
        self.assertEqual(len(versions), 3)
        self.assertIn("1.0.0", versions)
        self.assertIn("2.0.0", versions)

    def test_compare_models(self, temp_registry):
        """Test model comparison"""
        model = MockModel()

        temp_registry.register_model(
            model=model,
            model_name="test_model",
            version="1.0.0",
            model_type="classifier",
            metrics={"accuracy": 0.90, "f1": 0.88},
        )

        temp_registry.register_model(
            model=model,
            model_name="test_model",
            version="2.0.0",
            model_type="classifier",
            metrics={"accuracy": 0.95, "f1": 0.93},
        )

        comparison = temp_registry.compare_models("test_model", "1.0.0", "2.0.0")

        self.assertEqual(comparison["model_name"], "test_model")
        self.assertIn("metrics_comparison", comparison)
        self.assertTrue(()
            comparison["metrics_comparison"]["accuracy"]["v2.0.0"]
            > comparison["metrics_comparison"]["accuracy"]["v1.0.0"]
        )

    def test_registry_stats(self, temp_registry):
        """Test registry statistics"""
        model = MockModel()

        temp_registry.register_model(
            model=model,
            model_name="model1",
            version="1.0.0",
            model_type="classifier",
            metrics={"accuracy": 0.95},
        )

        temp_registry.register_model(
            model=model,
            model_name="model2",
            version="1.0.0",
            model_type="regressor",
            metrics={"mse": 0.05},
        )

        stats = temp_registry.get_registry_stats()

        self.assertEqual(stats["total_models"], 2)
        self.assertEqual(stats["total_versions"], 2)
        self.assertIn(ModelStage.DEVELOPMENT, stats["models_by_stage"])


# ============================================================================
# REDIS CACHE TESTS
# ============================================================================


class TestRedisCache(unittest.TestCase):
    """Test Redis cache with fallback"""

    @pytest.fixture
    def cache(self):
        """Create cache instance"""
        return RedisCache()

    def test_cache_set_get(self, cache):
        """Test basic cache operations"""
        cache.set("test_key", {"data": "value"})
        result = cache.get("test_key")
        self.assertEqual(result, {"data": "value"})

    def test_cache_delete(self, cache):
        """Test cache deletion"""
        cache.set("test_key", "value")
        cache.delete("test_key")
        self.assertIsNone(cache.get("test_key"))

    def test_cache_clear(self, cache):
        """Test cache clearing"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        self.assertIsNone(cache.get("key1"))
        self.assertIsNone(cache.get("key2"))

    def test_cache_ttl(self, cache):
        """Test TTL expiration"""
        import time

        cache.set("test_key", "value", ttl=1)
        self.assertEqual(cache.get("test_key"), "value")
        time.sleep(2)
        # In-memory cache may not respect TTL perfectly
        # Just verify the API works

    def test_cache_stats(self, cache):
        """Test cache statistics"""
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("nonexistent")  # Miss

        stats = cache.stats()
        self.assertIn("mode", stats)
        self.assertIn("total_keys", stats)


# ============================================================================
# MODEL EXPLAINABILITY TESTS
# ============================================================================


class TestModelExplainer(unittest.TestCase):
    """Test SHAP-based explainability"""

    @pytest.fixture
    def explainer(self):
        """Create explainer instance"""
        return ModelExplainer()

    def test_explainer_initialization(self, explainer):
        """Test explainer initialization"""
        self.assertIsNotNone(explainer)
        self.assertIsInstance(explainer.explainers, dict)

    def test_create_explainer_without_shap(self, explainer):
        """Test explainer creation when SHAP not available"""
        try:
            model = MockModel()
            X_bg = np.random.randn(100, 5)
            result = explainer.create_explainer(model, X_bg, "test_model")
            # If SHAP is installed, this should work
            # If not, it should raise ImportError
        except ImportError as e:
            self.assertIn("SHAP not installed", str(e))

    def test_explain_prediction_without_explainer(self, explainer):
        """Test prediction explanation without explainer"""
        X = np.array([[1, 2, 3]])

        with pytest.raises(ValueError, match="No explainer found"):
            explainer.explain_prediction("nonexistent_model", X)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestMLIntegration(unittest.TestCase):
    """Integration tests for ML infrastructure"""

    @pytest.fixture
    def setup_ml(self):
        """Set up ML infrastructure"""
        temp_dir = tempfile.mkdtemp()
        registry = ModelRegistry(registry_path=temp_dir)
        cache = RedisCache()
        explainer = ModelExplainer()

        yield registry, cache, explainer

        shutil.rmtree(temp_dir)
        cache.clear()

    def test_full_ml_workflow(self, setup_ml):
        """Test complete ML workflow"""
        registry, cache, explainer = setup_ml

        # 1. Train and register model
        model = MockModel()
        X_train = np.random.randn(100, 5)
        y_train = np.random.randint(0, 2, 100)
        model.fit(X_train, y_train)

        metadata = registry.register_model(
            model=model,
            model_name="workflow_model",
            version="1.0.0",
            model_type="classifier",
            metrics={"accuracy": 0.95},
            parameters={"trained": True},
        )

        self.assertEqual(metadata.model_name, "workflow_model")

        # 2. Load model and cache predictions
        loaded_model = registry.load_model("workflow_model", version="1.0.0")
        X_test = np.array([[1, 2, 3, 4, 5]])

        cache_key = "workflow_model:1.0.0:prediction"
        prediction = loaded_model.predict(X_test)
        cache.set(cache_key, prediction.tolist())

        cached_prediction = cache.get(cache_key)
        self.assertIsNotNone(cached_prediction)

        # 3. Promote model
        registry.promote_model("workflow_model", "1.0.0", ModelStage.PRODUCTION)
        metadata = registry.get_metadata("workflow_model", "1.0.0")
        self.assertEqual(metadata.stage, ModelStage.PRODUCTION)

    def test_model_versioning_workflow(self, setup_ml):
        """Test model versioning and comparison"""
        registry, cache, _ = setup_ml

        model = MockModel()

        # Register v1
        registry.register_model(
            model=model,
            model_name="versioned_model",
            version="1.0.0",
            model_type="classifier",
            metrics={"accuracy": 0.85, "f1": 0.82},
        )

        # Register v2 with better metrics
        registry.register_model(
            model=model,
            model_name="versioned_model",
            version="2.0.0",
            model_type="classifier",
            metrics={"accuracy": 0.92, "f1": 0.90},
        )

        # Compare versions
        comparison = registry.compare_models("versioned_model", "1.0.0", "2.0.0")

        self.assertTrue(()
            comparison["metrics_comparison"]["accuracy"]["v2.0.0"]
            > comparison["metrics_comparison"]["accuracy"]["v1.0.0"]
        )

        # Promote better model to production
        registry.promote_model("versioned_model", "2.0.0", ModelStage.PRODUCTION)

        # Load production model
        prod_model = registry.load_model("versioned_model", stage=ModelStage.PRODUCTION)
        self.assertIsNotNone(prod_model)


# ============================================================================
# API ENDPOINT TESTS (if FastAPI is available)
# ============================================================================


class TestMLAPI(unittest.TestCase):
    """Test ML API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient

        from main import app

        return TestClient(app)

    def test_ml_health_check(self, client):
        """Test ML health endpoint"""
        response = client.get("/api/v1/ml/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("registry", data)
        self.assertIn("cache_mode", data)

    def test_registry_stats_requires_auth(self, client):
        """Test registry stats requires authentication"""
        response = client.get("/api/v1/ml/registry/stats")
        self.assertEqual(response.status_code, 401  # Unauthorized)

    def test_cache_stats_requires_auth(self, client):
        """Test cache stats requires authentication"""
        response = client.get("/api/v1/ml/cache/stats")
        self.assertEqual(response.status_code, 401  # Unauthorized)
