import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from backend.database.seed import seed_all
from backend.api import profile_routes, food_routes, meal_routes, hydration_routes, progress_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB schema & seed data
    seed_all()
    yield

app = FastAPI(
    title="AI Personal Food & Wellness Management Agent API",
    version="1.0.0",
    description="Agentic AI Food & Wellness Management System with Deterministic Nutrition Calculations",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(profile_routes.router)
app.include_router(food_routes.router)
app.include_router(meal_routes.router)
app.include_router(hydration_routes.router)
app.include_router(progress_routes.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Personal Food & Wellness Management Agent",
        "database": "connected",
        "phase": 1
    }

# Mount Frontend static files
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)
