# lesson-9-maintaining-long-term-agent-memory-in-python/exercises/solution/long_term_memory/models.py

from dataclasses import dataclass, asdict, fields
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class MemoryItem:
    """
    Represents a single memory entry in long-term storage.
    """
    id: str
    session_id: str
    content: str
    memory_type: str
    importance_score: float
    access_count: int
    last_accessed: datetime
    created_at: datetime
    tags: List[str]
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

    # Optimization fields
    priority_score: float = 0.0
    relevance_score: float = 0.0
    memory_size: int = 0
    access_frequency: float = 0.0
    decay_factor: float = 1.0
    is_archived: bool = False
    retention_priority: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for Cosmos DB storage.
        Ensures datetime fields are serialized as ISO strings.
        """
        data = asdict(self)
        data["last_accessed"] = self.last_accessed.isoformat()
        data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        """
        Create a MemoryItem from a dictionary (e.g. loaded from Cosmos DB).
        Ignores Cosmos system fields (_rid, _etag, etc.).
        Safely parses datetime fields.
        """
        allowed = {f.name for f in fields(cls)}
        clean = {k: v for k, v in data.items() if k in allowed}
        clean.setdefault("tags", [])
        clean.setdefault("metadata", {})

        for key in ("last_accessed", "created_at"):
            val = clean.get(key)
            if isinstance(val, str):
                try:
                    clean[key] = datetime.fromisoformat(val)
                except Exception:
                    clean[key] = datetime.utcnow()
            elif not isinstance(val, datetime):
                clean[key] = datetime.utcnow()

        return cls(**clean)
