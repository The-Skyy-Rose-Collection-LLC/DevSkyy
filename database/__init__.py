"""DevSkyy Database Package

Import Note: This package re-exports database.py components.
Due to module naming (database package vs database.py file),
imports from this package should use absolute imports.
"""

__version__ = "1.0.0"

#  Note: Import components from database.py module (not this package)
# Tests should import directly: from database import AsyncSessionLocal
# Or use: import database; database.AsyncSessionLocal

__all__ = []
