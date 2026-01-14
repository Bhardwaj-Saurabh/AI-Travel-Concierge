# lesson-9-maintaining-long-term-agent-memory-in-python/exercises/solution/long_term_memory/core.py

import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from .models import MemoryItem
from .db import get_cosmos_client, get_container
from .ai import get_openai_kernel
from .pruning import prune_by_importance, prune_by_age, prune_by_access_frequency, prune_hybrid
from .reordering import reorder_memories
from .optimization import (
    prune_ai_optimized,
    reorder_memories_intelligent,
    archive_old_memories,
    calculate_performance_improvements,
)

logger = logging.getLogger(__name__)


class LongTermMemory:
    """
    High-level class for managing long-term memory:
    - Adds, retrieves, updates memories
    - Applies pruning/reordering
    - Uses AI for optimization
    """

    def __init__(self,
                 database_name: str = "agent_memory",
                 container_name: str = "memories",
                 max_memories: int = 1000,
                 importance_threshold: float = 0.3,
                 enable_ai_scoring: bool = True):
        self.database_name = database_name
        self.container_name = container_name
        self.max_memories = max_memories
        self.importance_threshold = importance_threshold
        self.enable_ai_scoring = enable_ai_scoring

        # Initialize Cosmos
        get_cosmos_client(database_name=self.database_name, container_name=self.container_name)
        self._container = get_container()

        # Initialize AI kernel lazily
        self._kernel = get_openai_kernel(enable_ai_scoring)

        # Pruning strategies map
        self.pruning_strategies = {
            "importance": lambda: prune_by_importance(self._container, self.importance_threshold),
            "age": lambda: prune_by_age(self._container, 30),
            "access_frequency": lambda: prune_by_access_frequency(self._container, 2),
            "hybrid": lambda: prune_hybrid(self._container, self.max_memories),
        }

    # ---------------- Core operations ----------------

    async def add_memory(self,
                         session_id: str,
                         content: str,
                         memory_type: str = "conversation",
                         importance_score: float = 0.5,
                         tags: Optional[List[str]] = None,
                         metadata: Optional[Dict[str, Any]] = None,
                         embedding: Optional[List[float]] = None,
                         context: Optional[str] = None) -> str:
        """Add a new memory to Cosmos DB."""
        memory_id = str(uuid.uuid4())
        now = datetime.utcnow()
        item = MemoryItem(
            id=memory_id,
            session_id=session_id,
            content=content,
            memory_type=memory_type,
            importance_score=importance_score,
            access_count=0,
            last_accessed=now,
            created_at=now,
            tags=tags or [],
            metadata=metadata or {},
            embedding=embedding,
        )
        # TODO: Add memory to Cosmos DB
        logger.info(f"✅ Added memory {memory_id} (importance={importance_score})")

        self._check_and_prune_if_needed()
        return memory_id

    def get_memory(self, memory_id: str, session_id: str) -> Optional[MemoryItem]:
        """Retrieve memory by id and increment access stats."""
        try:
            # TODO: Get memory from Cosmos DB
            mem = MemoryItem.from_dict(item)
            mem.access_count += 1
            mem.last_accessed = datetime.utcnow()
            self._container.upsert_item(mem.to_dict())
            return mem
        except Exception as e:
            logger.error(f"❌ Failed to get memory {memory_id}: {e}")
            return None

    def get_memory_statistics(self, session_id: str = None) -> Dict[str, Any]:
        """Get memory statistics across all sessions or a single session."""
        try:
            if session_id:
                query = "SELECT * FROM c WHERE c.session_id = @sid"
                params = [{"name": "@sid", "value": session_id}]
                enable_cross = False
            else:
                query = "SELECT * FROM c"
                params = []
                enable_cross = True

            items = list(self._container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=enable_cross
            ))

            if not items:
                return {
                    "total_memories": 0,
                    "memory_types": {},
                    "average_importance": 0.0,
                    "average_access_count": 0.0,
                    "oldest_memory": None,
                    "newest_memory": None,
                }

            memory_types = {}
            importance_scores, access_counts, created_dates = [], [], []

            for mem in items:
                mtype = mem.get("memory_type", "unknown")
                memory_types[mtype] = memory_types.get(mtype, 0) + 1
                importance_scores.append(float(mem.get("importance_score", 0.0)))
                access_counts.append(int(mem.get("access_count", 0)))
                try:
                    created_dates.append(datetime.fromisoformat(mem.get("created_at")))
                except Exception:
                    pass

            return {
                "total_memories": len(items),
                "memory_types": memory_types,
                "average_importance": round(sum(importance_scores)/len(importance_scores), 3),
                "average_access_count": round(sum(access_counts)/len(access_counts), 2),
                "oldest_memory": min(created_dates).isoformat() if created_dates else None,
                "newest_memory": max(created_dates).isoformat() if created_dates else None,
            }
        except Exception as e:
            logger.error(f"❌ Failed to calculate memory statistics: {e}")
            return {}

    
    def search_memories(self,
                        session_id: str,
                        query: Optional[str] = None,
                        memory_type: Optional[str] = None,
                        tags: Optional[List[str]] = None,
                        min_importance: float = 0.0,
                        limit: int = 10) -> List[MemoryItem]:
        """Search memories with filters."""
        try:
            sql = ["SELECT * FROM c WHERE c.session_id = @sid"]
            params = [{"name": "@sid", "value": session_id}]

            if query:
                sql.append("AND CONTAINS(LOWER(c.content), @q)")
                params.append({"name": "@q", "value": query.lower()})
            if memory_type:
                sql.append("AND c.memory_type = @mt")
                params.append({"name": "@mt", "value": memory_type})
            if min_importance > 0:
                sql.append("AND c.importance_score >= @imp")
                params.append({"name": "@imp", "value": min_importance})
            if tags:
                for i, t in enumerate(tags):
                    sql.append(f"AND ARRAY_CONTAINS(c.tags, @tag{i})")
                    params.append({"name": f"@tag{i}", "value": t})

            query_str = " ".join(sql)
            items = list(self._container.query_items(
                query=query_str,
                parameters=params,
                enable_cross_partition_query=False,
                partition_key=session_id
            ))
            memories = [MemoryItem.from_dict(i) for i in items]
            memories.sort(key=lambda m: (m.importance_score, m.last_accessed), reverse=True)
            return memories[:limit]
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []

    def update_memory_importance(self, memory_id: str, session_id: str, new_importance: float) -> bool:
        """Update importance score of a memory."""
        mem = self.get_memory(memory_id, session_id)
        if not mem:
            return False
        mem.importance_score = max(0.0, min(1.0, new_importance))
        self._container.upsert_item(mem.to_dict())
        logger.info(f"Updated memory {memory_id} importance to {new_importance}")
        return True

    # ---------------- Pruning & Reordering ----------------

    def _check_and_prune_if_needed(self):
        """Run pruning if memory count exceeds max_memories."""
        try:
            count = list(self._container.query_items(
                query="SELECT VALUE COUNT(1) FROM c",
                enable_cross_partition_query=True
            ))[0]
            if count > self.max_memories:
                self.prune_memories("hybrid")
        except Exception as e:
            logger.error(f"❌ Check/prune failed: {e}")

    def prune_memories(self, strategy: str = "hybrid") -> int:
        """Run a specific pruning strategy."""
        if strategy not in self.pruning_strategies:
            raise ValueError(f"Unknown pruning strategy: {strategy}")
        return self.pruning_strategies[strategy]()

    def reorder_memories(self, session_id: str, strategy: str = "importance") -> int:
        """Reorder memories using a basic strategy."""
        return reorder_memories(self._container, session_id, strategy)

    # ---------------- AI Optimization ----------------

    async def optimize_memory_performance(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run comprehensive optimization:
        - AI pruning
        - Intelligent reordering
        - Archiving
        - Performance metrics
        """
        results = {"pruned": 0, "reordered": 0, "archived": 0, "metrics": {}}

        results["pruned"] = await prune_ai_optimized(
            self._container, self.max_memories, self.enable_ai_scoring
        )

        # Reorder all active memories (or filter by session_id)
        query = "SELECT * FROM c WHERE c.is_archived = false"
        params = []
        if session_id:
            query += " AND c.session_id = @sid"
            params.append({"name": "@sid", "value": session_id})
        memories = list(self._container.query_items(
            query=query, parameters=params, enable_cross_partition_query=not session_id
        ))

        results["reordered"] = await reorder_memories_intelligent(
            self._container, memories, self.enable_ai_scoring
        )
        results["archived"] = await archive_old_memories(self._container)
        results["metrics"] = await calculate_performance_improvements(
            self._container, self.max_memories
        )
        return results
