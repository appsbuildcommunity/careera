from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import connect_to_mongo, close_mongo_connection, get_db_stats

app = FastAPI(title="Careera API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event - connect to MongoDB
@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()

# Shutdown event - close MongoDB connection
@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo_connection()

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
from app.api import auth

app.include_router(auth.router, prefix="/api/v1")