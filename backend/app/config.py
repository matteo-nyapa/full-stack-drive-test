import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:rootpassword@mongodb:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "drive")

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB_NAME]
files_collection = db["files"]
