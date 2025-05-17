from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import uuid4
from pymongo.results import UpdateResult
from db.index import mongoDBClient

Users = mongoDBClient.get_collection("users")
