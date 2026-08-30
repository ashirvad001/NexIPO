from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import Optional
from app.core.config import get_settings

settings = get_settings()


class MongoDB:
    """MongoDB connection manager for prospectus storage"""
    
    client: Optional[AsyncIOMotorClient] = None
    sync_client: Optional[MongoClient] = None
    
    @classmethod
    def connect(cls):
        """Connect to MongoDB"""
        cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
        cls.sync_client = MongoClient(settings.MONGODB_URL)
        print(f"Successfully Connected to MongoDB: {settings.MONGODB_DB}")
    
    @classmethod
    def close(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
        if cls.sync_client:
            cls.sync_client.close()
        print("👋 Closed MongoDB connection")
    
    @classmethod
    def get_database(cls):
        """Get async database instance"""
        if not cls.client:
            cls.connect()
        return cls.client[settings.MONGODB_DB]
    
    @classmethod
    def get_sync_database(cls):
        """Get sync database instance"""
        if not cls.sync_client:
            cls.connect()
        return cls.sync_client[settings.MONGODB_DB]
    
    @classmethod
    async def get_collection(cls, collection_name: str):
        """Get collection from database"""
        db = cls.get_database()
        return db[collection_name]


async def get_prospectus_collection():
    """Get prospectus collection"""
    return await MongoDB.get_collection("prospectus")


async def get_file_metadata_collection():
    """Get file metadata collection"""
    return await MongoDB.get_collection("file_metadata")


mongodb = MongoDB()
