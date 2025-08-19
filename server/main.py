"""
Main FastAPI application.

Startup path overview:
- Serves built React UI from `ui/dist` at `/` (if present) and `/assets`.
- Exposes API routes under `/api/*` (bots, metrics, strategies).
- SPA catch-all returns `index.html` for non-API/docs paths.
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from server.api.routes import bots, metrics, strategies

app = FastAPI(
    title="Trading Bot API",
    description="API for controlling and monitoring trading bots.",
    version="1.0.0",
)

# Configure CORS for local development with React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:3000", "http://localhost:8000"],  # Allow frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(bots.router, prefix="/api", tags=["Bots"])
app.include_router(metrics.router, prefix="/api", tags=["Metrics"])
app.include_router(strategies.router, prefix="/api", tags=["Strategies"])

# Serve static files from the React build
static_dir = os.path.join(os.path.dirname(__file__), "..", "ui", "dist")

# Mount static assets directory if it exists
if os.path.exists(static_dir):
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/", include_in_schema=False)
async def serve_root():
    """Serve the React app root"""
    if os.path.exists(static_dir):
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    return {"message": "Welcome to the Trading Bot API. Visit /docs for API documentation."}

# Catch-all route for client-side routing (must be last)
@app.get("/{catchall:path}", include_in_schema=False)
async def serve_spa(catchall: str):
    """Serve the React app for all other routes (SPA routing)"""
    # Don't serve index.html for API or docs routes
    if catchall.startswith("api") or catchall.startswith("docs") or catchall.startswith("redoc") or catchall == "openapi.json":
        raise HTTPException(status_code=404, detail="Not found")
    
    # Serve index.html for all frontend routes
    if os.path.exists(static_dir):
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    
    return {"error": "Frontend not built"}
