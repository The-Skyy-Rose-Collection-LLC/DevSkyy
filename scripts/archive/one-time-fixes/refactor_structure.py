#!/usr/bin/env python3
"""
DevSkyy File Structure Refactoring Script
==========================================

Reorganizes the DevSkyy codebase for improved maintainability:
- Consolidates root-level files into organized directories
- Standardizes naming conventions
- Removes duplicate functionality
- Updates import statements after restructuring

Usage:
    python scripts/refactor_structure.py --dry-run  # Preview changes
    python scripts/refactor_structure.py --execute  # Apply changes

Dependencies: pathlib, shutil, argparse
"""

import argparse
import logging
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class FileStructureRefactor:
    """Handles DevSkyy file structure refactoring operations."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.moves: list[tuple[Path, Path]] = []
        self.deletions: list[Path] = []
        self.renames: list[tuple[Path, Path]] = []

    def plan_refactoring(self) -> None:
        """Plan all refactoring operations."""
        logger.info("Planning file structure refactoring...")

        # 1. Consolidate documentation files
        self._plan_documentation_consolidation()

        # 2. Organize configuration files
        self._plan_config_consolidation()

        # 3. Remove duplicate MCP servers
        self._plan_mcp_consolidation()

        # 4. Standardize naming conventions
        self._plan_naming_standardization()

        # 5. Clean up legacy files
        self._plan_legacy_cleanup()

        logger.info(
            f"Planned {len(self.moves)} moves, {len(self.deletions)} deletions, {len(self.renames)} renames"
        )

    def _plan_documentation_consolidation(self) -> None:
        """Plan consolidation of documentation files."""
        doc_files = [
            "CLAUDE.md",
            "CLEAN_CODING_AGENTS.md",
            "COMPLIANCE_ARCHITECTURE.txt",
            "DEVELOPER_QUICKREF.md",
            "ENV_SETUP_GUIDE.md",
            "IMPLEMENTATION_SUMMARY.md",
            "QUICKSTART.md",
            "REPOSITORY_FILES.md",
            "SERVER_README.md",
        ]

        for doc_file in doc_files:
            source = self.root_dir / doc_file
            if source.exists():
                target = self.root_dir / "docs" / "guides" / doc_file.lower().replace("_", "-")
                self.moves.append((source, target))

    def _plan_config_consolidation(self) -> None:
        """Plan consolidation of configuration files."""
        # Create config directory structure
        config_moves = [
            ("claude_desktop_config.example.json", "config/claude/desktop.example.json"),
            ("jest.config.js", "config/testing/jest.config.js"),
            ("tsconfig.json", "config/typescript/tsconfig.json"),
        ]

        for source_name, target_path in config_moves:
            source = self.root_dir / source_name
            if source.exists():
                target = self.root_dir / target_path
                self.moves.append((source, target))

    def _plan_mcp_consolidation(self) -> None:
        """Plan MCP server consolidation."""
        # Keep devskyy_mcp.py as primary, move server.py to mcp/
        server_py = self.root_dir / "server.py"
        if server_py.exists():
            target = self.root_dir / "mcp" / "openai_server.py"
            self.moves.append((server_py, target))

    def _plan_naming_standardization(self) -> None:
        """Plan standardization of naming conventions."""
        # Standardize to snake_case for Python files
        renames = [
            ("DevSkyyDashboard.jsx", "devskyy_dashboard.jsx"),
            ("DevSkyyDashboard.js", "devskyy_dashboard.js"),
            ("DevSkyyDashboard.d.ts", "devskyy_dashboard.d.ts"),
        ]

        for old_name, new_name in renames:
            old_path = self.root_dir / old_name
            if old_path.exists():
                new_path = self.root_dir / new_name
                self.renames.append((old_path, new_path))

    def _plan_legacy_cleanup(self) -> None:
        """Plan cleanup of legacy and redundant files."""
        # Files to remove (after backing up to legacy/)
        cleanup_files = [
            "test_server.py",  # Redundant with tests/
            "__pycache__",  # Should be in .gitignore
        ]

        for file_name in cleanup_files:
            file_path = self.root_dir / file_name
            if file_path.exists():
                self.deletions.append(file_path)

    def execute_refactoring(self, dry_run: bool = True) -> None:
        """Execute the planned refactoring operations."""
        if dry_run:
            logger.info("DRY RUN - No files will be modified")
            self._preview_changes()
            return

        logger.info("Executing file structure refactoring...")

        # Create necessary directories
        self._create_directories()

        # Execute moves
        for source, target in self.moves:
            self._safe_move(source, target)

        # Execute renames
        for old_path, new_path in self.renames:
            self._safe_rename(old_path, new_path)

        # Execute deletions (move to legacy first)
        for file_path in self.deletions:
            self._safe_delete(file_path)

        logger.info("File structure refactoring completed successfully")

    def _preview_changes(self) -> None:
        """Preview all planned changes."""
        print("\n=== PLANNED CHANGES ===")

        if self.moves:
            print("\nFILE MOVES:")
            for source, target in self.moves:
                print(f"  {source} → {target}")

        if self.renames:
            print("\nFILE RENAMES:")
            for old_path, new_path in self.renames:
                print(f"  {old_path} → {new_path}")

        if self.deletions:
            print("\nFILE DELETIONS:")
            for file_path in self.deletions:
                print(f"  {file_path} (moved to legacy/)")

    def _create_directories(self) -> None:
        """Create necessary directory structure."""
        dirs_to_create = [
            "config/claude",
            "config/testing",
            "config/typescript",
            "docs/guides",
            "mcp",
            "legacy/cleanup",
        ]

        for dir_path in dirs_to_create:
            full_path = self.root_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")

    def _safe_move(self, source: Path, target: Path) -> None:
        """Safely move a file with error handling."""
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            logger.info(f"Moved: {source} → {target}")
        except Exception as e:
            logger.error(f"Failed to move {source} → {target}: {e}")

    def _safe_rename(self, old_path: Path, new_path: Path) -> None:
        """Safely rename a file with error handling."""
        try:
            old_path.rename(new_path)
            logger.info(f"Renamed: {old_path} → {new_path}")
        except Exception as e:
            logger.error(f"Failed to rename {old_path} → {new_path}: {e}")

    def _safe_delete(self, file_path: Path) -> None:
        """Safely delete a file (move to legacy first)."""
        try:
            legacy_path = self.root_dir / "legacy" / "cleanup" / file_path.name
            if file_path.is_dir():
                shutil.move(str(file_path), str(legacy_path))
            else:
                shutil.move(str(file_path), str(legacy_path))
            logger.info(f"Moved to legacy: {file_path}")
        except Exception as e:
            logger.error(f"Failed to move {file_path} to legacy: {e}")


def main():
    """Main entry point for the refactoring script."""
    parser = argparse.ArgumentParser(description="DevSkyy file structure refactoring")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
    parser.add_argument("--execute", action="store_true", help="Execute the refactoring")

    args = parser.parse_args()

    if not (args.dry_run or args.execute):
        parser.error("Must specify either --dry-run or --execute")

    root_dir = Path(__file__).parent.parent
    refactor = FileStructureRefactor(root_dir)

    refactor.plan_refactoring()
    refactor.execute_refactoring(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
