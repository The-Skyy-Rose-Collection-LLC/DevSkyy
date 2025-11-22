#!/usr/bin/env python3
"""
DevSkyy Interactive Log Viewer
Enterprise-grade log viewing utility with filtering and real-time monitoring

Usage:
    python scripts/view_logs.py                     # Interactive menu
    python scripts/view_logs.py --file error        # View error log
    python scripts/view_logs.py --follow            # Follow logs in real-time
    python scripts/view_logs.py --level ERROR       # Filter by log level
    python scripts/view_logs.py --lines 100         # Show last 100 lines
    python scripts/view_logs.py --search "Exception" # Search for text
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


class Colors:
    """ANSI color codes for terminal output"""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Log levels
    DEBUG = "\033[36m"  # Cyan
    INFO = "\033[32m"  # Green
    WARNING = "\033[33m"  # Yellow
    ERROR = "\033[31m"  # Red
    CRITICAL = "\033[35m"  # Magenta

    # UI elements
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    OKGREEN = "\033[92m"
    FAIL = "\033[91m"


class LogViewer:
    """Interactive log viewer with filtering and search capabilities"""

    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.available_logs = self._discover_logs()

    def _discover_logs(self) -> dict:
        """Discover all available log files"""
        if not self.logs_dir.exists():
            return {}

        logs = {}
        for log_file in self.logs_dir.glob("*.log"):
            # Skip backup files (*.log.1, *.log.2, etc.)
            if not re.match(r".*\.log\.\d+$", str(log_file)):
                logs[log_file.stem] = log_file

        return logs

    def list_logs(self):
        """Display available log files"""
        print(f"\n{Colors.HEADER}{'=' * 70}{Colors.RESET}")
        print(
            f"{Colors.BOLD}{Colors.BLUE}📊 Available Log Files{Colors.RESET}"
        )
        print(f"{Colors.HEADER}{'=' * 70}{Colors.RESET}\n")

        if not self.available_logs:
            print(f"{Colors.WARNING}⚠️  No log files found in {self.logs_dir}/{Colors.RESET}\n")
            print(f"💡 Tip: Run the application first to generate logs\n")
            return

        for i, (name, path) in enumerate(self.available_logs.items(), 1):
            size = self._get_file_size(path)
            modified = self._get_modified_time(path)
            lines = self._count_lines(path)

            print(f"{Colors.BOLD}{i}. {name}.log{Colors.RESET}")
            print(f"   📁 Path: {path}")
            print(f"   📏 Size: {size}")
            print(f"   📝 Lines: {lines:,}")
            print(f"   🕒 Modified: {modified}\n")

    def view_log(
        self,
        log_name: str,
        lines: Optional[int] = None,
        level: Optional[str] = None,
        search: Optional[str] = None,
        follow: bool = False,
    ):
        """View log file with optional filtering"""
        if log_name not in self.available_logs:
            print(f"{Colors.FAIL}❌ Log file '{log_name}' not found{Colors.RESET}\n")
            self.list_logs()
            return

        log_path = self.available_logs[log_name]

        print(f"\n{Colors.HEADER}{'=' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}📖 Viewing: {log_path}{Colors.RESET}")
        if level:
            print(f"{Colors.DIM}🔍 Filtering: Level = {level}{Colors.RESET}")
        if search:
            print(f"{Colors.DIM}🔍 Searching: '{search}'{Colors.RESET}")
        print(f"{Colors.HEADER}{'=' * 70}{Colors.RESET}\n")

        if follow:
            self._follow_log(log_path, level, search)
        else:
            self._display_log(log_path, lines, level, search)

    def _display_log(
        self,
        log_path: Path,
        lines: Optional[int] = None,
        level: Optional[str] = None,
        search: Optional[str] = None,
    ):
        """Display log file content"""
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.readlines()

            # Apply filters
            if level:
                content = [line for line in content if level.upper() in line]

            if search:
                content = [line for line in content if search in line]

            # Get last N lines
            if lines:
                content = content[-lines:]

            # Display with colors
            for line in content:
                print(self._colorize_line(line), end="")

            print(
                f"\n{Colors.DIM}{'─' * 70}{Colors.RESET}"
            )
            print(
                f"{Colors.DIM}📊 Displayed {len(content):,} lines{Colors.RESET}\n"
            )

        except Exception as e:
            print(f"{Colors.FAIL}❌ Error reading log: {e}{Colors.RESET}\n")

    def _follow_log(
        self, log_path: Path, level: Optional[str] = None, search: Optional[str] = None
    ):
        """Follow log file in real-time (like tail -f)"""
        print(f"{Colors.INFO}👀 Following log file... (Ctrl+C to stop){Colors.RESET}\n")

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                # Go to end of file
                f.seek(0, 2)

                while True:
                    line = f.readline()
                    if line:
                        # Apply filters
                        if level and level.upper() not in line:
                            continue
                        if search and search not in line:
                            continue

                        print(self._colorize_line(line), end="")
                    else:
                        time.sleep(0.1)

        except KeyboardInterrupt:
            print(f"\n{Colors.INFO}✋ Stopped following log{Colors.RESET}\n")
        except Exception as e:
            print(f"\n{Colors.FAIL}❌ Error following log: {e}{Colors.RESET}\n")

    def _colorize_line(self, line: str) -> str:
        """Add color to log line based on level"""
        # Try to detect log level
        if "DEBUG" in line:
            return f"{Colors.DEBUG}{line}{Colors.RESET}"
        elif "INFO" in line:
            return f"{Colors.INFO}{line}{Colors.RESET}"
        elif "WARNING" in line:
            return f"{Colors.WARNING}{line}{Colors.RESET}"
        elif "ERROR" in line:
            return f"{Colors.ERROR}{line}{Colors.RESET}"
        elif "CRITICAL" in line:
            return f"{Colors.CRITICAL}{line}{Colors.RESET}"
        else:
            return line

    def _get_file_size(self, path: Path) -> str:
        """Get human-readable file size"""
        size = path.stat().st_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _get_modified_time(self, path: Path) -> str:
        """Get last modified time"""
        timestamp = path.stat().st_mtime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def _count_lines(self, path: Path) -> int:
        """Count lines in file"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def interactive_menu(self):
        """Display interactive menu for log selection"""
        while True:
            self.list_logs()

            if not self.available_logs:
                break

            print(f"{Colors.BOLD}Select an option:{Colors.RESET}")
            print("1-9) View log file")
            print("  f) Follow log in real-time")
            print("  s) Search logs")
            print("  q) Quit\n")

            choice = input(f"{Colors.BLUE}Your choice: {Colors.RESET}").strip().lower()

            if choice == "q":
                print(f"\n{Colors.INFO}👋 Goodbye!{Colors.RESET}\n")
                break
            elif choice == "f":
                self._follow_menu()
            elif choice == "s":
                self._search_menu()
            elif choice.isdigit() and 1 <= int(choice) <= len(self.available_logs):
                log_name = list(self.available_logs.keys())[int(choice) - 1]
                self.view_log(log_name)
                input(
                    f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}"
                )
            else:
                print(f"{Colors.FAIL}❌ Invalid choice{Colors.RESET}\n")

    def _follow_menu(self):
        """Menu for following logs"""
        self.list_logs()
        log_num = input(
            f"{Colors.BLUE}Enter log number to follow: {Colors.RESET}"
        ).strip()

        if log_num.isdigit() and 1 <= int(log_num) <= len(self.available_logs):
            log_name = list(self.available_logs.keys())[int(log_num) - 1]
            self.view_log(log_name, follow=True)
        else:
            print(f"{Colors.FAIL}❌ Invalid log number{Colors.RESET}\n")

    def _search_menu(self):
        """Menu for searching logs"""
        self.list_logs()
        log_num = input(
            f"{Colors.BLUE}Enter log number to search: {Colors.RESET}"
        ).strip()

        if not (log_num.isdigit() and 1 <= int(log_num) <= len(self.available_logs)):
            print(f"{Colors.FAIL}❌ Invalid log number{Colors.RESET}\n")
            return

        search_term = input(
            f"{Colors.BLUE}Enter search term: {Colors.RESET}"
        ).strip()

        if not search_term:
            print(f"{Colors.FAIL}❌ Search term cannot be empty{Colors.RESET}\n")
            return

        log_name = list(self.available_logs.keys())[int(log_num) - 1]
        self.view_log(log_name, search=search_term)
        input(f"\n{Colors.DIM}Press Enter to continue...{Colors.RESET}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="DevSkyy Interactive Log Viewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Interactive menu
  %(prog)s --file error                 # View error log
  %(prog)s --file devskyy --lines 100   # View last 100 lines
  %(prog)s --file error --follow        # Follow error log
  %(prog)s --level ERROR                # Show only errors
  %(prog)s --search "Exception"         # Search for text
  %(prog)s --file security --level WARNING --lines 50
        """,
    )

    parser.add_argument(
        "--file",
        "-f",
        help="Log file to view (without .log extension)",
    )

    parser.add_argument(
        "--lines",
        "-n",
        type=int,
        help="Number of lines to display (from end of file)",
    )

    parser.add_argument(
        "--level",
        "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Filter by log level",
    )

    parser.add_argument(
        "--search",
        "-s",
        help="Search for text in logs",
    )

    parser.add_argument(
        "--follow",
        "-F",
        action="store_true",
        help="Follow log file in real-time (like tail -f)",
    )

    parser.add_argument(
        "--logs-dir",
        default="logs",
        help="Logs directory (default: logs)",
    )

    args = parser.parse_args()

    # Create viewer
    viewer = LogViewer(args.logs_dir)

    # Interactive mode or direct view
    if args.file:
        viewer.view_log(
            args.file,
            lines=args.lines,
            level=args.level,
            search=args.search,
            follow=args.follow,
        )
    else:
        viewer.interactive_menu()


if __name__ == "__main__":
    main()
