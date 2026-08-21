import uvicorn
import webbrowser
import time
import threading

def open_browser():
    time.sleep(2)
    webbrowser.open("http://localhost:8000/docs")

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Бэкенд запускается...")
    print("📄 Swagger документация: http://localhost:8000/docs")
    print("=" * 50)
    
    # Открываем браузер автоматически
    threading.Thread(target=open_browser, daemon=True).start()
    
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)