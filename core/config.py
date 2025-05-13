import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

env_path = "/Users/fadel/Desktop/dev/spydr-mcp/.env" #update in prod
load_dotenv(dotenv_path=env_path)

print(f"LOADING ENVIRONMENT: {os.getenv('FASTAPI_ENV', 'NOT SET')}", file=sys.stderr)

class Settings(BaseSettings):
    mongo_initdb_database: str
    mongo_url: str
    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str
    fastapi_env: str
    fastapi_secret_key: str
    fastapi_api_url: str
    pinecone_api_key: str
    pinecone_index_name: str

    class Config:
        env_file = env_path
        ignore_extra = True

try:
    settings = Settings()
    print(f"WELCOME TO SPYDR MCP", file=sys.stderr)
except Exception as e:
    print(f"ERROR loading settings: {e}", file=sys.stderr)