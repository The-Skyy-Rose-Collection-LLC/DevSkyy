"""DevSkyy Database Package

Re-exports components from the root database.py module for backwards compatibility.
This allows imports like `from database import AsyncSessionLocal` to work whether
importing the package or the module.
"""

__version__ = "1.0.0"

import sys
from pathlib import Path

# Get the root directory
_root = Path(__file__).parent.parent

# We need to import the root database.py file, not this package
# Use importlib to load it with a different name to avoid recursion
import importlib.util

_database_py_path = _root / "database.py"

if _database_py_path.exists():
    _spec = importlib.util.spec_from_file_location("_root_database", _database_py_path)
    if _spec and _spec.loader:
        _root_db = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_root_db)

        # Re-export everything from the root database module
        AsyncSessionLocal = _root_db.AsyncSessionLocal
        Base = _root_db.Base
        DATABASE_URL = _root_db.DATABASE_URL
        DatabaseManager = _root_db.DatabaseManager
        db_manager = _root_db.db_manager
        engine = _root_db.engine
        get_db = _root_db.get_db
        init_db = _root_db.init_db
        close_db = _root_db.close_db

        __all__ = [
            "AsyncSessionLocal",
            "Base",
            "DATABASE_URL",
            "DatabaseManager",
            "db_manager",
            "engine",
            "get_db",
            "init_db",
            "close_db",
        ]
else:
    # Fallback if database.py doesn't exist
    __all__ = []
