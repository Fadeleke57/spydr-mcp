from neo4j import GraphDatabase
from core.config import settings
from neo4j import Record, Session
from typing import Dict, Any, List, Tuple

class Neo4jDBClient:
    def __init__(self) -> None:
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
            max_connection_lifetime=300,  # close stale connection after 5 minutes and reefresh
            keep_alive=True,  # keep connection alive
        )
        self.supported_labels = {"source", "connection"}

    def close(self) -> None:
        self.driver.close()

    def verify_connectivity(self) -> None:
        self.driver.verify_connectivity()

    def session(self) -> Session:
        return self.driver.session()

    def execute_query(
        self, query: str, parameters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]
        
client = Neo4jDBClient()