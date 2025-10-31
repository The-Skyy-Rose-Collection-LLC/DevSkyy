"""FastAPI application setup."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import load_config

from .routes import router

# Load configuration
config = load_config()

# Create FastAPI app
app = FastAPI(
    title="Fashion AI Autonomous Commerce Platform",
    description="End-to-end autonomous fashion design and commerce system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "status": "online",
        "message": "Fashion AI Autonomous Commerce Platform",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "fashion-ai-api"}
