from mcp.server.fastmcp import FastMCP
import os

# Create an MCP server
mcp = FastMCP("spydr-mcp")

@mcp.tool()
def add_chat_to_memory(message: str) -> str:
    pass

@mcp.tool() # websites and notes for now
def create_new_source() -> str:
    pass

@mcp.resource("pinecone") # over public webs
def get_query_context(query: str, k: int) -> str:
    pass

@mcp.resource("neo4j_graph") # different traversals
def get_graph_context(cypher: str) -> str:
    pass

@mcp.prompt()
def note_summary_prompt() -> str:
    pass