from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import uuid4
from models.web import Webs
from db.index import neo4jClient
from pymongo.results import UpdateResult
import sys


class CreateNote(BaseModel):
    title: str
    content: str


class UpdateNote(BaseModel):
    content: Optional[str]


class Source(BaseModel):
    sourceId: str
    webId: str
    userId: str
    name: str
    url: Optional[str] = None
    content: Optional[str] = None
    type: str
    size: int
    created: datetime
    updated: datetime
    ogImage: Optional[str] = None  # website specific
    ogDescription: Optional[str] = None  # website specific
    ogTitle: Optional[str] = None  # website specific
    favicon: Optional[str] = None  # website specific
    description: Optional[str] = None  # youtube specific


class CreateSource(BaseModel):
    userId: str
    webId: str
    name: str
    content: str
    type: str


def create_source(sourceToCreate: CreateSource):
    if not sourceToCreate:
        raise ValueError("Source object and user ID is required")

    try:

        sourceId = str(uuid4())
        print(f"Source ID: {sourceId}", file=sys.stderr)
        source = Source(
            sourceId=sourceId,
            webId=sourceToCreate.webId,
            userId=sourceToCreate.userId,
            name=sourceToCreate.name,
            content=sourceToCreate.content,
            type=sourceToCreate.type,
            size=len(sourceToCreate.content) * 200,
            created=datetime.now(),
            updated=datetime.now(),
        )
        source = neo4jClient.create_node("source", source.model_dump())
        print(f"Created source in neo4j: {source}", file=sys.stderr)
        result: UpdateResult = Webs.update_one(
            {"webId": sourceToCreate.webId},
            {"$addToSet": {"sourceIds": sourceId}},
        )
        print(f"Webs modified: {result.modified_count}", file=sys.stderr)
        return source

    except Exception as e:

        print(f"ERROR creating source: {e}", file=sys.stderr)


class UpdateSource(BaseModel):
    name: Optional[str] = None
