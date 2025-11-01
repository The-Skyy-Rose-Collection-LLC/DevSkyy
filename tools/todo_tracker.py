from datetime import datetime
from pathlib import Path
import json
import os
import re
import sys

        import hashlib
    import argparse
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Set

#!/usr/bin/env python3
"""
DevSkyy TODO Tracking System

A comprehensive system for tracking, managing, and reporting on TODO items,
technical debt, and development tasks across the DevSkyy codebase.
"""

class Priority(Enum):
    """Priority levels for TODO items"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class Status(Enum):
    """Status of TODO items"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"

class Category(Enum):
    """Categories of TODO items"""
    BUG = "bug"
    FEATURE = "feature"
    REFACTOR = "refactor"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ACCESSIBILITY = "accessibility"
    SEO = "seo"
    TECHNICAL_DEBT = "technical_debt"

@dataclass
class TodoItem:
    """Represents a single TODO item"""
    id: str
    title: str
    description: str
    file_path: str
    line_number: int
    priority: Priority
    category: Category
    status: Status
    created_date: str
    updated_date: str
    assignee: Optional[str] = None
    estimated_hours: Optional[float] = None
    tags: List[str] = None
    related_issues: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.related_issues is None:
            self.related_issues = []

class TodoTracker:
    """Main TODO tracking system"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.todo_file = self.project_root / "TODO_TRACKING.json"
        self.todos: Dict[str, TodoItem] = {}
        self.load_todos()
    
    def scan_codebase(self) -> List[TodoItem]:
        """
        Scan the entire codebase for TODO comments and create TodoItem objects.
        
        Returns:
            List[TodoItem]: List of discovered TODO items
        """
        discovered_todos = []
        
        # Patterns to match different types of TODO comments
        todo_patterns = [
            (r'#\s*TODO:?\s*(.+)', Category.FEATURE),
            (r'#\s*FIXME:?\s*(.+)', Category.BUG),
            (r'#\s*HACK:?\s*(.+)', Category.TECHNICAL_DEBT),
            (r'#\s*XXX:?\s*(.+)', Category.TECHNICAL_DEBT),
            (r'#\s*NOTE:?\s*(.+)', Category.DOCUMENTATION),
            (r'#\s*BUG:?\s*(.+)', Category.BUG),
            (r'#\s*SECURITY:?\s*(.+)', Category.SECURITY),
            (r'#\s*PERFORMANCE:?\s*(.+)', Category.PERFORMANCE),
            (r'#\s*REFACTOR:?\s*(.+)', Category.REFACTOR),
            (r'#\s*TEST:?\s*(.+)', Category.TESTING),
        ]
        
        # File extensions to scan
        extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss', '.md'}
        
        for file_path in self.project_root.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix in extensions and
                not any(part.startswith('.') for part in file_path.parts) and
                'node_modules' not in str(file_path) and
                '__pycache__' not in str(file_path)):
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        for pattern, category in todo_patterns:
                            match = re.search(pattern, line, re.IGNORECASE)
                            if match:
                                todo_text = match.group(1).strip()
                                
                                # Generate unique ID
                                todo_id = self._generate_todo_id(file_path, line_num, todo_text)
                                
                                # Skip if already exists
                                if todo_id in self.todos:
                                    continue
                                
                                # Determine priority from keywords
                                priority = self._determine_priority(todo_text)
                                
                                todo_item = TodoItem(
                                    id=todo_id,
                                    title=todo_text[:100] + "..." if len(todo_text) > 100 else todo_text,
                                    description=todo_text,
                                    file_path=str(file_path.relative_to(self.project_root)),
                                    line_number=line_num,
                                    priority=priority,
                                    category=category,
                                    status=Status.OPEN,
                                    created_date=datetime.now().isoformat(),
                                    updated_date=datetime.now().isoformat()
                                )
                                
                                discovered_todos.append(todo_item)
                                
                except Exception as e:
                    logger.info(f"Error scanning {file_path}: {e}")
                    continue
        
        return discovered_todos
    
    def _generate_todo_id(self, file_path: Path, line_num: int, text: str) -> str:
        """Generate a unique ID for a TODO item"""
        content = f"{file_path}:{line_num}:{text[:50]}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def _determine_priority(self, text: str) -> Priority:
        """Determine priority based on keywords in the TODO text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['critical', 'urgent', 'asap', 'immediately']):
            return Priority.CRITICAL
        elif any(word in text_lower for word in ['important', 'high', 'soon', 'security']):
            return Priority.HIGH
        elif any(word in text_lower for word in ['medium', 'moderate', 'eventually']):
            return Priority.MEDIUM
        elif any(word in text_lower for word in ['low', 'minor', 'nice to have', 'someday']):
            return Priority.LOW
        else:
            return Priority.MEDIUM
    
    def add_todo(self, todo_item: TodoItem) -> None:
        """Add a new TODO item"""
        self.todos[todo_item.id] = todo_item
        self.save_todos()
    
    def update_todo(self, todo_id: str, **kwargs) -> bool:
        """Update an existing TODO item"""
        if todo_id not in self.todos:
            return False
        
        todo = self.todos[todo_id]
        for key, value in kwargs.items():
            if hasattr(todo, key):
                setattr(todo, key, value)
        
        todo.updated_date = datetime.now().isoformat()
        self.save_todos()
        return True
    
    def complete_todo(self, todo_id: str) -> bool:
        """Mark a TODO item as completed"""
        return self.update_todo(todo_id, status=Status.COMPLETED)
    
    def delete_todo(self, todo_id: str) -> bool:
        """Delete a TODO item"""
        if todo_id in self.todos:
            del self.todos[todo_id]
            self.save_todos()
            return True
        return False
    
    def get_todos_by_status(self, status: Status) -> List[TodoItem]:
        """Get all TODO items with a specific status"""
        return [todo for todo in self.todos.values() if todo.status == status]
    
    def get_todos_by_priority(self, priority: Priority) -> List[TodoItem]:
        """Get all TODO items with a specific priority"""
        return [todo for todo in self.todos.values() if todo.priority == priority]
    
    def get_todos_by_category(self, category: Category) -> List[TodoItem]:
        """Get all TODO items in a specific category"""
        return [todo for todo in self.todos.values() if todo.category == category]
    
    def get_todos_by_file(self, file_path: str) -> List[TodoItem]:
        """Get all TODO items in a specific file"""
        return [todo for todo in self.todos.values() if todo.file_path == file_path]
    
    def search_todos(self, query: str) -> List[TodoItem]:
        """Search TODO items by text"""
        query_lower = query.lower()
        return [
            todo for todo in self.todos.values()
            if query_lower in todo.title.lower() or query_lower in todo.description.lower()
        ]
    
    def generate_report(self) -> Dict:
        """Generate a comprehensive TODO report"""
        total_todos = len(self.todos)
        
        if total_todos == 0:
            return {
                "summary": "No TODO items found",
                "total": 0,
                "by_status": {},
                "by_priority": {},
                "by_category": {},
                "by_file": {}
            }
        
        # Count by status
        by_status = {}
        for status in Status:
            count = len(self.get_todos_by_status(status))
            if count > 0:
                by_status[status.value] = count
        
        # Count by priority
        by_priority = {}
        for priority in Priority:
            count = len(self.get_todos_by_priority(priority))
            if count > 0:
                by_priority[priority.value] = count
        
        # Count by category
        by_category = {}
        for category in Category:
            count = len(self.get_todos_by_category(category))
            if count > 0:
                by_category[category.value] = count
        
        # Count by file
        by_file = {}
        for todo in self.todos.values():
            by_file[todo.file_path] = by_file.get(todo.file_path, 0) + 1
        
        return {
            "generated_at": datetime.now().isoformat(),
            "total": total_todos,
            "by_status": by_status,
            "by_priority": by_priority,
            "by_category": by_category,
            "by_file": dict(sorted(by_file.items(), key=lambda x: x[1], reverse=True)),
            "high_priority_items": [
                asdict(todo) for todo in self.get_todos_by_priority(Priority.CRITICAL) +
                self.get_todos_by_priority(Priority.HIGH)
            ]
        }
    
    def save_todos(self) -> None:
        """Save TODO items to JSON file"""
        data = {
            "todos": {todo_id: asdict(todo) for todo_id, todo in self.todos.items()},
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.todo_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_todos(self) -> None:
        """Load TODO items from JSON file"""
        if not self.todo_file.exists():
            return
        
        try:
            with open(self.todo_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for todo_id, todo_data in data.get("todos", {}).items():
                # Convert string enums back to enum objects
                todo_data['priority'] = Priority(todo_data['priority'])
                todo_data['category'] = Category(todo_data['category'])
                todo_data['status'] = Status(todo_data['status'])
                
                self.todos[todo_id] = TodoItem(**todo_data)
                
        except Exception as e:
            logger.info(f"Error loading TODO file: {e}")
    
    def sync_with_codebase(self) -> Dict[str, int]:
        """
        Synchronize TODO tracking with actual codebase.
        
        Returns:
            Dict[str, int]: Statistics about sync operation
        """
        # Discover new TODOs
        discovered = self.scan_codebase()
        
        # Add new TODOs
        new_count = 0
        for todo in discovered:
            if todo.id not in self.todos:
                self.add_todo(todo)
                new_count += 1
        
        # Mark TODOs as completed if they no longer exist in code
        completed_count = 0
        for todo_id, todo in list(self.todos.items()):
            if todo.status == Status.OPEN:
                # Check if TODO still exists in the file
                try:
                    file_path = self.project_root / todo.file_path
                    if file_path.exists():
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        
                        if (todo.line_number <= len(lines) and)
                            todo.description not in lines[todo.line_number - 1]):
                            # TODO no longer exists, mark as completed
                            self.update_todo(todo_id, status=Status.COMPLETED)
                            completed_count += 1
                    else:
                        # File no longer exists, mark as completed
                        self.update_todo(todo_id, status=Status.COMPLETED)
                        completed_count += 1
                        
                except Exception as e:
                    logger.info(f"Error checking TODO {todo_id}: {e}")
        
        return {
            "new_todos": new_count,
            "completed_todos": completed_count,
            "total_todos": len(self.todos)
        }

def main():
    """Main CLI interface for TODO tracker"""
    
    parser = argparse.ArgumentParser(description="DevSkyy TODO Tracking System")
    parser.add_argument("command", choices=["scan", "report", "sync", "list"], 
                       help="Command to execute")
    parser.add_argument("--priority", choices=[p.value for p in Priority],
                       help="Filter by priority")
    parser.add_argument("--status", choices=[s.value for s in Status],
                       help="Filter by status")
    parser.add_argument("--category", choices=[c.value for c in Category],
                       help="Filter by category")
    parser.add_argument("--file", help="Filter by file path")
    parser.add_argument("--output", help="Output file for report")
    
    args = parser.parse_args()
    
    tracker = TodoTracker()
    
    if args.command == "scan":
        logger.info("Scanning codebase for TODO items...")
        discovered = tracker.scan_codebase()
        logger.info(f"Discovered {len(discovered)} TODO items")
        
        for todo in discovered:
            tracker.add_todo(todo)
        
        logger.info(f"Added {len(discovered)} new TODO items to tracking system")
    
    elif args.command == "sync":
        logger.info("Synchronizing TODO tracking with codebase...")
        stats = tracker.sync_with_codebase()
        logger.info(f"Sync complete:")
        logger.info(f"  New TODOs: {stats['new_todos']}")
        logger.info(f"  Completed TODOs: {stats['completed_todos']}")
        logger.info(f"  Total TODOs: {stats['total_todos']}")
    
    elif args.command == "report":
        logger.info("Generating TODO report...")
        report = tracker.generate_report()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {args.output}")
        else:
            logger.info(json.dumps(report, indent=2))
    
    elif args.command == "list":
        todos = list(tracker.todos.values())
        
        # Apply filters
        if args.priority:
            todos = [t for t in todos if t.priority.value == args.priority]
        if args.status:
            todos = [t for t in todos if t.status.value == args.status]
        if args.category:
            todos = [t for t in todos if t.category.value == args.category]
        if args.file:
            todos = [t for t in todos if args.file in t.file_path]
        
        logger.info(f"Found {len(todos)} TODO items:")
        for todo in todos:
            logger.info(f"  [{todo.priority.value.upper()}] {todo.title}")
            logger.info(f"    File: {todo.file_path}:{todo.line_number}")
            logger.info(f"    Status: {todo.status.value}")
            logger.info()

if __name__ == "__main__":
    main()
