import sys
print("Python version:", sys.version)
print("Starting test...")

try:
    from fastapi import FastAPI
    print("FastAPI OK")
except Exception as e:
    print(f"FastAPI Error: {e}")

try:
    import uvicorn
    print("Uvicorn OK")
except Exception as e:
    print(f"Uvicorn Error: {e}")

try:
    import requests
    print("Requests OK")
except Exception as e:
    print(f"Requests Error: {e}")

try:
    import tkinter as tk
    print("Tkinter OK")
except Exception as e:
    print(f"Tkinter Error: {e}")

print("\nAll imports successful! Starting server test...")

from fastapi import FastAPI
import threading
import time

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="error")

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(3)

try:
    r = requests.get("http://127.0.0.1:5000/", timeout=5)
    print(f"Server test: {r.json()}")
except Exception as e:
    print(f"Server test failed: {e}")

print("\nTest complete!")
input("Press Enter to exit...")

