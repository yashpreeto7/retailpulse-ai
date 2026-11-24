"""
RetailPulse AI Application Startup Script.
One-command launch for the entire application.
"""
import sys
import uvicorn
from retailpulse.config import DB_PATH
from retailpulse.data.ingestion import run_ingestion_pipeline

def main():
    print("=" * 65)
    print("🚀 RetailPulse AI — Business Intelligence & Data Analyst Agent")
    print("=" * 65)
    
    # 1. Verify or initialize database
    if not DB_PATH.exists():
        print("[Startup] Database not detected. Initializing data ingestion pipeline...")
        run_ingestion_pipeline(force_regenerate=True)
    else:
        print(f"[Startup] Active database found at: {DB_PATH}")

    print("\n[Startup] Starting FastAPI server...")
    print("👉 Web Application Dashboard: http://127.0.0.1:8000")
    print("👉 API Documentation (Swagger): http://127.0.0.1:8000/docs")
    print("👉 Alternative Docs (ReDoc): http://127.0.0.1:8000/redoc\n")

    uvicorn.run(
        "retailpulse.api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
