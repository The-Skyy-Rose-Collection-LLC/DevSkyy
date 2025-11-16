"""DevSkyy Database Package"""

__version__ = "1.0.0"

# Re-export database components for easy imports
# This allows: from database import Base, engine, etc.
import sys
import os

# Add parent directory to path to import database.py
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import from database.py module (file in parent directory)
import importlib.util

spec = importlib.util.spec_from_file_location(
    "database_module", os.path.join(parent_dir, "database.py")
)
database_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(database_module)

# Re-export key components
Base = database_module.Base
engine = database_module.engine
AsyncSessionLocal = database_module.AsyncSessionLocal
get_db = database_module.get_db
init_db = database_module.init_db
close_db = database_module.close_db
DatabaseManager = database_module.DatabaseManager
db_manager = database_module.db_manager

__all__ = [
    "Base",
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "init_db",
    "close_db",
    "DatabaseManager",
    "db_manager",
]
