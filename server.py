"""
Bio-Sentinel Local Web Deployment Server.

Serves:
- Dashboard interface at http://localhost:8000
- Inference API endpoint at http://localhost:8000/api/predict
- Visualizations at http://localhost:8000/visualizations/
"""

import os
import sys
import json
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, 'src'))

from predict import BioSentinelPredictor

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

predictor = BioSentinelPredictor(os.path.join(BASE_DIR, 'models', 'decision_tree_frugal.joblib'))

class BioSentinelHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Serve dashboard/index.html as root
        parsed = urlparse(path)
        if parsed.path == '/' or parsed.path == '/index.html':
            return os.path.join(BASE_DIR, 'dashboard', 'index.html')
        elif parsed.path.startswith('/visualizations/'):
            filename = parsed.path.replace('/visualizations/', '')
            return os.path.join(BASE_DIR, 'visualizations', filename)
        elif parsed.path.startswith('/dashboard/'):
            filename = parsed.path.replace('/dashboard/', '')
            return os.path.join(BASE_DIR, 'dashboard', filename)
        return super().translate_path(path)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/predict':
            query = parse_qs(parsed.query)
            # Parse query params
            readings = {
                'pH': float(query.get('pH', [7.3])[0]),
                'EC': float(query.get('EC', [450.0])[0]),
                'TDS': float(query.get('TDS', [288.0])[0]),
                'turbidity': float(query.get('turbidity', [0.5])[0]),
                'temperature': float(query.get('temperature', [25.0])[0]),
                'flow': float(query.get('flow', [11.5])[0]),
                'delta_p': float(query.get('delta_p', [16.0])[0]),
                'cumulative_litres': float(query.get('cumulative_litres', [1450.0])[0]),
                'cartridge_age': float(query.get('cartridge_age', [6.0])[0])
            }
            res = predictor.predict_single(readings)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/predict':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                body = json.loads(post_data.decode('utf-8'))
                res = predictor.predict_single(body)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(res).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        else:
            self.send_error(404)

if __name__ == '__main__':
    print(f"==================================================")
    print(f"  BIO-SENTINEL LOCAL DEPLOYMENT SERVER ACTIVE")
    print(f"==================================================")
    print(f"Dashboard URL: http://localhost:{PORT}")
    print(f"Prediction API: http://localhost:{PORT}/api/predict")
    print(f"Press Ctrl+C to stop the server.")
    
    with socketserver.TCPServer(("", PORT), BioSentinelHandler) as httpd:
        httpd.serve_forever()
