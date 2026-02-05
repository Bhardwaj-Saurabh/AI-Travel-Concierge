# app/long_term_memory.py
"""
Long-term memory system for persistent context storage in Cosmos DB.

Implements durable memory storage across sessions with importance scoring,
tagging, and search capabilities.
"""

import os
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class LongTermMemory:
    """
    Long-term memory system with Cosmos DB persistence.

    Features:
    - Store memories persistently across sessions
    - Importance scoring for memory prioritization
    - Tagging and metadata support
    - Search and filter capabilities
    - Automatic pruning based on importance
    """

    def __init__(self):
        """
        Initialize long-term memory with Cosmos DB.

        Reads configuration from environment variables:
        - COSMOS_ENDPOINT: Cosmos DB endpoint URL
        - COSMOS_KEY: Cosmos DB access key
        - COSMOS_DB: Database name (default: "agent-memory-db")
        - COSMOS_CONTAINER: Container name (default: "memory")
        - COSMOS_PARTITION_KEY: Partition key path (default: "/session_id")
        """
        self.endpoint = os.getenv("COSMOS_ENDPOINT")
        self.key = os.getenv("COSMOS_KEY")
        self.database_name = os.getenv("COSMOS_DB", "agent-memory-db").strip('"')
        self.container_name = os.getenv("COSMOS_CONTAINER", "memory").strip('"')
        self.partition_key_path = os.getenv("COSMOS_PARTITION_KEY", "/session_id").strip('"')

        if not self.endpoint or not self.key:
            raise ValueError("COSMOS_ENDPOINT and COSMOS_KEY must be set in environment")

        # Initialize Cosmos DB client
        self._client = CosmosClient(self.endpoint, self.key)
        self._database = self._client.create_database_if_not_exists(id=self.database_name)
        self._container = self._database.create_container_if_not_exists(
            id=self.container_name,
            partition_key=PartitionKey(path=self.partition_key_path)
        )

        logger.info(f"✅ Long-term memory connected to Cosmos DB: {self.database_name}/{self.container_name}")

    def add_memory(
        self,
        session_id: str,
        content: str,
        memory_type: str = "conversation",
        importance_score: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a new memory to Cosmos DB.

        Args:
            session_id: Session identifier (partition key)
            content: Memory content text
            memory_type: Type of memory (conversation, trip_plan, user_query, preference)
            importance_score: Score from 0.0 to 1.0 indicating importance
            tags: Optional list of tags for filtering
            metadata: Optional additional metadata

        Returns:
            The generated memory_id
        """
        memory_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        item = {
            "id": memory_id,
            "session_id": session_id,
            "content": content,
            "memory_type": memory_type,
            "importance_score": max(0.0, min(1.0, importance_score)),
            "tags": tags or [],
            "metadata": metadata or {},
            "access_count": 0,
            "created_at": now,
            "last_accessed": now,
            "is_archived": False
        }

        try:
            self._container.upsert_item(item)
            logger.info(f"✅ Added memory {memory_id} (type={memory_type}, importance={importance_score})")
            return memory_id
        except Exception as e:
            logger.error(f"❌ Failed to add memory: {e}")
            raise

    def get_memory(self, memory_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory by ID and update access stats.

        Args:
            memory_id: The unique memory identifier
            session_id: Session identifier (partition key)

        Returns:
            Memory dict if found, None otherwise
        """
        try:
            item = self._container.read_item(item=memory_id, partition_key=session_id)

            # Update access stats
            item["access_count"] = item.get("access_count", 0) + 1
            item["last_accessed"] = datetime.now(timezone.utc).isoformat()
            self._container.upsert_item(item)

            logger.info(f"✅ Retrieved memory {memory_id} (access_count={item['access_count']})")
            return item
        except Exception as e:
            logger.error(f"❌ Failed to get memory {memory_id}: {e}")
            return None

    def search_memories(
        self,
        session_id: str,
        query: Optional[str] = None,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_importance: float = 0.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search memories with filters.

        Args:
            session_id: Session identifier
            query: Optional text to search in content
            memory_type: Optional memory type filter
            tags: Optional tags to filter by
            min_importance: Minimum importance score
            limit: Maximum results to return

        Returns:
            List of matching memories
        """
        try:
            sql_parts = ["SELECT * FROM c WHERE c.session_id = @sid"]
            params = [{"name": "@sid", "value": session_id}]

            if query:
                sql_parts.append("AND CONTAINS(LOWER(c.content), @q)")
                params.append({"name": "@q", "value": query.lower()})

            if memory_type:
                sql_parts.append("AND c.memory_type = @mt")
                params.append({"name": "@mt", "value": memory_type})

            if min_importance > 0:
                sql_parts.append("AND c.importance_score >= @imp")
                params.append({"name": "@imp", "value": min_importance})

            if tags:
                for i, tag in enumerate(tags):
                    sql_parts.append(f"AND ARRAY_CONTAINS(c.tags, @tag{i})")
                    params.append({"name": f"@tag{i}", "value": tag})

            query_str = " ".join(sql_parts)
            items = list(self._container.query_items(
                query=query_str,
                parameters=params,
                partition_key=session_id
            ))

            # Sort by importance and recency
            items.sort(key=lambda m: (m.get("importance_score", 0), m.get("last_accessed", "")), reverse=True)
            return items[:limit]

        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []

    def get_all_memories(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all memories for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of all memories in the session
        """
        try:
            query = "SELECT * FROM c WHERE c.session_id = @sid ORDER BY c.created_at DESC"
            params = [{"name": "@sid", "value": session_id}]

            items = list(self._container.query_items(
                query=query,
                parameters=params,
                partition_key=session_id
            ))
            return items
        except Exception as e:
            logger.error(f"❌ Failed to get memories: {e}")
            return []

    def get_memory_statistics(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get memory statistics.

        Args:
            session_id: Optional session to filter by

        Returns:
            Dictionary with memory statistics
        """
        try:
            if session_id:
                query = "SELECT * FROM c WHERE c.session_id = @sid"
                params = [{"name": "@sid", "value": session_id}]
                cross_partition = False
            else:
                query = "SELECT * FROM c"
                params = []
                cross_partition = True

            items = list(self._container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=cross_partition
            ))

            if not items:
                return {
                    "total_memories": 0,
                    "memory_types": {},
                    "average_importance": 0.0,
                    "average_access_count": 0.0
                }

            memory_types = {}
            importance_scores = []
            access_counts = []

            for item in items:
                mtype = item.get("memory_type", "unknown")
                memory_types[mtype] = memory_types.get(mtype, 0) + 1
                importance_scores.append(float(item.get("importance_score", 0.0)))
                access_counts.append(int(item.get("access_count", 0)))

            return {
                "total_memories": len(items),
                "memory_types": memory_types,
                "average_importance": round(sum(importance_scores) / len(importance_scores), 3),
                "average_access_count": round(sum(access_counts) / len(access_counts), 2)
            }

        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            return {}

    def delete_memory(self, memory_id: str, session_id: str) -> bool:
        """
        Delete a memory.

        Args:
            memory_id: Memory identifier
            session_id: Session identifier (partition key)

        Returns:
            True if deleted, False otherwise
        """
        try:
            self._container.delete_item(item=memory_id, partition_key=session_id)
            logger.info(f"✅ Deleted memory {memory_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete memory: {e}")
            return False

    def clear_session(self, session_id: str) -> int:
        """
        Clear all memories for a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of memories deleted
        """
        try:
            memories = self.get_all_memories(session_id)
            count = 0
            for mem in memories:
                if self.delete_memory(mem["id"], session_id):
                    count += 1
            logger.info(f"✅ Cleared {count} memories from session {session_id}")
            return count
        except Exception as e:
            logger.error(f"❌ Failed to clear session: {e}")
            return 0

    def __str__(self) -> str:
        """String representation of memory."""
        return f"LongTermMemory(db={self.database_name}, container={self.container_name})"

    def __repr__(self) -> str:
        """Detailed representation of memory."""
        stats = self.get_memory_statistics()
        return f"LongTermMemory(db={self.database_name}, container={self.container_name}, total={stats.get('total_memories', 0)})"
