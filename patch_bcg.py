import sys

with open('bcg_live.py', 'r') as f:
    content = f.read()

import_block = """
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import io
from PIL import Image

latest_jpeg = None

class CamHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    def do_GET(self):
        global latest_jpeg
        if self.path.endswith('.mjpg'):
            self.send_response(200)
            self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            while True:
                try:
                    if latest_jpeg is not None:
                        self.wfile.write(b"--jpgboundary\\r\\n")
                        self.send_header('Content-type','image/jpeg')
                        self.send_header('Content-length',str(len(latest_jpeg)))
                        self.end_headers()
                        self.wfile.write(latest_jpeg)
                        self.wfile.write(b"\\r\\n")
                    import time
                    time.sleep(0.1)
                except Exception as e:
                    break
        else:
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><img src="/cam.mjpg"/></body></html>')

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

def start_mjpeg_server():
    try:
        server = ThreadedHTTPServer(('0.0.0.0', 8002), CamHandler)
        print("MJPEG Server listening on port 8002...")
        server.serve_forever()
    except Exception as e:
        print(f"Error starting MJPEG Server: {e}")
"""

# Insert imports and classes
content = content.replace("import smtplib", import_block + "\nimport smtplib")

# Insert thread start in main
thread_block = """
    mjpeg_thread = threading.Thread(target=start_mjpeg_server, daemon=True)
    mjpeg_thread.start()
    
    print("Initializing signal buffers and displaying dashboard...")
"""
content = content.replace("print(\"Initializing signal buffers and displaying dashboard...\")", thread_block)

# Insert frame capture at end of update_plot
capture_block = """
        panel_text.set_text(panel_content)
        
        global latest_jpeg
        try:
            fig.canvas.draw()
            rgba = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8).reshape(fig.canvas.get_width_height()[::-1] + (4,))
            img = Image.fromarray(rgba, 'RGBA').convert('RGB')
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=65)
            latest_jpeg = buf.getvalue()
        except Exception:
            pass
            
        return (line_raw_x,
"""
content = content.replace("panel_text.set_text(panel_content)\n        \n        return (line_raw_x,", capture_block)

with open('bcg_live.py', 'w') as f:
    f.write(content)

print("bcg_live.py patched")
