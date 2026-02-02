"""
Prometheus Metrics HTTP Server

Exposes Prometheus metrics endpoint for scraping by Prometheus/Grafana.
Runs on a separate port from the main MCP server to avoid interference.

Endpoints:
    GET /metrics - Prometheus metrics in text format
    GET /health - Health check endpoint
    GET / - Simple status page

Usage:
    # Start standalone
    python monitoring/metrics_server.py

    # Or import and start programmatically
    from monitoring.metrics_server import start_metrics_server
    await start_metrics_server(port=9090)

Configuration:
    METRICS_PORT (default: 9090)
    METRICS_HOST (default: 0.0.0.0)

Version: 1.0.0
"""

import asyncio
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from monitoring.prometheus_metrics import get_metrics_text, update_server_uptime

# Server configuration
METRICS_PORT = int(os.getenv("METRICS_PORT", "9090"))
METRICS_HOST = os.getenv("METRICS_HOST", "0.0.0.0")

# Track server start time
SERVER_START_TIME = time.time()


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics endpoint."""

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/metrics":
            self.serve_metrics()
        elif self.path == "/health":
            self.serve_health()
        elif self.path == "/":
            self.serve_status()
        else:
            self.send_error(404, "Not Found")

    def serve_metrics(self):
        """Serve Prometheus metrics in text format."""
        try:
            # Update uptime before serving metrics
            uptime = time.time() - SERVER_START_TIME
            update_server_uptime(uptime)

            # Get metrics in Prometheus format
            metrics_data = get_metrics_text()

            # Send response
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.end_headers()
            self.wfile.write(metrics_data)

        except Exception as e:
            self.send_error(500, f"Error generating metrics: {e}")

    def serve_health(self):
        """Serve health check endpoint."""
        try:
            uptime = time.time() - SERVER_START_TIME

            health_data = {
                "status": "healthy",
                "uptime_seconds": round(uptime, 2),
                "metrics_endpoint": f"http://{METRICS_HOST}:{METRICS_PORT}/metrics",
            }

            response = str(health_data).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response)

        except Exception as e:
            self.send_error(500, f"Health check failed: {e}")

    def serve_status(self):
        """Serve simple status page with links."""
        uptime = time.time() - SERVER_START_TIME
        uptime_hours = uptime / 3600

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>DevSkyy Metrics Server</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    max-width: 800px;
                    margin: 40px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{ color: #333; }}
                .status {{ color: #22c55e; font-weight: bold; }}
                .metric {{ margin: 10px 0; padding: 10px; background: #f9fafb; border-radius: 4px; }}
                .link {{ color: #3b82f6; text-decoration: none; }}
                .link:hover {{ text-decoration: underline; }}
                code {{
                    background: #1f2937;
                    color: #f9fafb;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: "Fira Code", monospace;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 DevSkyy Metrics Server</h1>
                <p class="status">● Running</p>

                <h2>📊 Endpoints</h2>
                <div class="metric">
                    <strong>Metrics:</strong>
                    <a class="link" href="/metrics">/metrics</a>
                    (Prometheus format)
                </div>
                <div class="metric">
                    <strong>Health:</strong>
                    <a class="link" href="/health">/health</a>
                    (JSON status)
                </div>

                <h2>⏱️ Server Status</h2>
                <div class="metric">
                    <strong>Uptime:</strong> {uptime_hours:.2f} hours
                </div>
                <div class="metric">
                    <strong>Port:</strong> {METRICS_PORT}
                </div>
                <div class="metric">
                    <strong>Host:</strong> {METRICS_HOST}
                </div>

                <h2>🔧 Prometheus Configuration</h2>
                <p>Add this to your <code>prometheus.yml</code>:</p>
                <pre style="background: #1f2937; color: #f9fafb; padding: 15px; border-radius: 4px; overflow-x: auto;">
scrape_configs:
  - job_name: 'devskyy_mcp'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:{METRICS_PORT}']
        labels:
          service: 'devskyy_mcp'
          environment: 'production'
                </pre>

                <h2>📈 Grafana Dashboard</h2>
                <p>Import the DevSkyy dashboard JSON from <code>monitoring/grafana/devskyy_dashboard.json</code></p>

                <h2>🚀 Quick Start</h2>
                <ol>
                    <li>Start Prometheus: <code>prometheus --config.file=prometheus.yml</code></li>
                    <li>Start Grafana: <code>grafana-server</code></li>
                    <li>Add Prometheus data source in Grafana (http://localhost:9090)</li>
                    <li>Import DevSkyy dashboard</li>
                    <li>Monitor your MCP server! 📊</li>
                </ol>
            </div>
        </body>
        </html>
        """

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        """Override to customize logging."""
        # Only log errors and important events
        if "500" in str(args) or "404" in str(args):
            print(f"[{self.log_date_time_string()}] {format % args}")


def start_metrics_server(port: int = METRICS_PORT, host: str = METRICS_HOST):
    """
    Start the Prometheus metrics HTTP server.

    Args:
        port: Port to listen on (default: 9090)
        host: Host to bind to (default: 0.0.0.0)
    """
    server = HTTPServer((host, port), MetricsHandler)

    print(f"🎯 DevSkyy Metrics Server starting...")
    print(f"📊 Prometheus metrics: http://{host}:{port}/metrics")
    print(f"❤️  Health check: http://{host}:{port}/health")
    print(f"🌐 Status page: http://{host}:{port}/")
    print(f"\n✅ Server ready! Press Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down metrics server...")
        server.shutdown()
        print("✅ Metrics server stopped.")


def start_metrics_server_background(port: int = METRICS_PORT, host: str = METRICS_HOST):
    """
    Start metrics server in a background thread.

    Args:
        port: Port to listen on
        host: Host to bind to

    Returns:
        Thread: The background thread running the server
    """
    thread = Thread(
        target=start_metrics_server,
        args=(port, host),
        daemon=True,
        name="MetricsServer"
    )
    thread.start()
    return thread


if __name__ == "__main__":
    # Start server directly
    start_metrics_server()
