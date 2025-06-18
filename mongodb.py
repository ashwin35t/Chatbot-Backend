from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = "fitness_ai"

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect_to_database(cls):
        cls.client = AsyncIOMotorClient(MONGODB_URL)
        cls.db = cls.client[DATABASE_NAME]
        print("Connected to MongoDB!")

    @classmethod
    async def close_database_connection(cls):
        cls.client.close()
        print("Closed MongoDB connection!")

    @classmethod
    async def get_collection(cls, collection_name: str):
        return cls.db[collection_name]

    # User related operations
    @classmethod
    async def create_user(cls, user_data: dict):
        collection = await cls.get_collection("users")
        result = await collection.insert_one(user_data)
        return result.inserted_id

    @classmethod
    async def get_user(cls, user_id: str):
        collection = await cls.get_collection("users")
        return await collection.find_one({"_id": user_id})

    # Chat history operations
    @classmethod
    async def save_chat_message(cls, user_id: str, message: dict):
        collection = await cls.get_collection("chat_history")
        message["user_id"] = user_id
        message["timestamp"] = datetime.utcnow()
        result = await collection.insert_one(message)
        return result.inserted_id

    @classmethod
    async def get_user_chat_history(cls, user_id: str, limit: int = 50):
        collection = await cls.get_collection("chat_history")
        cursor = collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

    # User progress tracking
    @classmethod
    async def save_daily_progress(cls, user_id: str, progress_data: dict):
        collection = await cls.get_collection("daily_progress")
        progress_data["user_id"] = user_id
        progress_data["date"] = datetime.utcnow().date()
        result = await collection.insert_one(progress_data)
        return result.inserted_id

    @classmethod
    async def get_user_progress(cls, user_id: str, start_date: datetime, end_date: datetime):
        collection = await cls.get_collection("daily_progress")
        cursor = collection.find({
            "user_id": user_id,
            "date": {
                "$gte": start_date,
                "$lte": end_date
            }
        }).sort("date", 1)
        return await cursor.to_list(length=None)
