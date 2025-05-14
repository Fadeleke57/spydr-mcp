from pymongo import MongoClient, ReturnDocument
from bson.objectid import ObjectId
from pymongo.collection import Collection
from core.config import settings
from typing import List, Dict, Any


class MongoDBClient:
    def __init__(self):
        self.client = MongoClient(settings.mongo_url)
        self.db = self.client[settings.mongo_initdb_database]

    def get_collection(self, collection_name: str) -> Collection:
        return self.db[collection_name]


client = MongoDBClient()
