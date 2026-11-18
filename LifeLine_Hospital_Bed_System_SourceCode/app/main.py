import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, Base, get_db
from app.seed_data import seed_database
from app.routers import hospitals, ws, analytics

# Create database tables and seed sample dataset on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    # Seed initial hospital data
    db = next(get_db())
    try:
        seed_database(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Real-Time Hospital Bed Availability System for Emergency Critical Care Admissions",
    lifespan=lifespan
)

# CORS middleware to allow external integrations if required
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup directories for static assets and Jinja2 templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Include API Routers
app.include_router(hospitals.router)
app.include_router(ws.router)
app.include_router(analytics.router)

# Page Routes
@app.get("/", tags=["UI"])
def home_page(request: Request):
    """Public Emergency Hospital Bed Finder Portal."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": settings.APP_NAME, "city": settings.CITY_DEFAULT}
    )

@app.get("/staff", tags=["UI"])
def staff_page(request: Request):
    """Dedicated Hospital Staff Bed Management Console."""
    return templates.TemplateResponse(
        request=request,
        name="staff.html",
        context={"app_name": settings.APP_NAME}
    )

@app.get("/analytics", tags=["UI"])
def analytics_page(request: Request):
    """City-Wide Bed Analytics & Critical Shortage Monitor."""
    return templates.TemplateResponse(
        request=request,
        name="analytics.html",
        context={"app_name": settings.APP_NAME, "city": settings.CITY_DEFAULT}
    )

@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint for Docker, Render, Kubernetes, and uptime monitors."""
    return {"status": "healthy", "version": settings.APP_VERSION}
