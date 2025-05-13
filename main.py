from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from db.index import mongoDBClient, pineconeClient, neo4jClient, MongoDBClient, PineconeClient, Neo4jClient
import httpx
import os
import sys
import traceback
from dataclasses import dataclass

@dataclass
class AppContext:
    mongdb: MongoDBClient
    pinecone: PineconeClient
    neo4j: Neo4jClient

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    try:

        print("Initializing server and connecting to databases..", file=sys.stderr)

        mongoDBClient.client.server_info()
        pineconeClient.client.list_indexes()
        neo4jClient.verify_connectivity()

        print("Successfully connected to databases!", file=sys.stderr)
        print("Starting server..", file=sys.stderr)
        yield AppContext(mongdb=mongoDBClient, pinecone=pineconeClient, neo4j=neo4jClient)

    except Exception as e:
        print(f"ERROR starting server: {e} Preparing traceback..", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

    finally:
        # Cleanup on shutdown
        print("Shutting down server and disconnecting from databases..", file=sys.stderr)
        mongoDBClient.client.close()
        neo4jClient.close()
        print("Successfully shut down server!", file=sys.stderr)

mcp = FastMCP("spydr-mcp", lifespan=app_lifespan)

@mcp.tool()
def add_chat_to_memory(messages: list[str]) -> str:
    pass

@mcp.tool() # websites and notes for now
def create_new_source() -> str:
    pass

@mcp.resource("config://app")
def get_config() -> str:
    """Static configuration data"""
    return "App configuration here"

@mcp.resource("pinecone://{query}/{k}") # over public webs
def get_query_context(query: str, k: int) -> str:
    pass

@mcp.resource("neo4j://{cypher}") # different traversals
def get_graph_context(cypher: str) -> str:
    pass

@mcp.prompt()
def note_summary_prompt() -> str:
    pass