# lesson-9-maintaining-long-term-agent-memory-in-python/exercises/solution/long_term_memory/db.py

import os
import logging
from typing import Optional
from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

logger = logging.getLogger(__name__)

# Internal cached client/container
_client: Optional[CosmosClient] = None
_database = None
_container = None


def get_cosmos_client(database_name: str = "agent_memory",
                      container_name: str = "memories",
                      partition_key: str = "/session_id") -> CosmosClient:
    """
    Get or create a Cosmos DB client, database, and container.
    Returns the CosmosClient (container can be accessed via get_container()).
    """
    global _client, _database, _container

    if _client is None:
        endpoint = os.getenv("COSMOS_ENDPOINT")
        key = os.getenv("COSMOS_KEY")

        if not endpoint or not key:
            raise ValueError("COSMOS_ENDPOINT and COSMOS_KEY must be set in environment")

        _client = CosmosClient(endpoint, key)
        _database = _client.create_database_if_not_exists(id=database_name)
        _container = _database.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path=partition_key),
        )

        logger.info(f"✅ Connected to Cosmos DB: {database_name}/{container_name}")

    return _client


def get_container():
    """
    Return the initialized Cosmos container.
    Call get_cosmos_client() first if not already connected.
    """
    global _container
    if _container is None:
        raise RuntimeError("Cosmos DB container not initialized. Call get_cosmos_client() first.")
    return _container
