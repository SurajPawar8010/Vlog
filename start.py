import uvicorn
import webbrowser
import threading
import time
import os

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    print("=" * 60)
    print("  🚀 Starting AutoVlog AI Studio (100% Local Engine)")
    print("  🌐 Web Interface: http://localhost:8000")
    print("  🔒 Mode: 100% Offline, Zero Cloud Upload")
    print("=" * 60)
    
    # Auto launch browser
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run FastAPI server
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
