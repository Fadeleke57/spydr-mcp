from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv(".env")

print(f"LOADING ENVIRONMENT: {os.getenv('FASTAPI_ENV')}")

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
        env_file = ".env"
        extra = "ignore"

settings = Settings()
