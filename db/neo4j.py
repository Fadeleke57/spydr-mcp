from neo4j import GraphDatabase
from core.config import settings
from neo4j import Record, Session
from typing import Dict, Any, List, Tuple
import sys


class Neo4jClient:
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

    def create_node(self, label: str, properties: dict) -> Dict[str, Any]:
        if label not in self.supported_labels:
            raise ValueError(f"Unsupported label: {label}")

        query = f"CREATE (n:{label} $props) RETURN n"
        result = self.execute_query(query, {"props": properties})
        return result[0]["n"] if result else None

    def get_node_by_id(self, node_id: int) -> Dict[str, Any]:
        query = "MATCH (n) WHERE id(n) = $node_id RETURN n"
        result = self.execute_query(query, {"node_id": node_id})
        return result[0]["n"] if result else None

    def update_node(self, node_id: int, properties: Dict[str, Any]) -> Dict[str, Any]:
        query = "MATCH (n) WHERE id(n) = $node_id SET n += $props RETURN n"
        result = self.execute_query(query, {"node_id": node_id, "props": properties})
        return result[0]["n"] if result else None

    def delete_node(self, node_id: int) -> bool:
        query = "MATCH (n) WHERE id(n) = $node_id DELETE n"
        self.execute_query(query, {"node_id": node_id})
        return True

    def get_nodes_by_properties(
        self, label: str, properties: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        props_filter = " AND ".join([f"n.{key} = ${key}" for key in properties.keys()])
        query = f"MATCH (n:{label}) WHERE {props_filter} RETURN n"
        result = self.execute_query(query, properties)
        return [record["n"] for record in result]

    def delete_nodes_by_properties(self, label: str, properties: Dict[str, Any]) -> int:
        if label not in self.supported_labels:
            raise ValueError(f"Unsupported label: {label}")

        props_filter = " AND ".join([f"n.{key} = ${key}" for key in properties.keys()])
        query = f"MATCH (n:{label}) WHERE {props_filter} DETACH DELETE n RETURN count(n) AS deleted_count"
        result = self.execute_query(query, properties)
        return result[0]["deleted_count"] if result else 0

    def update_nodes_by_properties(
        self,
        label: str,
        match_properties: Dict[str, Any],
        update_properties: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        if label not in self.supported_labels:
            raise ValueError(f"Unsupported label: {label}")

        match_filter = " AND ".join(
            [f"n.{key} = ${key}" for key in match_properties.keys()]
        )
        query = (
            f"MATCH (n:{label}) WHERE {match_filter} SET n += $update_props RETURN n"
        )
        params = {**match_properties, "update_props": update_properties}
        result = self.execute_query(query, params)
        return [record["n"] for record in result]

    def create_many_nodes(
        self, label: str, nodes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if label not in self.supported_labels:
            raise ValueError(f"Unsupported label: {label}")

        query_template = (
            f"UNWIND $props AS prop CREATE (n:{label}) SET n = prop RETURN n"
        )
        created_nodes = []

        with self.driver.session() as session:
            result = session.run(query_template, {"props": nodes})
            for record in result:
                created_nodes.append(record["n"])

        return created_nodes

    @staticmethod
    def serialize_source(source: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "sourceId": source["sourceId"],
            "userId": source["userId"],
            "name": source["name"],
            "url": source.get("url") or None,
            "content": source["content"],
            "webId": source["webId"],
            "created": source["created"],
            "updated": source["updated"],
            "size": source.get("size") or None,
        }

    @staticmethod
    def serialize_connection(connection: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": connection["id"],
            "sourceId": connection["sourceId"],
            "targetId": connection["targetId"],
            "created": connection["created"],
            "updated": connection["updated"],
        }

    def delete_relationship(
        self, start_node_id: int, end_node_id: int, relationship_type: str
    ) -> bool:
        query = f"""
        MATCH (start)-[r:{relationship_type}]-(end)
        WHERE id(start) = $start_id AND id(end) = $end_id
        DELETE r
        """
        params = {"start_id": start_node_id, "end_id": end_node_id}
        self.execute_query(query, params)
        return True

    def update_relationship(
        self,
        start_node_id: int,
        end_node_id: int,
        relationship_type: str,
        update_properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        query = f"""
        MATCH (start)-[c:{relationship_type}]-(end)
        WHERE id(start) = $start_id AND id(end) = $end_id
        SET r += $update_props
        RETURN r
        """

        params = {
            "start_id": start_node_id,
            "end_id": end_node_id,
            "update_props": update_properties,
        }

        result = self.execute_query(query, params)

        return result[0]["r"] if result else None

    def create_relationship(
        self,
        start_node_id: int,
        end_node_id: int,
        relationship_type: str,
        properties: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        query = """
        MATCH (start), (end)
        WHERE id(start) = $start_id AND id(end) = $end_id
        CREATE (start)-[r:$rel_type $props]->(end)
        RETURN r
        """
        params = {
            "start_id": start_node_id,
            "end_id": end_node_id,
            "rel_type": relationship_type,
            "props": properties or {},
        }
        result = self.execute_query(query, params)
        return result[0]["r"] if result else None

    # spydr specific methods
    def get_all_sources_for_web(self, label: str, web_id: str) -> List[Dict[str, Any]]:
        if label not in self.supported_labels:
            raise ValueError(f"Unsupported label: {label}")

        sources_query = """
        MATCH (s:source)
        WHERE s.webId=$web_id
        RETURN s {.*, created: toString(s.created), updated: toString(s.updated), size: toInteger(s.size) }
        """

        params = {"web_id": web_id}
        sources_result = self.execute_query(sources_query, params)
        sources = [source["s"] for source in sources_result]
        return sources

    def get_all_connections_for_web(
        self, label: str, web_id: str
    ) -> List[Dict[str, Any]]:
        if label not in self.supported_labels:
            raise ValueError(f"Unsupported label: {label}")

        connections_query = """
        MATCH (s:source)-[c]->(t:source)
        WHERE s.webId=$web_id
        RETURN c {.*, created: toString(c.created), updated: toString(c.updated)}
        """

        params = {"web_id": web_id}
        connections_result = self.execute_query(connections_query, params)
        connections = [connection["c"] for connection in connections_result]
        return connections

    def get_outgoing_connections_for_source(
        self, label: str, source_id: str
    ) -> List[Dict[str, Any]]:
        if label not in self.supported_labels:
            raise ValueError(f"Unsupported label: {label}")

        connections_query = """
        MATCH (s:source)-[c]->(t:source)
        WHERE c.fromSourceId=$source_id
        ORDER BY c.updated DESC
        RETURN c {.*, created: toString(c.created), updated: toString(c.updated)}
        """

        params = {"source_id": source_id}
        connections_result = self.execute_query(connections_query, params)
        connections = [connection["c"] for connection in connections_result]

        return connections

    def get_incoming_connections_for_source(
        self, label: str, source_id: str
    ) -> List[Dict[str, Any]]:
        if label not in self.supported_labels:
            raise ValueError(f"Unsupported label: {label}")

        connections_query = """
        MATCH (s:source)-[c]->(t:source)
        WHERE c.toSourceId=$source_id
        ORDER BY c.updated DESC
        RETURN c {.*, created: toString(c.created), updated: toString(c.updated)}
        """

        params = {"source_id": source_id}
        connections_result = self.execute_query(connections_query, params)
        connections = [connection["c"] for connection in connections_result]

        return connections

    def get_connection_by_id(self, label: str, connection_id: str) -> Dict[str, Any]:
        if label not in self.supported_labels:
            raise ValueError(f"Unsupported label: {label}")

        connections_query = """
        MATCH (s:source)-[c]->(t:source)
        WHERE c.connectionId=$connection_id
        RETURN c {.*, created: toString(c.created), updated: toString(c.updated)}
        """

        params = {"connection_id": connection_id}
        connections_result = self.execute_query(connections_query, params)
        connections = [connection["c"] for connection in connections_result]

        return connections

    def create_connection_between_sources(
        self,
        start_node_id: int,
        end_node_id: int,
        properties: Dict[str, Any] = None,
    ) -> Dict[str, Any]:

        query = """
        MATCH (s:source {sourceId: $start_id})
        MATCH (t:source {sourceId: $end_id})
        CREATE (s)-[c:connection $props]->(t)
        RETURN c {.*, created: toString(c.created), updated: toString(c.updated)}
        """
        params = {
            "start_id": start_node_id,
            "end_id": end_node_id,
            "props": properties or {},
        }
        try:
            result = self.execute_query(query, params)
        except Exception:
            print("Error creating conntection", file=sys.stderr)
        finally:
            return result[0]["c"] if result else None

    def update_connection(
        self,
        connection_id,
        relationship_type: str,
        update_properties: Dict[str, Any],
    ) -> Dict[str, Any]:
        query = f"""
        MATCH (start)-[c:{relationship_type}]-(end)
        WHERE c.connectionId=$connection_id
        SET r += $update_props
        RETURN r
        """
        params = {
            "connection_id": connection_id,
            "update_props": update_properties,
        }
        result = self.execute_query(query, params)
        return result[0]["c"] if result else None

    def delete_connection(self, connection_id, relationship_type: str) -> bool:
        if relationship_type not in self.supported_labels:
            raise ValueError(f"Unsupported label: {relationship_type}")

        query = f"""
        MATCH (start)-[c:{relationship_type}]-(end)
        WHERE c.connectionId=$connection_id
        DELETE c
        """

        params = {"connection_id": connection_id}
        self.execute_query(query, params)
        return True

    def get_source_by_id(self, label: str, source_id: str) -> Dict[str, Any]:
        if label not in self.supported_labels:
            raise ValueError(f"Unsupported label: {label}")

        sources_query = """
        MATCH (s:source)
        WHERE s.sourceId=$source_id
        RETURN s {.*, created: toString(s.created), updated: toString(s.updated)}
        """

        params = {"source_id": source_id}
        sources_result = self.execute_query(sources_query, params)
        sources = [source["s"] for source in sources_result]
        return sources[0]

    def update_source(
        self, source_id: int, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        query = "MATCH (n) WHERE n.sourceId = $source_id SET n += $props RETURN n"
        result = self.execute_query(
            query, {"source_id": source_id, "props": properties}
        )
        return result[0]["n"] if result else None


client = Neo4jClient()
