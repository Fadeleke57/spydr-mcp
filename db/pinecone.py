from pinecone import Pinecone
from core.config import settings
from datetime import datetime
from pytz import UTC
from typing import Dict, Any, Literal, Optional
import re
import json
import sys
import time


class PineconeClient:
    def __init__(self):
        self.client = Pinecone(api_key=settings.pinecone_api_key)
        self.index = self.client.Index(name=settings.pinecone_index_name)

    def get_query_embedding(self, query: str):
        """
        Generate a vector embedding for a given query string using the Pinecone
        multilingual-e5-large model.

        Args:
            query (str): The query string to generate an embedding for.

        Returns:
            List[float]: A list of float values representing the embedding of the query.
        """
        embedding = self.client.inference.embed(
            model="multilingual-e5-large",
            inputs=[query],
            parameters={"input_type": "query"},
        )
        
        return embedding[0].values

    def run_semantic_web_search(
        self, query: str, filter: Dict[str, Any] = {}, limit: int = 10
    ):
        """
        Runs a semantic search on the Pinecone index for webs, given a query string and an optional filter.

        Args:
            query (str): The query string to search for.
            filter (Dict[str, Any]): A filter to apply on the results. The filter should be a dictionary
                where each key is a metadata key and the value is a filter value.
            limit (int): The number of results to return. Defaults to 10.

        Returns:
            list: A list of dictionaries, each containing the metadata of a result, as well as its ID.
        """
        query_embedding = self.get_query_embedding(query)
        pinecone_response = self.index.query(
            vector=query_embedding,
            top_k=limit,
            include_metadata=True,
            namespace="webs",
            filter=filter,
        )
        results = []

        for match in pinecone_response["matches"]:
            result = match["metadata"]
            result["id"] = match["id"]
            results.append(result)

        return results

    def run_semantic_source_search(
        self, query: str, filter: Dict[str, Any] = {}, limit: int = 10
    ):
        """
        Runs a semantic search over the Pinecone index for a given web ID.

        Args:
        - webId (str): The ID of the web to search within.
        - query (str): The query string to search for.
        - limit (int): The maximum number of results to return.
        - filter (Dict[str, Any]): A filter to apply on the results. The filter should be a dictionary
            where each key is a metadata key and the value is a filter value.

        Returns:
        - List[Dict[str, Any]]: A list of dictionaries, each representing a result. The dictionary will
            contain the metadata of the result, as well as an "id" key containing the ID of the result.
        """
        query_embedding = self.get_query_embedding(query)

        print(f"Query embedding: {query_embedding}", file=sys.stderr)

        pinecone_response = self.index.query(
            vector=query_embedding,
            top_k=limit,
            include_metadata=True,
            namespace="sources",
            filter=filter,
        )

        results = []
        print(f"Pinecone response: {pinecone_response}", file=sys.stderr)

        for match in pinecone_response["matches"]:
            result = match["metadata"]
            result["id"] = match["id"]
            results.append(result)
        
        return results


client = PineconeClient()
