from mcp.server.fastmcp import FastMCP
import os

mcp = FastMCP("spydr-mcp")

@mcp.tool()
def add_chat_to_memory(messages: list[str]) -> str:
    pass

@mcp.tool() # websites and notes for now
def create_new_source() -> str:
    pass

@mcp.resource("pinecone://{query}/{k}") # over public webs
def get_query_context(query: str, k: int) -> str:
    pass

@mcp.resource("neo4j://{cypher}") # different traversals
def get_graph_context(cypher: str) -> str:
    pass

@mcp.prompt()
def note_summary_prompt() -> str:
    pass