import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import connect_to_mongo, close_mongo_connection, get_db_stats

from app.share.api.errors import register_error_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(title="Careera API", version="1.0.0", lifespan=lifespan)

register_error_handler(app)

# CORS
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Careera API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint - tests MongoDB connection"""
    db_stats = await get_db_stats()
    
    return {
        "api": "healthy",
        "version": "1.0.0",
        "database": db_stats
    }

# Import and include routers with /api/v1 prefix (for later)
# from app.api import auth, users, careers
# app.include_router(auth.router, prefix="/api/v1")
# app.include_router(users.router, prefix="/api/v1")
# ... etc

# Import and include routers
from app.auth.api import auth
from app.career.api import analysis as career_analysis

app.include_router(auth.router, prefix="/api/v1")
app.include_router(career_analysis.router, prefix="/api/v1")
