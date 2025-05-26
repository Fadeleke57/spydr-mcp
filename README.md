
This repository contains a Python SDK built on top of the `FastMCP` framework, designed to provide a set of tools and resources for interacting with various database systems and managing user memory. It integrates with MongoDB, Pinecone, and Neo4j for data storage and retrieval, offering functionalities to add chat logs to memory and query semantic and graph-based contexts.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
  - [Lifespan Management](#lifespan-management)
  - [Tools](#tools)
  - [Resources](#resources)
- [Database Configuration](#database-configuration)
- [Development](#development)
- [License](#license)

---

## Features

- **Multi-database Integration**: Seamlessly connects to MongoDB (for general data), Pinecone (for semantic search), and Neo4j (for graph-based data).
- **FastMCP Framework**: Leverages the `FastMCP` framework for building modular and scalable microservices and tools.
- **Memory Management**: Provides tools to store and retrieve user chat logs as "notes" in a memory database.
- **Semantic Search**: Enables semantic search over stored user memory using Pinecone.
- **Graph Context Retrieval**: Future-proofed for retrieving graph-based context from Neo4j.
- **Dependency Management**: Uses `uv` for efficient dependency resolution and locking.

---

## Project Structure

```
fadeleke57-mcp-python-sdk/
├── README.md             (This file)
├── main.py               (Main application entry point and FastMCP setup)
├── pyproject.toml        (Project metadata and dependencies)
├── uv.lock               (Locked dependencies managed by uv)
├── auth/                 (Authentication related modules - currently a placeholder)
│   ├── __init__.py
│   └── index.py
├── core/                 (Core application functionalities)
│   ├── __init__.py
│   └── config.py         (Configuration related settings - currently static)
├── db/                   (Database connection and interaction modules)
│   ├── __init__.py
│   ├── index.py          (Database client instantiation and access)
│   ├── mongodb.py        (MongoDB specific operations)
│   ├── neo4j.py          (Neo4j specific operations)
│   └── pinecone.py       (Pinecone specific operations)
├── docs/                 (Project documentation)
│   └── README.md
└── models/               (Data models and schemas)
    ├── __init__.py
    ├── source.py         (Data models for sources, e.g., CreateSource)
    └── web.py
```

---

## Installation

To set up the project, you'll need `uv` installed, which is used for dependency management.

1.  **Install `uv`**:
    If you don't have `uv` installed, you can install it using pip:
    ```bash
    pip install uv
    ```

2.  **Clone the repository**:
    ```bash
    git clone [https://github.com/your-username/fadeleke57-mcp-python-sdk.git](https://github.com/your-username/fadeleke57-mcp-python-sdk.git)
    cd fadeleke57-mcp-python-sdk
    ```

3.  **Install dependencies**:
    This project uses `uv` to manage its dependencies. The `main.py` file specifies the required packages.
    ```bash
    uv run mcp install main.py --with pymongo --with neo4j --with pinecone --with pydantic-settings --with pydantic --with python-dotenv
    ```
    This command will install all necessary packages as defined in `pyproject.toml` and the `main.py` dependencies.

---

## Usage

The application is built with `FastMCP` and can be run using the `mcp` CLI tool.

### Running the Application

To start the `FastMCP` server:

```bash
uv run mcp serve main.py
```

### Lifespan Management

The `app_lifespan` context manager in `main.py` handles the initialization and shutdown of database connections (MongoDB, Pinecone, Neo4j). It ensures that database clients are connected before the server starts and gracefully closed upon shutdown.

Any errors during initialization will be caught, and a traceback will be printed to `stderr`.

### Tools

The `main.py` defines several `FastMCP` tools that expose specific functionalities:

-   `add_chat_to_memory(messages: list[str], summary: str) -> str`:
    Adds a chat log to the user's memory database as a "note" type source.
    -   `messages`: A list of strings representing the chat log.
    -   `summary`: A string to be used as the summary/name for the source.
    -   **Returns**: A string indicating success or failure.

    **Example Usage (within the MCP environment)**:
    ```python
    result = add_chat_to_memory(messages=["Hello!", "How are you?"], summary="Quick chat about greetings")
    print(result)
    ```

-   `create_new_source() -> str`:
    (Currently a placeholder) Intended for creating new sources, possibly of different types like websites or notes.

-   `get_query_context(query: str, k: int) -> str`:
    Retrieves the `k` most semantically relevant sources from the user's memory database based on a query.
    -   `query`: The query string for semantic search.
    -   `k`: The number of top relevant sources to return.
    -   **Returns**: A string containing the found content.

    **Example Usage (within the MCP environment)**:
    ```python
    context = get_query_context(query="important concepts", k=3)
    print(context)
    ```

### Resources

-   `get_config() -> str` (Resource: `config://app`):
    A static resource that returns "App configuration here". This is an example of serving static configuration data.

-   `get_graph_context(cypher: str) -> str` (Resource: `neo4j://{cypher}`):
    (Currently a placeholder) This resource is designed to execute Neo4j Cypher queries and return graph-based context.

---

## Database Configuration

This SDK expects the following environment variables to be set for database connectivity. It's recommended to use a `.env` file in the root directory for local development.

-   **MongoDB**: Connection string for MongoDB.
-   **Pinecone**: API key and environment for Pinecone.
-   **Neo4j**: URI, username, and password for Neo4j.

*Note: Specific environment variable names are typically defined within the `db` and `core/config.py` modules. Please refer to those files for exact variable names if not explicitly mentioned here.*

---

## Development

-   **Adding New Tools/Resources**: New functionalities can be exposed as `FastMCP` tools or resources by decorating Python functions with `@mcp.tool()` or `@mcp.resource()`.
-   **Extending Database Interactions**: The `db/` directory contains modules for each database. New functions for database operations should be added there.
-   **Defining Data Models**: Use `pydantic` models in the `models/` directory for robust data validation and serialization.

---

## License

---
