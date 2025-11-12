# DevSkyy ML Subproject

## Overview

This directory contains machine learning models, training pipelines, and AI capabilities for the DevSkyy platform. The ML subproject is isolated to prevent heavy ML dependencies from affecting other deployment targets (Docker, Vercel, MCP).

## Structure

```
ml/
├── requirements.txt           # ML-specific Python dependencies (isolated)
├── __init__.py               # ML module initialization
├── auto_retrain.py           # Automated model retraining
├── codex_integration.py      # Codex AI integration
├── codex_orchestrator.py     # ML model orchestration
├── explainability.py         # Model explainability (SHAP, LIME)
├── model_registry.py         # Model versioning and registry
├── recommendation_engine.py  # Recommendation algorithms
├── redis_cache.py            # ML result caching
├── theme_templates.py        # Theme generation ML models
├── registry/                 # Model registry storage
└── README.md                 # This file
```

## Dependencies

The `requirements.txt` file contains ML-specific dependencies:

### Core ML Libraries
- **PyTorch**: 2.9.0 (latest stable with security fixes)
- **Transformers**: 4.57.1 (Hugging Face)
- **scikit-learn**: 1.5.2
- **XGBoost**: 2.1.3
- **LightGBM**: 4.6.0

### Computer Vision
- **OpenCV**: 4.11.0.86
- **Pillow**: 12.0.0
- **ImageHash**: 4.3.2

### Data Science
- **NumPy**: 2.3.4
- **Pandas**: 2.3.3
- **SciPy**: 1.14.1

### NLP
- **Sentence Transformers**: 3.4.1
- **TextBlob**: 0.18.0
- **VaderSentiment**: 3.3.2

### Model Utilities
- **SHAP**: Model explainability
- **LIME**: Local interpretability
- **PEFT**: Parameter-efficient fine-tuning

**Note**: These heavy dependencies are **excluded** from Docker production, MCP, and Vercel builds.

## ML Components

### 1. Model Registry (`model_registry.py`)
Centralized model versioning and management:
- Model registration and versioning
- Experiment tracking
- A/B testing support
- Performance metrics tracking

### 2. Auto Retrain (`auto_retrain.py`)
Automated model retraining pipeline:
- Scheduled retraining jobs
- Performance degradation detection
- Automatic model updates
- Rollback support

### 3. Recommendation Engine (`recommendation_engine.py`)
Fashion recommendation algorithms:
- Collaborative filtering
- Content-based recommendations
- Hybrid approaches
- Real-time personalization

### 4. Explainability (`explainability.py`)
Model interpretation and transparency:
- SHAP values for feature importance
- LIME for local explanations
- Model debugging tools
- Bias detection

### 5. Codex Integration (`codex_integration.py`, `codex_orchestrator.py`)
AI code generation and orchestration:
- Multi-model AI routing
- Task-specific model selection
- Performance optimization
- Cost management

## Installation

### For ML Development
```bash
# Install ML dependencies
pip install -r ml/requirements.txt
```

### For Production Deployment (Lightweight)
```bash
# Use production requirements (excludes heavy ML)
pip install -r requirements-production.txt
```

## Usage

### Model Training
```python
from ml.auto_retrain import AutoRetrainScheduler

scheduler = AutoRetrainScheduler()
await scheduler.schedule_retrain(
    model_name="fashion_classifier",
    schedule="daily",
    min_performance_threshold=0.85
)
```

### Inference
```python
from ml.recommendation_engine import RecommendationEngine

recommender = RecommendationEngine()
recommendations = await recommender.get_recommendations(
    user_id="user123",
    context={"category": "dresses", "price_range": "luxury"},
    limit=10
)
```

### Model Registry
```python
from ml.model_registry import ModelRegistry

registry = ModelRegistry()

# Register model
await registry.register_model(
    name="price_optimizer_v2",
    version="2.1.0",
    framework="pytorch",
    metrics={"accuracy": 0.92, "f1": 0.89}
)

# Load model
model = await registry.load_model("price_optimizer_v2", version="latest")
```

### Explainability
```python
from ml.explainability import ModelExplainer

explainer = ModelExplainer(model)
explanation = await explainer.explain_prediction(
    input_data=product_features,
    method="shap"  # or "lime"
)
```

## Testing

### Run ML Tests
```bash
# Run all ML tests
pytest tests/ml/ -v

# Run specific model tests
pytest tests/ml/test_recommendation_engine.py -v

# With coverage
pytest tests/ml/ --cov=ml --cov-report=html
```

### Performance Benchmarks
```bash
# Run performance benchmarks
pytest tests/ml/test_performance.py --benchmark
```

## CI/CD Integration

ML workflows are automated via GitHub Actions:
- Workflow: `.github/workflows/ml.yml`
- Model training: Triggered on schedule or manually
- Model validation: Automated testing on new models
- Model deployment: Automated registry updates

## Model Deployment

### Containerized ML Inference
```dockerfile
# Use ML-specific Dockerfile
FROM python:3.11-slim

COPY ml/requirements.txt .
RUN pip install -r requirements.txt

COPY ml/ /app/ml/
CMD ["python", "-m", "uvicorn", "ml.inference_server:app"]
```

### Serverless ML (Excluded from Vercel)
For serverless deployments, use lightweight model proxies:
- Call hosted ML endpoints (AWS SageMaker, Azure ML)
- Use model APIs (OpenAI, Anthropic)
- Deploy models separately from main app

## Performance Optimization

### Model Quantization
```python
# Reduce model size for faster inference
from ml.optimization import quantize_model

quantized_model = quantize_model(model, dtype="int8")
```

### Batch Inference
```python
# Process multiple predictions efficiently
predictions = await model.predict_batch(inputs, batch_size=32)
```

### Caching
```python
# Cache ML predictions
from ml.redis_cache import MLCache

cache = MLCache()
cached_result = await cache.get_or_compute(
    key=f"prediction_{input_hash}",
    compute_fn=lambda: model.predict(input_data),
    ttl=3600
)
```

## Monitoring

### Model Performance Tracking
- Accuracy degradation alerts
- Prediction latency monitoring
- Resource usage tracking
- A/B test results

### Metrics
```python
from ml.monitoring import MLMetrics

metrics = MLMetrics()
await metrics.log_prediction(
    model_name="classifier",
    input_features=features,
    prediction=output,
    actual=ground_truth,
    latency_ms=45.2
)
```

## Best Practices

1. **Version Control**: Track all model versions in registry
2. **Isolation**: Keep ML dependencies separate from core app
3. **Testing**: Validate models before production deployment
4. **Monitoring**: Track model performance continuously
5. **Explainability**: Provide interpretable predictions
6. **Security**: Sanitize inputs, validate outputs
7. **Scalability**: Use batch inference for efficiency
8. **Caching**: Cache expensive model predictions

## Troubleshooting

### CUDA/GPU Issues
```bash
# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"

# Use CPU fallback
export CUDA_VISIBLE_DEVICES=""
```

### Memory Issues
```bash
# Reduce batch size
# Use model quantization
# Enable gradient checkpointing for training
```

### Import Errors
```bash
# Ensure ML dependencies are installed
pip install -r ml/requirements.txt

# Check PyTorch installation
python -c "import torch; print(torch.__version__)"
```

## Related Documentation

- [ML Models Documentation](/docs/ml/)
- [Model Registry Guide](/docs/model_registry.md)
- [AI Integration](/AGENTS.md)
- [Enterprise ML Features](/ENTERPRISE_README.md)
