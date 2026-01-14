# lesson-9-maintaining-long-term-agent-memory-in-python/exercises/solution/long_term_memory/pruning.py

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


def prune_by_importance(container: Any, importance_threshold: float) -> int:
    """Delete memories below an importance threshold."""
    try:
        query = """
        SELECT c.id, c.session_id 
        FROM c 
        WHERE c.importance_score < @threshold
        """
        params = [{"name": "@threshold", "value": importance_threshold}]
        items = list(container.query_items(
            query=query, parameters=params, enable_cross_partition_query=True
        ))

        count = 0
        for item in items:
            try:
                container.delete_item(item=item["id"], partition_key=item["session_id"])
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete memory {item['id']}: {e}")
        return count
    except Exception as e:
        logger.error(f"❌ Failed to prune by importance: {e}")
        return 0


def prune_by_age(container: Any, days: int = 30) -> int:
    """Delete memories older than `days` days."""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = """
        SELECT c.id, c.session_id 
        FROM c 
        WHERE c.created_at < @cutoff_date
        """
        params = [{"name": "@cutoff_date", "value": cutoff.isoformat()}]
        items = list(container.query_items(
            query=query, parameters=params, enable_cross_partition_query=True
        ))

        count = 0
        for item in items:
            try:
                container.delete_item(item=item["id"], partition_key=item["session_id"])
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete memory {item['id']}: {e}")
        return count
    except Exception as e:
        logger.error(f"❌ Failed to prune by age: {e}")
        return 0


def prune_by_access_frequency(container: Any, min_accesses: int = 2) -> int:
    """Delete memories with fewer than `min_accesses`."""
    try:
        query = """
        SELECT c.id, c.session_id 
        FROM c 
        WHERE c.access_count < @min_accesses
        """
        params = [{"name": "@min_accesses", "value": min_accesses}]
        items = list(container.query_items(
            query=query, parameters=params, enable_cross_partition_query=True
        ))

        count = 0
        for item in items:
            try:
                container.delete_item(item=item["id"], partition_key=item["session_id"])
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete memory {item['id']}: {e}")
        return count
    except Exception as e:
        logger.error(f"❌ Failed to prune by access frequency: {e}")
        return 0


def prune_hybrid(container: Any, max_memories: int) -> int:
    """
    Hybrid strategy: score memories by importance + recency + access,
    then delete lowest scoring ones until under the limit.
    """
    try:
        query = """
        SELECT c.id, c.session_id, c.importance_score, c.access_count, c.created_at
        FROM c
        """
        all_memories = list(container.query_items(
            query=query, parameters=[], enable_cross_partition_query=True
        ))

        now = datetime.utcnow()
        scored = []
        for mem in all_memories:
            try:
                age_days = (now - datetime.fromisoformat(mem["created_at"])).days
                age_factor = max(0, 1 - (age_days / 365))  # decay over 1 year
                access_factor = min(1, mem["access_count"] / 10)
                score = (
                    mem["importance_score"] * 0.5 +
                    age_factor * 0.3 +
                    access_factor * 0.2
                )
                scored.append((mem, score))
            except Exception:
                scored.append((mem, 0.0))

        scored.sort(key=lambda x: x[1])  # lowest first

        to_delete = max(0, len(all_memories) - max_memories)
        count = 0
        for mem, _ in scored[:to_delete]:
            try:
                container.delete_item(item=mem["id"], partition_key=mem["session_id"])
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete memory {mem['id']}: {e}")
        return count
    except Exception as e:
        logger.error(f"❌ Failed to prune hybrid: {e}")
        return 0
