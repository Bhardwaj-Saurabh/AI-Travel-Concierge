# lesson-9-maintaining-long-term-agent-memory-in-python/exercises/solution/long_term_memory/reordering.py

import logging
from datetime import datetime
from typing import List, Any
from .models import MemoryItem

logger = logging.getLogger(__name__)


def reorder_memories(container: Any, session_id: str, strategy: str = "importance") -> int:
    """
    Reorder memories for a given session by updating a priority field in metadata.

    Args:
        container: Cosmos DB container (ContainerProxy)
        session_id: Session ID
        strategy: Strategy to reorder by ('importance', 'recency', 'access_frequency')

    Returns:
        Number of memories reordered
    """
    try:
        query = "SELECT * FROM c WHERE c.session_id = @sid"
        params = [{"name": "@sid", "value": session_id}]
        items = list(container.query_items(
            query=query,
            parameters=params,
            enable_cross_partition_query=False,
            partition_key=session_id
        ))

        memories = [MemoryItem.from_dict(i) for i in items]
        if not memories:
            return 0

        if strategy == "importance":
            memories.sort(key=lambda m: m.importance_score, reverse=True)
        elif strategy == "recency":
            memories.sort(key=lambda m: m.last_accessed, reverse=True)
        elif strategy == "access_frequency":
            memories.sort(key=lambda m: m.access_count, reverse=True)
        else:
            raise ValueError(f"Unknown reordering strategy: {strategy}")

        count = 0
        for i, mem in enumerate(memories):
            mem.metadata["priority"] = i
            container.upsert_item(mem.to_dict())
            count += 1

        logger.info(f"✅ Reordered {count} memories for session {session_id} using {strategy}")
        return count

    except Exception as e:
        logger.error(f"❌ Failed to reorder memories for session {session_id}: {e}")
        return 0


def heuristic_priority_scores(memories: List[dict]) -> List[float]:
    """
    Calculate heuristic priority scores when AI scoring is unavailable.
    Uses importance, access frequency, recency, and memory type.

    Args:
        memories: List of memory dicts (as returned from Cosmos)

    Returns:
        List of priority scores (0.0–1.0)
    """
    scores = []
    now = datetime.utcnow()

    for m in memories:
        score = 0.0

        importance = float(m.get("importance_score", 0.5))
        score += importance * 0.3

        access_count = int(m.get("access_count", 0))
        score += min(access_count * 0.2, 0.4)

        try:
            created_at = datetime.fromisoformat(m.get("created_at", ""))
            days_old = (now - created_at).days
            recency = max(0, 1.0 - (days_old / 90))  # decay over 90 days
            score += recency * 0.2
        except Exception:
            score += 0.1

        mtype = m.get("memory_type", "")
        if mtype == "knowledge":
            score += 0.1
        elif mtype == "system_event":
            score += 0.05

        scores.append(max(0.0, min(1.0, score)))

    return scores
