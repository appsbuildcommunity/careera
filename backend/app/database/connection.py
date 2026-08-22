from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration from .env
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://admin:password123@localhost:27017")
DB_NAME = os.getenv("DB_NAME", "careera_db")

# Module-level client singleton for connection pooling
_client = None

async def connect_to_mongo():
    """Connect to MongoDB when app starts"""
    global _client
    try:
        _client = AsyncIOMotorClient(MONGODB_URI, server_api=ServerApi('1'))
        # Test the connection
        await _client.admin.command('ping')
        print(f"Connected to MongoDB at {MONGODB_URI}")
        print(f"Database: {DB_NAME}")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close MongoDB connection when app shuts down"""
    global _client
    if _client:
        _client.close()
        _client = None
        print("Closed MongoDB connection")

async def get_database():
    """Get database instance"""
    if _client is None:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    return _client[DB_NAME]

async def get_db_stats():
    """Get database statistics for health check"""
    try:
        db = await get_database()
        stats = await db.command("dbStats")
        return {
            "status": "connected",
            "database": DB_NAME,
            "collections": stats.get("collections", 0),
            "dataSize": stats.get("dataSize", 0),
            "ok": True
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "ok": False
        }