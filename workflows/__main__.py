"""
Workflow Module Entry Point
===========================

Enables running workflows as a module:
    python -m workflows run ci
"""

from workflows.cli import main

if __name__ == "__main__":
    main()
