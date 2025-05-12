from pinecone import Pinecone
from core.config import settings
from datetime import datetime
from pytz import UTC
from typing import Dict, Any, Literal, Optional
import re
import time

class PineconeClient:
    def __init__(self):
        self.client = Pinecone(api_key=settings.pinecone_api_key)
        self.index = self.client.Index(name=settings.pinecone_index_name)

client = PineconeClient()