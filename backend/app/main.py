import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.auth import seed_default_admin
from backend.app.routers import health, auth, shipments, tracking

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    
    # Bootstrap default administrator account
    db = SessionLocal()
    try:
        seed_default_admin(db)
    finally:
        db.close()
        
    yield
    # Cleanup on shutdown if needed

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API service for Cloud-Based Product Delivery & Real-Time Tracking System",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local testing and decoupled CloudFront/S3 frontend hosting
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(shipments.router)
app.include_router(tracking.router)

# Mount frontend directories for seamless local development
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    css_dir = os.path.join(frontend_dir, "css")
    js_dir = os.path.join(frontend_dir, "js")
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", include_in_schema=False)
    @app.get("/index.html", include_in_schema=False)
    def serve_customer_portal():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/admin", include_in_schema=False)
    @app.get("/admin.html", include_in_schema=False)
    def serve_admin_portal():
        return FileResponse(os.path.join(frontend_dir, "admin.html"))
