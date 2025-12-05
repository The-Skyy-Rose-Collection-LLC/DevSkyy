"""
Compatibility shim for legacy tooling expecting a `config-3` module.

Some CI/coverage hooks reference `/workspace/config-3.py`.  The canonical
configuration lives in `config.py`, so this module simply re-exports the same
symbols to keep coverage and any historical imports satisfied without
duplicating logic.
"""

from config import (  # noqa: F401
    Config,
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
    config,
)
