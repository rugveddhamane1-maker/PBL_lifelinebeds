import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🏥 Starting LifeLine Real-Time Bed Availability System on http://127.0.0.1:{port}")
    print(f"📖 Swagger API Docs available at http://127.0.0.1:{port}/docs")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
