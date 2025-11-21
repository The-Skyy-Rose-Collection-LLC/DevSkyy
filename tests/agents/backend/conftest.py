"""
Minimal conftest for backend agent tests.
Avoids importing dependencies that may not be available.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
