refactor / clean - main - py
"""
API module initialization for DevSkyy Platform.
"""
from fastapi import FastAPI

__version__ = "2.0.0"


def create_app() -> FastAPI:
    """Create and configure FastAPI application instance.

    Returns:
        FastAPI: Configured FastAPI application
    """
    app = FastAPI(
        title="The Skyy Rose Collection - DevSkyy Enhanced Platform",
        version=__version__,
        description="Production-grade AI-powered platform for luxury e-commerce",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    return app


"""DevSkyy API Package"""

__VERSION__ = "1.0.0"
main
