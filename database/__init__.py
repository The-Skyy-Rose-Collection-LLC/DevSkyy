"""DevSkyy Database Package

Re-exports database.py components for backward compatibility.
Since the database/ package shadows database.py, we import from
the module using importlib and re-export all components.
"""
import importlib.util
import sys
from pathlib import Path

__version__ = "1.0.0"

# Load database.py module directly from file to avoid circular import issues
_database_py_path = Path(__file__).parent.parent / "database.py"
_spec = importlib.util.spec_from_file_location("_database_module", _database_py_path)
_database_module = importlib.util.module_from_spec(_spec)
sys.modules["_database_module"] = _database_module
_spec.loader.exec_module(_database_module)

# Re-export all components from database.py
AsyncSessionLocal = _database_module.AsyncSessionLocal
Base = _database_module.Base
get_db = _database_module.get_db
init_db = _database_module.init_db
close_db = _database_module.close_db
DatabaseManager = _database_module.DatabaseManager
db_manager = _database_module.db_manager
engine = _database_module.engine
DATABASE_URL = _database_module.DATABASE_URL

__all__ = [
    "AsyncSessionLocal",
    "Base",
    "get_db",
    "init_db",
    "close_db",
    "DatabaseManager",
    "db_manager",
    "engine",
    "DATABASE_URL",
]
