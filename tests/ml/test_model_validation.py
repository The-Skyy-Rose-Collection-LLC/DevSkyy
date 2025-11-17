import time

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from agent.ml_models.forecasting_engine import ForecastingEngine
from ml.model_registry import ModelRegistry


"""
ML Model Validation Tests
Tests for machine learning models, performance benchmarks, and validation
"""


class TestModelPerformance:
    """Test ML model performance and benchmarks"""

    def setup_method(self):
        """Setup test data"""
        # Generate synthetic dataset
        np.random.seed(42)
        self.n_samples = 1000
        self.n_features = 10

        self.X = np.random.randn(self.n_samples, self.n_features)
        self.y = 2 * self.X[:, 0] + 1.5 * self.X[:, 1] + 0.5 * np.random.randn(self.n_samples)

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42
        )

    @pytest.mark.benchmark
    def test_model_training_performance(self, benchmark):
        """Benchmark model training performance"""

        def train_model():
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(self.X_train, self.y_train)
            return model

        model = benchmark(train_model)

        # Verify model was trained
        assert hasattr(model, "estimators_")
        assert len(model.estimators_) == 100

    @pytest.mark.benchmark
    def test_model_prediction_performance(self, benchmark):
        """Benchmark model prediction performance"""
        # Train model first
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(self.X_train, self.y_train)

        def predict():
            return model.predict(self.X_test)

        predictions = benchmark(predict)

        # Verify predictions
        assert len(predictions) == len(self.X_test)
        assert not np.isnan(predictions).any()

    def test_model_accuracy(self):
        """Test model accuracy meets minimum requirements"""
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(self.X_train, self.y_train)

        predictions = model.predict(self.X_test)

        # Calculate metrics
        mse = mean_squared_error(self.y_test, predictions)
        r2 = r2_score(self.y_test, predictions)

        # Assert minimum performance requirements
        assert mse < 1.0, f"MSE too high: {mse}"
        assert r2 > 0.8, f"R² too low: {r2}"

    def test_model_training_time(self):
        """Test that model training completes within time limit"""
        start_time = time.time()

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(self.X_train, self.y_train)

        training_time = time.time() - start_time

        # Assert training time is reasonable
        assert training_time < 10.0, f"Training took too long: {training_time}s"

    def test_model_prediction_time(self):
        """Test that model prediction is fast enough"""
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(self.X_train, self.y_train)

        start_time = time.time()
        model.predict(self.X_test)
        prediction_time = time.time() - start_time

        # Assert prediction time is reasonable
        assert prediction_time < 1.0, f"Prediction took too long: {prediction_time}s"


class TestForecastingEngine:
    """Test the forecasting engine"""

    def setup_method(self):
        """Setup forecasting engine"""
        self.engine = ForecastingEngine()

        # Generate time series data
        dates = pd.date_range("2023-01-01", periods=365, freq="D")
        trend = np.linspace(100, 200, 365)
        seasonal = 10 * np.sin(2 * np.pi * np.arange(365) / 365.25 * 4)
        noise = np.random.normal(0, 5, 365)

        self.data = pd.DataFrame({"date": dates, "value": trend + seasonal + noise})

    def test_forecasting_engine_initialization(self):
        """Test forecasting engine initializes correctly"""
        assert self.engine is not None
        assert hasattr(self.engine, "models")

    def test_data_preprocessing(self):
        """Test data preprocessing functionality"""
        processed_data = self.engine._preprocess_data(self.data)

        assert processed_data is not None
        assert len(processed_data) > 0
        assert not processed_data.isnull().any().any()

    def test_model_training(self):
        """Test model training functionality"""
        # This would test the actual training method
        # For now, we'll test that the method exists and can be called
        assert hasattr(self.engine, "train_model")

        # Mock training
        result = self.engine.train_model(self.data, model_type="linear")
        assert result is not None

    def test_prediction_generation(self):
        """Test prediction generation"""
        # Train model first
        self.engine.train_model(self.data, model_type="linear")

        # Generate predictions
        predictions = self.engine.predict(steps=30)

        assert predictions is not None
        assert len(predictions) == 30
        assert not np.isnan(predictions).any()

    def test_forecast_accuracy(self):
        """Test forecast accuracy on known data"""
        # Split data for validation
        train_data = self.data.iloc[:-30]
        test_data = self.data.iloc[-30:]

        # Train on historical data
        self.engine.train_model(train_data, model_type="linear")

        # Predict the test period
        predictions = self.engine.predict(steps=30)
        actual = test_data["value"].values

        # Calculate accuracy metrics
        mse = mean_squared_error(actual, predictions)

        # Assert reasonable accuracy
        assert mse < 100, f"Forecast MSE too high: {mse}"


class TestModelRegistry:
    """Test the model registry functionality"""

    def setup_method(self):
        """Setup model registry"""
        self.registry = ModelRegistry()

    def test_model_registration(self):
        """Test model registration"""
        # Create a simple model
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        X = np.random.randn(100, 5)
        y = np.random.randn(100)
        model.fit(X, y)

        # Register the model
        model_id = self.registry.register_model(
            model=model,
            name="test_model",
            version="1.0.0",
            metadata={"type": "regression", "features": 5},
        )

        assert model_id is not None
        assert isinstance(model_id, str)

    def test_model_retrieval(self):
        """Test model retrieval from registry"""
        # Register a model first
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        X = np.random.randn(100, 5)
        y = np.random.randn(100)
        model.fit(X, y)

        model_id = self.registry.register_model(model=model, name="test_retrieval_model", version="1.0.0")

        # Retrieve the model
        retrieved_model = self.registry.get_model(model_id)

        assert retrieved_model is not None
        assert hasattr(retrieved_model, "predict")

    def test_model_versioning(self):
        """Test model versioning functionality"""
        # Register multiple versions of the same model
        for version in ["1.0.0", "1.1.0", "2.0.0"]:
            model = RandomForestRegressor(n_estimators=10, random_state=42)
            X = np.random.randn(100, 5)
            y = np.random.randn(100)
            model.fit(X, y)

            model_id = self.registry.register_model(model=model, name="versioned_model", version=version)

            assert model_id is not None

        # Test getting latest version
        latest_model = self.registry.get_model_by_name("versioned_model", version="latest")
        assert latest_model is not None

    def test_model_metadata(self):
        """Test model metadata storage and retrieval"""
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        X = np.random.randn(100, 5)
        y = np.random.randn(100)
        model.fit(X, y)

        metadata = {
            "type": "regression",
            "features": 5,
            "accuracy": 0.95,
            "training_data_size": 100,
        }

        model_id = self.registry.register_model(
            model=model, name="metadata_test_model", version="1.0.0", metadata=metadata
        )

        # Retrieve metadata
        retrieved_metadata = self.registry.get_model_metadata(model_id)

        assert retrieved_metadata is not None
        assert retrieved_metadata["type"] == "regression"
        assert retrieved_metadata["features"] == 5
        assert retrieved_metadata["accuracy"] == 0.95


class TestModelValidation:
    """Test model validation and quality checks"""

    def test_model_input_validation(self):
        """Test model input validation"""
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        X_train = np.random.randn(100, 5)
        y_train = np.random.randn(100)
        model.fit(X_train, y_train)

        # Test valid input
        X_valid = np.random.randn(10, 5)
        predictions = model.predict(X_valid)
        assert len(predictions) == 10

        # Test invalid input shape
        X_invalid = np.random.randn(10, 3)  # Wrong number of features
        with pytest.raises(ValueError):
            model.predict(X_invalid)

    def test_model_output_validation(self):
        """Test model output validation"""
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        X = np.random.randn(100, 5)
        y = np.random.randn(100)
        model.fit(X, y)

        # Make predictions
        X_test = np.random.randn(20, 5)
        predictions = model.predict(X_test)

        # Validate output
        assert len(predictions) == 20
        assert not np.isnan(predictions).any()
        assert not np.isinf(predictions).any()
        assert predictions.dtype == np.float64

    def test_model_robustness(self):
        """Test model robustness to edge cases"""
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        X = np.random.randn(100, 5)
        y = np.random.randn(100)
        model.fit(X, y)

        # Test with extreme values
        X_extreme = np.array([[1000, -1000, 0, 1e-10, 1e10]])
        predictions = model.predict(X_extreme)

        # Should still produce valid predictions
        assert len(predictions) == 1
        assert not np.isnan(predictions[0])
        assert not np.isinf(predictions[0])

    def test_model_consistency(self):
        """Test model prediction consistency"""
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        X = np.random.randn(100, 5)
        y = np.random.randn(100)
        model.fit(X, y)

        # Make predictions multiple times with same input
        X_test = np.random.randn(10, 5)
        predictions1 = model.predict(X_test)
        predictions2 = model.predict(X_test)

        # Should be identical
        np.testing.assert_array_equal(predictions1, predictions2)


class TestModelMonitoring:
    """Test model monitoring and drift detection"""

    def test_prediction_logging(self):
        """Test that predictions are logged for monitoring"""
        # This would test integration with logging system
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        X = np.random.randn(100, 5)
        y = np.random.randn(100)
        model.fit(X, y)

        X_test = np.random.randn(5, 5)
        predictions = model.predict(X_test)

        # In actual implementation, this would verify logging
        assert len(predictions) == 5

    def test_model_performance_tracking(self):
        """Test model performance tracking over time"""
        # This would test performance metrics collection
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        X = np.random.randn(100, 5)
        y = np.random.randn(100)
        model.fit(X, y)

        # Simulate performance tracking
        X_test = np.random.randn(20, 5)
        y_test = np.random.randn(20)
        predictions = model.predict(X_test)

        mse = mean_squared_error(y_test, predictions)
        r2 = r2_score(y_test, predictions)

        # Performance metrics should be reasonable
        assert isinstance(mse, float)
        assert isinstance(r2, float)
        assert not np.isnan(mse)
        assert not np.isnan(r2)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
