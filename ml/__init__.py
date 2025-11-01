"""ML Infrastructure - Model Registry, Caching, Explainability, Codex Integration"""

from .codex_integration import codex, CodexIntegration
from .codex_orchestrator import codex_orchestrator, CodexOrchestrator
from .explainability import explainer, ModelExplainer
from .model_registry import model_registry, ModelRegistry, ModelStage

# Optional Redis caching support
try:
    from redis_cache import RedisCache

    redis_cache = RedisCache()
except ImportError:
    RedisCache = None  # type: ignore
    redis_cache = None  # Optional dependency

__all__ = [
    "ModelRegistry",
    "ModelStage",
    "model_registry",
    "RedisCache",
    "redis_cache",
    "ModelExplainer",
    "explainer",
    "CodexIntegration",
    "codex",
    "CodexOrchestrator",
    "codex_orchestrator",
]
