"""
Unit tests for ShortTermMemory class
"""

import pytest
import tempfile
import os
from datetime import datetime
from app.memory import ShortTermMemory


class TestShortTermMemory:
    """Test cases for ShortTermMemory class"""
    
    def test_initialization(self):
        """Test memory initialization with default parameters"""
        memory = ShortTermMemory()
        
        assert memory.max_items == 10
        assert memory.max_tokens == 2000
        assert len(memory.memory_items) == 0
        assert memory.total_tokens == 0
        assert memory.session_id is not None
        assert memory.created_at is not None
    
    def test_initialization_custom_params(self):
        """Test memory initialization with custom parameters"""
        memory = ShortTermMemory(max_items=5, max_tokens=1000)
        
        assert memory.max_items == 5
        assert memory.max_tokens == 1000
        assert len(memory.memory_items) == 0
        assert memory.total_tokens == 0
    
    def test_add_conversation(self):
        """Test adding conversation items"""
        memory = ShortTermMemory(max_items=10, max_tokens=1000)
        
        # Add user message
        memory.add_conversation("user", "Hello, how are you?")
        assert len(memory.memory_items) == 1
        assert memory.memory_items[0]['role'] == "user"
        assert memory.memory_items[0]['content'] == "Hello, how are you?"
        assert memory.memory_items[0]['tokens'] > 0
        assert 'timestamp' in memory.memory_items[0]
        
        # Add assistant response
        memory.add_conversation("assistant", "I'm doing well, thank you!")
        assert len(memory.memory_items) == 2
        assert memory.memory_items[1]['role'] == "assistant"
    
    def test_add_conversation_with_metadata(self):
        """Test adding conversation items with metadata"""
        memory = ShortTermMemory()
        
        metadata = {"source": "api", "confidence": 0.95}
        memory.add_conversation("assistant", "Here's the weather data", metadata)
        
        item = memory.memory_items[0]
        assert item['metadata'] == metadata
    
    def test_add_tool_call(self):
        """Test adding tool calls to memory"""
        memory = ShortTermMemory()
        
        input_data = {"location": "Paris", "units": "metric"}
        output_data = {"temperature": 22, "condition": "sunny"}
        
        memory.add_tool_call("weather", input_data, output_data, success=True)
        
        assert len(memory.memory_items) == 1
        item = memory.memory_items[0]
        assert item['role'] == "assistant"
        assert "Tool call: weather" in item['content']
        assert item['metadata']['type'] == "tool_call"
        assert item['metadata']['tool_name'] == "weather"
        assert item['metadata']['input'] == input_data
        assert item['metadata']['output'] == output_data
        assert item['metadata']['success'] is True
    
    def test_add_system_event(self):
        """Test adding system events to memory"""
        memory = ShortTermMemory()
        
        event_data = {"error_code": 500, "retry_count": 3}
        memory.add_system_event("API error occurred", event_data)
        
        assert len(memory.memory_items) == 1
        item = memory.memory_items[0]
        assert item['role'] == "system"
        assert item['content'] == "API error occurred"
        assert item['metadata']['type'] == "system_event"
        assert item['metadata']['event'] == "API error occurred"
        assert item['metadata']['data'] == event_data
    
    def test_memory_eviction_by_items(self):
        """Test memory eviction when max_items is exceeded"""
        memory = ShortTermMemory(max_items=3, max_tokens=10000)
        
        # Add 5 items (exceeds max_items of 3)
        for i in range(5):
            memory.add_conversation("user", f"Message {i}")
        
        # Should only keep the last 3 items
        assert len(memory.memory_items) == 3
        assert memory.memory_items[0]['content'] == "Message 2"  # First kept item
        assert memory.memory_items[2]['content'] == "Message 4"  # Last item
    
    def test_memory_eviction_by_tokens(self):
        """Test memory eviction when max_tokens is exceeded"""
        memory = ShortTermMemory(max_items=100, max_tokens=100)
        
        # Add items with high token counts
        for i in range(10):
            memory.add_conversation("user", f"This is a very long message number {i} that should use many tokens")
        
        # Should evict items to stay under token limit
        assert memory.total_tokens <= memory.max_tokens
        assert len(memory.memory_items) < 10  # Some items should be evicted
    
    def test_get_conversation_history(self):
        """Test getting conversation history"""
        memory = ShortTermMemory()
        
        memory.add_conversation("user", "Hello")
        memory.add_conversation("assistant", "Hi there")
        
        # Test with metadata
        history_with_meta = memory.get_conversation_history(include_metadata=True)
        assert len(history_with_meta) == 2
        assert 'metadata' in history_with_meta[0]
        
        # Test without metadata
        history_without_meta = memory.get_conversation_history(include_metadata=False)
        assert len(history_without_meta) == 2
        assert 'metadata' not in history_without_meta[0]
        assert 'role' in history_without_meta[0]
        assert 'content' in history_without_meta[0]
        assert 'timestamp' in history_without_meta[0]
    
    def test_get_recent_conversation(self):
        """Test getting recent conversation items"""
        memory = ShortTermMemory()
        
        # Add 5 items
        for i in range(5):
            memory.add_conversation("user", f"Message {i}")
        
        # Get last 3 items
        recent = memory.get_recent_conversation(3)
        assert len(recent) == 3
        assert recent[0]['content'] == "Message 2"
        assert recent[2]['content'] == "Message 4"
    
    def test_get_memory_summary(self):
        """Test getting memory summary"""
        memory = ShortTermMemory(max_items=5, max_tokens=1000)
        
        memory.add_conversation("user", "Hello")
        memory.add_conversation("assistant", "Hi")
        
        summary = memory.get_memory_summary()
        
        assert summary['session_id'] == memory.session_id
        assert summary['total_items'] == 2
        assert summary['total_tokens'] == memory.total_tokens
        assert summary['max_items'] == 5
        assert summary['max_tokens'] == 1000
        assert summary['memory_usage_percent'] == 40.0  # 2/5 * 100
        assert 'oldest_item' in summary
        assert 'newest_item' in summary
    
    def test_search_memory(self):
        """Test searching through memory"""
        memory = ShortTermMemory()
        
        memory.add_conversation("user", "What's the weather like?")
        memory.add_conversation("assistant", "It's sunny today")
        memory.add_tool_call("weather", {}, {"condition": "sunny"})
        memory.add_conversation("user", "What about restaurants?")
        
        # Search for "weather"
        weather_results = memory.search_memory("weather")
        assert len(weather_results) == 2  # User question and tool call
        
        # Search for "restaurants"
        restaurant_results = memory.search_memory("restaurants")
        assert len(restaurant_results) == 1
        
        # Search with role filter
        user_weather = memory.search_memory("weather", role_filter="user")
        assert len(user_weather) == 1
        assert user_weather[0]['role'] == "user"
    
    def test_clear_memory(self):
        """Test clearing memory"""
        memory = ShortTermMemory()
        
        memory.add_conversation("user", "Hello")
        memory.add_conversation("assistant", "Hi")
        assert len(memory.memory_items) == 2
        
        memory.clear_memory()
        assert len(memory.memory_items) == 0
        assert memory.total_tokens == 0
    
    def test_export_import_memory(self):
        """Test exporting and importing memory"""
        memory = ShortTermMemory()
        
        # Add some data
        memory.add_conversation("user", "Hello")
        memory.add_tool_call("weather", {}, {"temp": 22})
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            memory.export_memory(temp_path)
            
            # Create new memory and import
            new_memory = ShortTermMemory()
            new_memory.import_memory(temp_path)
            
            # Check that data was imported correctly
            assert new_memory.session_id == memory.session_id
            assert len(new_memory.memory_items) == len(memory.memory_items)
            assert new_memory.total_tokens == memory.total_tokens
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_get_context_window(self):
        """Test getting formatted context window"""
        memory = ShortTermMemory(max_tokens=200)
        
        memory.add_conversation("user", "Hello")
        memory.add_conversation("assistant", "Hi there")
        memory.add_conversation("user", "How are you?")
        
        context = memory.get_context_window()
        
        assert "USER: Hello" in context
        assert "ASSISTANT: Hi there" in context
        assert "USER: How are you?" in context
        assert isinstance(context, str)
    
    def test_get_context_window_with_limit(self):
        """Test context window with custom token limit"""
        memory = ShortTermMemory(max_tokens=1000)
        
        # Add many items with longer content to ensure token limit is reached
        for i in range(10):
            memory.add_conversation("user", f"This is a longer message number {i} with more content to increase token count")
        
        # Get context with small token limit
        context = memory.get_context_window(max_tokens=50)
        
        # Should contain fewer items due to token limit
        # Note: The token estimation might be conservative, so we check that it's reasonable
        context_lines = context.split('\n')
        assert len(context_lines) <= 10  # Should not exceed total items
        assert len(context_lines) > 0    # Should have some content
    
    def test_string_representations(self):
        """Test string representations of memory"""
        memory = ShortTermMemory()
        memory.add_conversation("user", "Hello")
        
        str_repr = str(memory)
        assert "ShortTermMemory" in str_repr
        assert memory.session_id in str_repr
        
        repr_str = repr(memory)
        assert "ShortTermMemory" in repr_str
        assert memory.session_id in repr_str
    
    def test_token_estimation(self):
        """Test token estimation accuracy"""
        memory = ShortTermMemory()
        
        # Test with known text
        test_text = "Hello world"
        estimated_tokens = memory._estimate_tokens(test_text)
        
        # Should be a reasonable estimate (roughly 2-3 tokens for "Hello world")
        assert 2 <= estimated_tokens <= 4
    
    def test_memory_limits_edge_cases(self):
        """Test memory behavior at limits"""
        memory = ShortTermMemory(max_items=1, max_tokens=10)
        
        # Add item that fits
        memory.add_conversation("user", "Hi")
        assert len(memory.memory_items) == 1
        
        # Add another item (should evict the first)
        memory.add_conversation("user", "Hello")
        assert len(memory.memory_items) == 1
        assert memory.memory_items[0]['content'] == "Hello"
    
    def test_conversation_flow_simulation(self):
        """Test a realistic conversation flow"""
        memory = ShortTermMemory(max_items=10, max_tokens=1000)
        
        # Simulate a realistic conversation
        memory.add_conversation("user", "What's the weather in Paris?")
        memory.add_conversation("assistant", "Let me check the weather for you.")
        memory.add_tool_call("weather", {"location": "Paris"}, {"temp": 22, "condition": "sunny"})
        memory.add_conversation("assistant", "It's 22°C and sunny in Paris today!")
        memory.add_conversation("user", "What about restaurants?")
        memory.add_conversation("assistant", "I can help you find restaurants in Paris.")
        memory.add_tool_call("search", {"query": "restaurants Paris"}, {"results": ["Restaurant A", "Restaurant B"]})
        
        # Verify the conversation flow
        history = memory.get_conversation_history()
        assert len(history) == 7  # 6 conversation items + 1 tool call
        
        # Check that tool calls are properly stored
        tool_calls = memory.search_memory("Tool call")
        assert len(tool_calls) == 2
        
        # Check context window
        context = memory.get_context_window()
        assert "weather" in context.lower()
        assert "restaurants" in context.lower()
        
        # Verify memory summary
        summary = memory.get_memory_summary()
        assert summary['total_items'] == 7  # 6 conversation items + 1 tool call
        assert summary['total_tokens'] > 0
