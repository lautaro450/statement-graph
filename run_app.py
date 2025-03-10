
"""
Run the FastAPI application
"""
import uvicorn

if __name__ == "__main__":
    print("Starting the Statement Graph API...")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=3000,
        reload=True,
        log_level="debug"
    )
