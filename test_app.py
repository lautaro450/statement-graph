"""
Simple test FastAPI app to check if the server can start
"""
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Test API")

@app.get("/")
def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    print("Starting test FastAPI server...")
    uvicorn.run(
        "test_app:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
    print("Server started!")
