# lesson-9-maintaining-long-term-agent-memory-in-python/exercises/solution/long_term_memory/optimization.py

import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

from .ai import get_openai_kernel
from .reordering import heuristic_priority_scores

logger = logging.getLogger(__name__)


async def prune_ai_optimized(container: Any,
                             max_memories: int,
                             enable_ai_scoring: bool = True) -> int:
    """
    AI-optimized pruning using OpenAI to score memories for retention.
    Archives lowest-scoring memories instead of deleting them.
    """
    try:
        if not enable_ai_scoring:
            logger.info("⚠️ AI scoring disabled, skipping AI pruning")
            return 0

        kernel = get_openai_kernel(enable_ai_scoring=True)
        if not kernel:
            logger.warning("⚠️ No OpenAI kernel available, skipping AI pruning")
            return 0

        # Load memories
        memories = list(container.query_items(
            query="SELECT * FROM c WHERE c.is_archived = false",
            enable_cross_partition_query=True
        ))
        if len(memories) <= max_memories:
            return 0

        logger.info(f"🧠 AI pruning: analyzing {len(memories)} memories")

        # Ask AI to score them
        scores = await ai_score_memories_for_retention(memories)
        scored = list(zip(memories, scores))
        scored.sort(key=lambda x: x[1])  # lowest first

        to_prune = len(memories) - max_memories
        count = 0
        for mem, score in scored[:to_prune]:
            try:
                mem["is_archived"] = True
                mem["ai_retention_score"] = score
                mem["pruned_at"] = datetime.utcnow().isoformat()
                container.upsert_item(mem)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to archive memory {mem.get('id')}: {e}")

        logger.info(f"✅ AI pruning archived {count} memories")
        return count
    except Exception as e:
        logger.error(f"❌ AI pruning failed: {e}")
        return 0


async def ai_score_memories_for_retention(memories: List[Dict[str, Any]]) -> List[float]:
    """
    Use AI to assign retention scores to memories.
    Returns list of floats 0.0–1.0.
    """
    try:
        kernel = get_openai_kernel()
        if not kernel:
            return [0.5] * len(memories)

        prompt = f"""
        You are an AI memory manager. Score each memory for retention (0.0=discard, 1.0=keep).

        Consider:
        - Importance and relevance
        - Recency
        - Uniqueness
        - Actionability
        - Emotional significance

        Memories:
        {json.dumps([{
            "id": m.get("id", ""),
            "content": m.get("content", "")[:200],
            "memory_type": m.get("memory_type", ""),
            "importance_score": m.get("importance_score", 0),
            "access_count": m.get("access_count", 0),
            "created_at": m.get("created_at", ""),
        } for m in memories], indent=2)}

        Respond with a JSON array of floats, one per memory.
        """

        fn = kernel.add_function(
            function_name="score_memories",
            plugin_name="memory_management",
            prompt=prompt
        )

        result = await kernel.invoke(fn)
        text = str(result)

        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])

    except Exception as e:
        logger.warning(f"⚠️ AI scoring fallback: {e}")

    # fallback heuristic
    return heuristic_memory_scoring(memories)


def heuristic_memory_scoring(memories: List[Dict[str, Any]]) -> List[float]:
    """Fallback scoring if AI not available."""
    scores = []
    now = datetime.utcnow()
    for m in memories:
        score = 0.0
        score += float(m.get("importance_score", 0.5)) * 0.4
        score += min(int(m.get("access_count", 0)) * 0.1, 0.3)
        try:
            created = datetime.fromisoformat(m.get("created_at", ""))
            days = (now - created).days
            score += max(0, 1 - days / 30) * 0.2
        except Exception:
            score += 0.1
        mtype = m.get("memory_type", "")
        if mtype == "knowledge":
            score += 0.1
        elif mtype == "conversation":
            score += 0.05
        scores.append(max(0.0, min(1.0, score)))
    return scores


async def reorder_memories_intelligent(container: Any,
                                       memories: List[Dict[str, Any]],
                                       enable_ai_scoring: bool = True) -> int:
    """
    Intelligent reordering using AI (or heuristics).
    Updates each memory with a priority_score.
    """
    try:
        if enable_ai_scoring:
            priorities = await calculate_intelligent_priorities(memories)
        else:
            priorities = heuristic_priority_scores(memories)

        count = 0
        for mem, score in zip(memories, priorities):
            mem["priority_score"] = score
            mem["last_reordered"] = datetime.utcnow().isoformat()
            container.upsert_item(mem)
            count += 1

        logger.info(f"✅ Reordered {count} memories intelligently")
        return count
    except Exception as e:
        logger.error(f"❌ Intelligent reordering failed: {e}")
        return 0


async def calculate_intelligent_priorities(memories: List[Dict[str, Any]]) -> List[float]:
    """
    Ask AI to calculate priority scores (0–1) for memories.
    """
    try:
        kernel = get_openai_kernel()
        if not kernel:
            return heuristic_priority_scores(memories)

        prompt = f"""
        You are an AI memory prioritization system.
        Assign priority scores (0.0–1.0) for these memories.

        Memories:
        {json.dumps([{
            "id": m.get("id", ""),
            "content": m.get("content", "")[:150],
            "memory_type": m.get("memory_type", ""),
            "importance_score": m.get("importance_score", 0),
            "access_count": m.get("access_count", 0),
            "created_at": m.get("created_at", ""),
        } for m in memories], indent=2)}

        Respond with a JSON array of floats, one per memory.
        """

        fn = kernel.add_function(
            function_name="calculate_priorities",
            plugin_name="memory_prioritization",
            prompt=prompt
        )

        result = await kernel.invoke(fn)
        text = str(result)

        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])

    except Exception as e:
        logger.warning(f"⚠️ AI priority fallback: {e}")

    return heuristic_priority_scores(memories)


async def archive_old_memories(container: Any,
                               days: int = 90,
                               importance_threshold: float = 0.3) -> int:
    """
    Archive memories older than N days and below an importance threshold.
    """
    try:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        query = """
        SELECT * FROM c
        WHERE c.created_at < @cutoff_date
        AND c.importance_score < @threshold
        AND c.is_archived = false
        """
        params = [
            {"name": "@cutoff_date", "value": cutoff},
            {"name": "@threshold", "value": importance_threshold},
        ]
        items = list(container.query_items(
            query=query, parameters=params, enable_cross_partition_query=True
        ))

        count = 0
        for mem in items:
            try:
                mem["is_archived"] = True
                mem["archived_at"] = datetime.utcnow().isoformat()
                mem["archive_reason"] = "age_and_low_importance"
                container.upsert_item(mem)
                count += 1
            except Exception as e:
                logger.warning(f"Failed to archive memory {mem.get('id')}: {e}")

        logger.info(f"📦 Archived {count} old/low-value memories")
        return count
    except Exception as e:
        logger.error(f"❌ Archiving failed: {e}")
        return 0


async def calculate_performance_improvements(container: Any,
                                             max_memories: int) -> Dict[str, Any]:
    """
    Return memory efficiency metrics.
    """
    try:
        active = list(container.query_items(
            query="SELECT VALUE COUNT(1) FROM c WHERE c.is_archived = false",
            enable_cross_partition_query=True
        ))[0]
        archived = list(container.query_items(
            query="SELECT VALUE COUNT(1) FROM c WHERE c.is_archived = true",
            enable_cross_partition_query=True
        ))[0]

        active = int(active or 0)
        archived = int(archived or 0)
        total = active + archived

        efficiency = active / max(total, 1)
        utilization = active / max(max_memories, 1)

        return {
            "total_memories": total,
            "active_memories": active,
            "archived_memories": archived,
            "memory_efficiency": efficiency,
            "storage_utilization": utilization,
            "optimization_score": min(1.0, efficiency * (1.0 - utilization)),
        }
    except Exception as e:
        logger.error(f"❌ Performance metrics failed: {e}")
        return {"error": str(e)}
