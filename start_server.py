#!/usr/bin/env python3
"""
Startup script for the Trading Bot API server.
This script starts the FastAPI server that serves both the API and the frontend.
"""
import uvicorn
import os
import sys

def main():
    """
    Start the Trading Bot API server with production settings.
    """
    # Check if the frontend is built
    frontend_dist = os.path.join(os.path.dirname(__file__), "ui", "dist")
    if not os.path.exists(frontend_dist):
        print("Frontend not found! Building frontend first...")
        os.system("cd ui && pnpm build")
        
    if not os.path.exists(os.path.join(frontend_dist, "index.html")):
        print("Frontend build failed! Please run: cd ui && pnpm run build")
        sys.exit(1)
        
    print("Starting Trading Bot API server...")
    print("Dashboard will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")
    
    try:
        uvicorn.run(
            "server.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["server"],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped gracefully")

if __name__ == "__main__":
    main()