from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from models.source import CreateSource, create_source
from db.index import (
    mongoDBClient,
    pineconeClient,
    neo4jClient,
    MongoDBClient,
    PineconeClient,
    Neo4jClient,
)
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
    """
    Lifespan context manager for the app.

    Yields an AppContext once the server and databases are fully initialized.
    The AppContext is an object that contains all the connected clients to the
    databases.

    On error, the exception is caught and a traceback is printed to stderr.
    After the error is caught, or if no error occurred, the finally block is
    executed to clean up the server and databases.

    """
    try:

        print("Initializing server and connecting to databases..", file=sys.stderr)

        mongoDBClient.client.server_info()
        pineconeClient.client.list_indexes()
        neo4jClient.verify_connectivity()

        print("Successfully connected to databases!", file=sys.stderr)
        print("Starting server..", file=sys.stderr)
        yield AppContext(
            mongdb=mongoDBClient, pinecone=pineconeClient, neo4j=neo4jClient
        )

    except Exception as e:
        print(f"ERROR starting server: {e} Preparing traceback..", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

    finally:
        # cleanup on shutdown
        print(
            "Shutting down server and disconnecting from databases..", file=sys.stderr
        )
        mongoDBClient.client.close()
        neo4jClient.close()
        print("Successfully shut down server!", file=sys.stderr)


mcp = FastMCP(
    name="spydr-mcp",
    lifespan=app_lifespan,
    dependencies=[
        "fastmcp",
        "mcp",
        "neo4j",
        "pinecone",
        "pydantic",
        "pydantic-settings",
        "pymongo",
        "python-dotenv",
    ],
)

USER_ID_TO_TEST = "8f05ff19-ab84-47ba-bd02-bed09c405981"
WEB_ID_TO_TEST = "861539e5-d6aa-4a58-97d9-c19ee87475ec"


@mcp.tool()
def add_chat_to_memory(messages: list[str], summary: str) -> str:
    """
    Given a list of strings that represent a chat log, and a string for the summary,
    this tool creates a new source in the user's memory database with the given content
    and summary. The source is named with the given summary and is of type 'note'.

    Args:
        messages (list[str]): List of strings representing the chat log.
        summary (str): String to be used as the summary for the source.

    Returns:
        str: A string indicating whether the source was added successfully or not.
    """
    try:

        sourceToCreate = CreateSource(
            userId=USER_ID_TO_TEST,
            webId=WEB_ID_TO_TEST,
            name=summary,
            content="\n".join(messages),
            type="note",
        )
        print(f"Creating source: {sourceToCreate}", file=sys.stderr)
        source = create_source(sourceToCreate)

        return f"Successfully added chat to memory: {source} for user {USER_ID_TO_TEST} in web {WEB_ID_TO_TEST}"

    except Exception as e:
        print(f"ERROR adding chat to memory: {e}", file=sys.stderr)
        return "Error adding chat to memory"


@mcp.tool()  # websites and notes for now
def create_new_source() -> str:
    pass


@mcp.resource("config://app")
def get_config() -> str:
    """Static configuration data"""
    return "App configuration here"

@mcp.tool()
def get_query_context(query: str, k: int) -> str:
    """
    Given a query string, get the k most semantically relevant sources in the user's memory database.

    The sources are filtered to only include those from the user's personal webs.

    Args:
        query (str): The query string to search for.
        k (int): The number of sources to return.

    Returns:
        str: A string containing the k most semantically relevant sources.
    """
    content = pineconeClient.run_semantic_source_search(
        webId=WEB_ID_TO_TEST,
        query=query,
        limit=k,
        filter={},
    )
    print(f"Query context: {content}", file=sys.stderr)
    return f"Query context: {content}"


@mcp.resource("neo4j://{cypher}")  # different traversals
def get_graph_context(cypher: str) -> str:
    pass