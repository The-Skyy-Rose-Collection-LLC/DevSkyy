#!/usr/bin/env python3
"""
DevSkyy TODO Dashboard

A web-based dashboard for managing TODO items, technical debt,
and development tasks across the DevSkyy platform.
"""
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from todo_tracker import Category, Priority, Status, TodoItem, TodoTracker
import uvicorn


logger = logging.getLogger(__name__)


class TodoDashboard:
    """Web dashboard for TODO management"""

    def __init__(self):
        self.app = FastAPI(title="DevSkyy TODO Dashboard", version="1.0.0")
        self.tracker = TodoTracker()
        self.setup_routes()

    def setup_routes(self):
        """Setup FastAPI routes for the dashboard"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home(request: Request):
            """Main dashboard page"""
            return self.render_dashboard()

        @self.app.get("/api/todos")
        async def get_todos(
            status: str | None = None,
            priority: str | None = None,
            category: str | None = None,
            file_path: str | None = None,
        ):
            """Get TODO items with optional filters"""
            todos = list(self.tracker.todos.values())

            # Apply filters
            if status:
                todos = [t for t in todos if t.status.value == status]
            if priority:
                todos = [t for t in todos if t.priority.value == priority]
            if category:
                todos = [t for t in todos if t.category.value == category]
            if file_path:
                todos = [t for t in todos if file_path in t.file_path]

            return {"todos": [self.todo_to_dict(todo) for todo in todos], "total": len(todos)}

        @self.app.get("/api/todos/{todo_id}")
        async def get_todo(todo_id: str):
            """Get a specific TODO item"""
            if todo_id not in self.tracker.todos:
                raise HTTPException(status_code=404, detail="TODO not found")

            return self.todo_to_dict(self.tracker.todos[todo_id])

        @self.app.put("/api/todos/{todo_id}")
        async def update_todo(todo_id: str, update_data: dict):
            """Update a TODO item"""
            if todo_id not in self.tracker.todos:
                raise HTTPException(status_code=404, detail="TODO not found")

            # Convert string enums to enum objects
            if "status" in update_data:
                update_data["status"] = Status(update_data["status"])
            if "priority" in update_data:
                update_data["priority"] = Priority(update_data["priority"])
            if "category" in update_data:
                update_data["category"] = Category(update_data["category"])

            success = self.tracker.update_todo(todo_id, **update_data)
            if not success:
                raise HTTPException(status_code=400, detail="Failed to update TODO")

            return self.todo_to_dict(self.tracker.todos[todo_id])

        @self.app.delete("/api/todos/{todo_id}")
        async def delete_todo(todo_id: str):
            """Delete a TODO item"""
            success = self.tracker.delete_todo(todo_id)
            if not success:
                raise HTTPException(status_code=404, detail="TODO not found")

            return {"message": "TODO deleted successfully"}

        @self.app.post("/api/sync")
        async def sync_todos():
            """Synchronize TODOs with codebase"""
            stats = self.tracker.sync_with_codebase()
            return stats

        @self.app.get("/api/report")
        async def get_report():
            """Get comprehensive TODO report"""
            return self.tracker.generate_report()

        @self.app.get("/api/stats")
        async def get_stats():
            """Get dashboard statistics"""
            return self.get_dashboard_stats()

    def todo_to_dict(self, todo: TodoItem) -> dict:
        """Convert TodoItem to dictionary for JSON serialization"""
        return {
            "id": todo.id,
            "title": todo.title,
            "description": todo.description,
            "file_path": todo.file_path,
            "line_number": todo.line_number,
            "priority": todo.priority.value,
            "category": todo.category.value,
            "status": todo.status.value,
            "created_date": todo.created_date,
            "updated_date": todo.updated_date,
            "assignee": todo.assignee,
            "estimated_hours": todo.estimated_hours,
            "tags": todo.tags,
            "related_issues": todo.related_issues,
        }

    def get_dashboard_stats(self) -> dict:
        """Get statistics for dashboard display"""
        total_todos = len(self.tracker.todos)

        if total_todos == 0:
            return {
                "total": 0,
                "open": 0,
                "in_progress": 0,
                "completed": 0,
                "critical": 0,
                "high": 0,
                "completion_rate": 0,
            }

        open_todos = len(self.tracker.get_todos_by_status(Status.OPEN))
        in_progress = len(self.tracker.get_todos_by_status(Status.IN_PROGRESS))
        completed = len(self.tracker.get_todos_by_status(Status.COMPLETED))
        critical = len(self.tracker.get_todos_by_priority(Priority.CRITICAL))
        high = len(self.tracker.get_todos_by_priority(Priority.HIGH))

        completion_rate = (completed / total_todos) * 100 if total_todos > 0 else 0

        return {
            "total": total_todos,
            "open": open_todos,
            "in_progress": in_progress,
            "completed": completed,
            "critical": critical,
            "high": high,
            "completion_rate": round(completion_rate, 1),
        }

    def render_dashboard(self) -> str:
        """Render the main dashboard HTML"""
        stats = self.get_dashboard_stats()

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>DevSkyy TODO Dashboard</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .stat-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .stat-number {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #333;
                }}
                .stat-label {{
                    color: #666;
                    margin-top: 5px;
                }}
                .critical {{ color: #e74c3c; }}
                .high {{ color: #f39c12; }}
                .medium {{ color: #3498db; }}
                .low {{ color: #27ae60; }}
                .actions {{
                    margin: 20px 0;
                }}
                .btn {{
                    background: #3498db;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    margin-right: 10px;
                }}
                .btn:hover {{
                    background: #2980b9;
                }}
                .todo-list {{
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .todo-item {{
                    border-bottom: 1px solid #eee;
                    padding: 15px 0;
                }}
                .todo-item:last-child {{
                    border-bottom: none;
                }}
                .todo-title {{
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                .todo-meta {{
                    font-size: 0.9em;
                    color: #666;
                }}
                .priority-badge {{
                    display: inline-block;
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 0.8em;
                    font-weight: bold;
                    margin-right: 10px;
                }}
                .priority-critical {{
                    background: #e74c3c;
                    color: white;
                }}
                .priority-high {{
                    background: #f39c12;
                    color: white;
                }}
                .priority-medium {{
                    background: #3498db;
                    color: white;
                }}
                .priority-low {{
                    background: #27ae60;
                    color: white;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 DevSkyy TODO Dashboard</h1>
                <p>Comprehensive TODO tracking and technical debt management</p>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{stats['total']}</div>
                    <div class="stat-label">Total TODOs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['open']}</div>
                    <div class="stat-label">Open</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['in_progress']}</div>
                    <div class="stat-label">In Progress</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['completed']}</div>
                    <div class="stat-label">Completed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number critical">{stats['critical']}</div>
                    <div class="stat-label">Critical Priority</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number high">{stats['high']}</div>
                    <div class="stat-label">High Priority</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['completion_rate']}%</div>
                    <div class="stat-label">Completion Rate</div>
                </div>
            </div>

            <div class="actions">
                <button class="btn" onclick="syncTodos()">🔄 Sync with Codebase</button>
                <button class="btn" onclick="generateReport()">📊 Generate Report</button>
                <button class="btn" onclick="refreshDashboard()">🔄 Refresh</button>
            </div>

            <div class="todo-list" id="todoList">
                <h2>Recent TODOs</h2>
                <div id="todos">Loading...</div>
            </div>

            <script>
                async function loadTodos() {{
                    try {{
                        const response = await fetch('/api/todos?status=open');
                        const data = await response.json();

                        const todosContainer = document.getElementById('todos');
                        if (data.todos.length === 0) {{
                            todosContainer.innerHTML = '<p>No open TODOs found. Great job! 🎉</p>';
                            return;
                        }}

                        todosContainer.innerHTML = data.todos.slice(0, 10).map(todo => `
                            <div class="todo-item">
                                <div class="todo-title">
                                    <span class="priority-badge priority-${{todo.priority}}">${{todo.priority.toUpperCase()}}</span>
                                    ${{todo.title}}
                                </div>
                                <div class="todo-meta">
                                    📁 ${{todo.file_path}}:${{todo.line_number}} |
                                    🏷️ ${{todo.category}} |
                                    📅 ${{new Date(todo.created_date).toLocaleDateString()}}
                                </div>
                            </div>
                        `).join('');
                    }} catch (error) {{
                        document.getElementById('todos').innerHTML = '<p>Error loading TODOs</p>';
                    }}
                }}

                async function syncTodos() {{
                    try {{
                        const response = await fetch('/api/sync', {{ method: 'POST' }});
                        const stats = await response.json();
                        alert(`Sync complete! New: ${{stats.new_todos}}, Completed: ${{stats.completed_todos}}`);
                        location.reload();
                    }} catch (error) {{
                        alert('Sync failed: ' + error.message);
                    }}
                }}

                async function generateReport() {{
                    try {{
                        const response = await fetch('/api/report');
                        const report = await response.json();

                        const reportWindow = window.open('', '_blank');
                        reportWindow.document.write(`
                            <html>
                                <head><title>DevSkyy TODO Report</title></head>
                                <body>
                                    <h1>DevSkyy TODO Report</h1>
                                    <pre>${{JSON.stringify(report, null, 2)}}</pre>
                                </body>
                            </html>
                        `);
                    }} catch (error) {{
                        alert('Report generation failed: ' + error.message);
                    }}
                }}

                function refreshDashboard() {{
                    location.reload();
                }}

                // Load TODOs on page load
                loadTodos();

                // Auto-refresh every 5 minutes
                setInterval(loadTodos, 5 * 60 * 1000);
            </script>
        </body>
        </html>
        """

        return html


def main():
    """Run the TODO dashboard server"""

    dashboard = TodoDashboard()

    logger.info("🚀 Starting DevSkyy TODO Dashboard...")
    logger.info("📊 Dashboard will be available at: http://localhost:8001")
    logger.info("🔄 Auto-syncing with codebase...")

    # Initial sync
    dashboard.tracker.sync_with_codebase()

    uvicorn.run(dashboard.app, host="0.0.0.0", port=8001)


if __name__ == "__main__":
    main()
