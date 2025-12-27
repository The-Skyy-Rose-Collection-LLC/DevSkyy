#!/usr/bin/env python3
"""
Meshy Webhook Receiver Server.

Run this locally with ngrok to receive Meshy task completion notifications.

Setup:
    1. Install ngrok: brew install ngrok
    2. Start this server: python scripts/meshy_webhook_server.py
    3. In another terminal: ngrok http 5555
    4. Copy the ngrok URL and set it in Meshy or as MESHY_WEBHOOK_URL

Usage:
    python scripts/meshy_webhook_server.py
"""

import json
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PORT = 5555
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "3d-models-generated" / "meshy"


class MeshyWebhookHandler(BaseHTTPRequestHandler):
    """Handle incoming Meshy webhook notifications."""

    def do_POST(self):
        """Process webhook POST from Meshy."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode("utf-8"))
            self.handle_webhook(data)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())

        except Exception as e:
            print(f"Error processing webhook: {e}")
            self.send_response(500)
            self.end_headers()

    def handle_webhook(self, data: dict):
        """Process Meshy webhook data."""
        task_id = data.get("id", "unknown")
        status = data.get("status", "unknown")
        task_type = data.get("object", "unknown")

        print(f"\n{'=' * 50}")
        print(f"WEBHOOK RECEIVED: {datetime.now().isoformat()}")
        print(f"{'=' * 50}")
        print(f"Task ID: {task_id}")
        print(f"Type: {task_type}")
        print(f"Status: {status}")

        if status == "SUCCEEDED":
            self.handle_success(data)
        elif status == "FAILED":
            print(f"Task failed: {data.get('message', 'Unknown error')}")
        else:
            print(f"Task in progress: {data.get('progress', 0)}%")

        # Save webhook data for debugging
        log_dir = OUTPUT_DIR / "webhooks"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{task_id}_{status}.json"
        with open(log_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved to: {log_path}")

    def handle_success(self, data: dict):
        """Download completed model."""
        task_id = data.get("id", "unknown")

        # Get model URLs
        model_urls = data.get("model_urls", {})
        glb_url = model_urls.get("glb")

        if not glb_url:
            print("No GLB URL in response")
            return

        # Download
        output_path = OUTPUT_DIR / f"{task_id}.glb"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"Downloading to: {output_path}")

        try:
            urllib.request.urlretrieve(glb_url, str(output_path))
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"Downloaded: {size_mb:.1f} MB")

            # Also download textures if available
            texture_urls = data.get("texture_urls", [])
            for _i, tex in enumerate(texture_urls):
                tex_type = (
                    tex.get("base_color")
                    or tex.get("metallic")
                    or tex.get("normal")
                    or tex.get("roughness")
                )
                if tex_type:
                    for name, url in tex.items():
                        if url and url.startswith("http"):
                            tex_path = OUTPUT_DIR / f"{task_id}_{name}.png"
                            urllib.request.urlretrieve(url, str(tex_path))
                            print(f"Texture saved: {tex_path.name}")

        except Exception as e:
            print(f"Download failed: {e}")

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("MESHY WEBHOOK SERVER")
    print("=" * 60)
    print(f"\nListening on port {PORT}")
    print("\nTo expose publicly, run in another terminal:")
    print(f"  ngrok http {PORT}")
    print("\nThen use the ngrok URL as your webhook in Meshy")
    print("\nExample webhook URL:")
    print("  https://xxxx-xx-xx-xxx-xxx.ngrok.io/webhook")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\n" + "=" * 60)
    print("Waiting for webhooks...")

    server = HTTPServer(("", PORT), MeshyWebhookHandler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
