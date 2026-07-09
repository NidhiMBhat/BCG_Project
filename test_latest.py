import urllib.request
import time
print("Checking stream...")
try:
    resp = urllib.request.urlopen("http://localhost:8002/cam.mjpg", timeout=2)
    print("Got headers, reading bytes...")
    data = resp.read(100)
    print("Got data:", data)
except Exception as e:
    print("Error:", e)
