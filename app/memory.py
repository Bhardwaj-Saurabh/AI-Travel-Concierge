# app/memory.py
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

class ShortTermMemory:
    """
    Short-term memory system for session-based context management.
    
    TODO: Implement short-term memory functionality
    - Store conversation history and context
    - Implement sliding window eviction
    - Provide methods to add, retrieve, and clear memories
    - Handle memory limits and cleanup
    """
    
    def __init__(self, max_memories: int = 100):
        # TODO: Initialize memory storage
        # This is a placeholder - replace with actual implementation
        self.max_memories = max_memories
        self.memories: List[Dict[str, Any]] = []
    
    def add_memory(self, content: str, memory_type: str = "conversation"):
        """
        Add a new memory to short-term storage.

        Stores memory with timestamp and type, implements sliding window eviction when needed.
        """
        memory = {
            "content": content,
            "memory_type": memory_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        self.memories.append(memory)
        self._evict_if_needed()

    def _evict_if_needed(self):
        """Implement sliding window eviction when memory limit is exceeded."""
        if len(self.memories) > self.max_memories:
            # Remove oldest memories (FIFO)
            self.memories = self.memories[-self.max_memories:]

    def get_memories(self, memory_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve memories from short-term storage.

        Filters by memory type if specified, returns memories in chronological order.
        """
        if memory_type is None:
            return self.memories.copy()

        return [m for m in self.memories if m["memory_type"] == memory_type]

    def clear_memories(self):
        """
        Clear all short-term memories.
        """
        self.memories = []