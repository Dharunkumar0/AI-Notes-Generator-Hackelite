from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    sync_client: MongoClient = None

db = Database()

async def connect_to_mongo():
    """Create database connection."""
    try:
        # Add connection options for better stability
        connection_options = {
            'serverSelectionTimeoutMS': 5000,  # 5 seconds timeout
            'connectTimeoutMS': 10000,
            'retryWrites': True,
            'maxPoolSize': 10
        }
        
        db.client = AsyncIOMotorClient(settings.mongodb_url, **connection_options)
        db.sync_client = MongoClient(settings.mongodb_url, **connection_options)
        
        # Test the connection
        await db.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Initialize the database and collections if they don't exist
        database = db.client[settings.database_name]
        collections = ['users', 'history']
        for collection in collections:
            if collection not in await database.list_collection_names():
                await database.create_collection(collection)
                logger.info(f"Created collection: {collection}")
        
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        logger.error(f"MongoDB URL: {settings.mongodb_url}")
        logger.error(f"Database name: {settings.database_name}")
        # Don't raise the error, just log it
        return None

async def close_mongo_connection():
    """Close database connection."""
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed")

def get_collection(collection_name: str):
    """Get a collection from the database."""
    return db.client[settings.database_name][collection_name]

def get_sync_collection(collection_name: str):
    """Get a synchronous collection from the database."""
    return db.sync_client[settings.database_name][collection_name] 