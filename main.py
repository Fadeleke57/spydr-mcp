from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.server import Settings
from mcp.server.auth.settings import (
    AuthSettings,
    RevocationOptions,
    ClientRegistrationOptions,
)
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from models.index import CreateSource, create_source, query_client
from db.index import (
    mongoDBClient,
    pineconeClient,
    neo4jClient,
    MongoDBClient,
    PineconeClient,
    Neo4jClient,
)
from core.config import settings
import sys
import traceback
from dataclasses import dataclass
from authlib.oauth2.rfc6749 import ResourceProtector
from auth.index import MCPClientAuthentication, MCPAuthorizationServer, MCPTokenValidator
from fastapi import Request, Depends

# uv run mcp install main.py --with pymongo --with neo4j --with pinecone --with pydantic-settings --with pydantic --with python-dotenv
client_auth = MCPClientAuthentication(query_client=query_client)
oauth_server = MCPAuthorizationServer()

require_oauth = ResourceProtector()
require_oauth.register_token_validator(
    MCPTokenValidator(
        realm="spydr-mcp",
        description="Protected resource requiring valid OAuth 2.1 token",
        scope="read",
        # Additional parameters per RFC6750[1]
        token_type="Bearer",
        token_type_hint="access_token"
    )
)

@dataclass
class AppContext:
    mongodb: MongoDBClient
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
            mongodb=mongoDBClient, pinecone=pineconeClient, neo4j=neo4jClient
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


server_settings = Settings(
    debug=settings.fastapi_env == "dev",
    auth=AuthSettings(
        issuer_url="https://spydr.dev",
        revocation_options=RevocationOptions(
            enabled=True,
        ),
        client_registration_options=ClientRegistrationOptions(
            enabled=True,
            valid_scopes=["read", "write"],  # define scopes
            default_scopes=["read"],  # default scope
        ),
        required_scopes=["read"],  # required scope
    ),
    dependencies=[
        "fastmcp",
        "mcp",
        "neo4j",
        "pinecone",
        "pydantic",
        "pydantic-settings",
        "pymongo",
        "python-dotenv",
        "authlib",
        "fastapi",
    ],
    lifespan=app_lifespan,
)

mcp = FastMCP(
    name="spydr-mcp",
    auth_server_provider=oauth_server,
    settings=server_settings,
)

USER_ID_TO_TEST = "8f05ff19-ab84-47ba-bd02-bed09c405981"
WEB_ID_TO_TEST = "861539e5-d6aa-4a58-97d9-c19ee87475ec"

@mcp.app.post("/oauth/token")
async def issue_token(request: Request):
    return await oauth_server.create_token_response(request)

@mcp.app.post("/oauth/introspect")
async def introspect_token(request: Request):
    return await oauth_server.create_introspect_response(request)


@mcp.tool(dependencies=[Depends(require_oauth)])
def add_chat_to_memory(
    messages: list[str],
    summary: str,
    token: dict = Depends(require_oauth)
) -> str:
    # Token is now validated via Authlib's RFC6750-compliant flow
    user_id = token.get('sub')
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
        query=query,
        limit=k,
        filter={},
    )
    print(f"Query context: {content}", file=sys.stderr)
    return f"Query context: {content}"


@mcp.resource("neo4j://{cypher}")  # different traversals
def get_graph_context(cypher: str) -> str:
    pass
