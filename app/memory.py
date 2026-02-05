# app/memory.py
"""
Short-term memory system for session-based context management.

Implements conversation history tracking with sliding window eviction,
token management, and search capabilities.
"""

import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


class ShortTermMemory:
    """
    Short-term memory system for session-based context management.

    Features:
    - Store conversation history (user/assistant messages)
    - Track tool calls and system events
    - Implement sliding window eviction by items and tokens
    - Search and filter memory items
    - Export/import memory state
    """

    def __init__(self, max_items: int = 10, max_tokens: int = 2000):
        """
        Initialize short-term memory.

        Args:
            max_items: Maximum number of items to store (default 10)
            max_tokens: Maximum number of tokens to store (default 2000)
        """
        self.max_items = max_items
        self.max_tokens = max_tokens
        self.memory_items: List[Dict[str, Any]] = []
        self.total_tokens = 0
        self.session_id = str(uuid.uuid4())
        self.created_at = datetime.now(timezone.utc).isoformat()

    def add_conversation(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add user/assistant messages to memory.

        Args:
            role: 'user' or 'assistant'
            content: The message content
            metadata: Optional metadata dictionary
        """
        tokens = self._estimate_tokens(content)
        item = {
            "role": role,
            "content": content,
            "tokens": tokens,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}
        }
        self.memory_items.append(item)
        self.total_tokens += tokens
        self._evict_if_needed()

    def add_tool_call(self, tool_name: str, input_data: Dict[str, Any],
                      output_data: Any, success: bool = True):
        """
        Add a tool call record to memory.

        Args:
            tool_name: Name of the tool called
            input_data: Input arguments to the tool
            output_data: Output/result from the tool
            success: Whether the tool call was successful
        """
        content = f"Tool call: {tool_name}"
        tokens = self._estimate_tokens(content)

        item = {
            "role": "assistant",
            "content": content,
            "tokens": tokens,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "type": "tool_call",
                "tool_name": tool_name,
                "input": input_data,
                "output": output_data,
                "success": success
            }
        }
        self.memory_items.append(item)
        self.total_tokens += tokens
        self._evict_if_needed()

    def add_system_event(self, event_message: str, event_data: Optional[Dict[str, Any]] = None):
        """
        Add a system event to memory.

        Args:
            event_message: Description of the system event
            event_data: Optional additional event data
        """
        tokens = self._estimate_tokens(event_message)

        item = {
            "role": "system",
            "content": event_message,
            "tokens": tokens,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {
                "type": "system_event",
                "event": event_message,
                "data": event_data or {}
            }
        }
        self.memory_items.append(item)
        self.total_tokens += tokens
        self._evict_if_needed()

    def _evict_if_needed(self):
        """Implement sliding window eviction when limits are exceeded."""
        # Evict by items first (FIFO)
        while len(self.memory_items) > self.max_items:
            removed = self.memory_items.pop(0)
            self.total_tokens -= removed.get("tokens", 0)

        # Then evict by tokens
        while self.total_tokens > self.max_tokens and self.memory_items:
            removed = self.memory_items.pop(0)
            self.total_tokens -= removed.get("tokens", 0)

        # Ensure total_tokens doesn't go negative
        self.total_tokens = max(0, self.total_tokens)

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Uses a rough approximation of ~4 characters per token.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        if not text:
            return 0
        # Rough estimation: ~4 characters per token for English text
        return max(1, len(text) // 4)

    def get_conversation_history(self, include_metadata: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history.

        Args:
            include_metadata: Whether to include metadata in results

        Returns:
            List of conversation items
        """
        if include_metadata:
            return [item.copy() for item in self.memory_items]

        # Return without metadata
        return [
            {
                "role": item["role"],
                "content": item["content"],
                "timestamp": item["timestamp"]
            }
            for item in self.memory_items
        ]

    def get_recent_conversation(self, n: int) -> List[Dict[str, Any]]:
        """
        Get the most recent n conversation items.

        Args:
            n: Number of items to retrieve

        Returns:
            List of recent items
        """
        return [item.copy() for item in self.memory_items[-n:]]

    def get_memory_summary(self) -> Dict[str, Any]:
        """
        Get a summary of memory state.

        Returns:
            Dictionary with memory statistics
        """
        summary = {
            "session_id": self.session_id,
            "total_items": len(self.memory_items),
            "total_tokens": self.total_tokens,
            "max_items": self.max_items,
            "max_tokens": self.max_tokens,
            "memory_usage_percent": (len(self.memory_items) / self.max_items * 100) if self.max_items > 0 else 0,
            "oldest_item": None,
            "newest_item": None
        }

        if self.memory_items:
            summary["oldest_item"] = self.memory_items[0].get("timestamp")
            summary["newest_item"] = self.memory_items[-1].get("timestamp")

        return summary

    def search_memory(self, query: str, role_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search through memory items.

        Args:
            query: Search query string
            role_filter: Optional role to filter by ('user', 'assistant', 'system')

        Returns:
            List of matching memory items
        """
        results = []
        query_lower = query.lower()

        for item in self.memory_items:
            # Apply role filter if specified
            if role_filter and item.get("role") != role_filter:
                continue

            # Search in content
            content = item.get("content", "").lower()
            if query_lower in content:
                results.append(item.copy())
                continue

            # Search in metadata (for tool calls)
            metadata = item.get("metadata", {})
            if metadata.get("tool_name", "").lower() == query_lower:
                results.append(item.copy())

        return results

    def clear_memory(self):
        """Clear all memory items."""
        self.memory_items = []
        self.total_tokens = 0

    def export_memory(self, file_path: str):
        """
        Export memory state to a JSON file.

        Args:
            file_path: Path to export file
        """
        export_data = {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "max_items": self.max_items,
            "max_tokens": self.max_tokens,
            "total_tokens": self.total_tokens,
            "memory_items": self.memory_items
        }

        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)

    def import_memory(self, file_path: str):
        """
        Import memory state from a JSON file.

        Args:
            file_path: Path to import file
        """
        with open(file_path, 'r') as f:
            import_data = json.load(f)

        self.session_id = import_data.get("session_id", self.session_id)
        self.created_at = import_data.get("created_at", self.created_at)
        self.max_items = import_data.get("max_items", self.max_items)
        self.max_tokens = import_data.get("max_tokens", self.max_tokens)
        self.total_tokens = import_data.get("total_tokens", 0)
        self.memory_items = import_data.get("memory_items", [])

    def get_context_window(self, max_tokens: Optional[int] = None) -> str:
        """
        Get a formatted context window for LLM prompts.

        Args:
            max_tokens: Optional maximum tokens to include

        Returns:
            Formatted string of context
        """
        if max_tokens is None:
            max_tokens = self.max_tokens

        context_parts = []
        token_count = 0

        # Iterate from oldest to newest
        for item in self.memory_items:
            role = item.get("role", "unknown").upper()
            content = item.get("content", "")
            item_tokens = item.get("tokens", self._estimate_tokens(content))

            # Check if adding this item would exceed token limit
            if token_count + item_tokens > max_tokens:
                break

            context_parts.append(f"{role}: {content}")
            token_count += item_tokens

        if not context_parts:
            return "No conversation history."
        return "\n".join(context_parts)

    def __str__(self) -> str:
        """String representation of memory."""
        return f"ShortTermMemory(session_id={self.session_id}, items={len(self.memory_items)}, tokens={self.total_tokens})"

    def __repr__(self) -> str:
        """Detailed representation of memory."""
        return f"ShortTermMemory(session_id={self.session_id}, max_items={self.max_items}, max_tokens={self.max_tokens}, current_items={len(self.memory_items)}, current_tokens={self.total_tokens})"
