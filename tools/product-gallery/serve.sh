#!/bin/bash
# SkyyRose Product Classifier — Threaded Dev Server
cd "$(dirname "$0")/../.."
echo ""
echo "  SkyyRose Product Classifier"
echo "  http://localhost:4200/tools/product-gallery/"
echo ""
python3 -c "
import http.server, socketserver, os
os.chdir('$(pwd)')
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args): pass  # quiet
with socketserver.ThreadingTCPServer(('', 4200), H) as s:
    s.serve_forever()
"
