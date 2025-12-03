#!/usr/bin/env python3
"""
Simple script to run the AdaptEd backend server.
"""
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    from backend.app import app
    
    print("Starting AdaptEd Backend Server...")
    print("API will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server.\n")
    
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
