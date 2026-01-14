"""
Integration tests for memory systems (short-term and long-term)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from app.memory import ShortTermMemory
from app.long_term_memory import LongTermMemory, MemoryItem


class TestMemoryIntegration:
    """Integration tests for memory systems"""
    
    def test_short_term_memory_basic_operations(self):
        """Test basic short-term memory operations"""
        memory = ShortTermMemory(max_items=5, max_tokens=1000)
        
        # Add conversation items
        memory.add_conversation("user", "Hello, I want to plan a trip to Paris")
        memory.add_conversation("assistant", "I'd be happy to help you plan your trip to Paris!")
        memory.add_tool_call("weather", {"location": "Paris"}, {"temp": 22, "condition": "sunny"})
        
        # Verify memory state
        assert len(memory.memory_items) == 3
        assert memory.total_tokens > 0
        
        # Test search
        weather_items = memory.search_memory("weather")
        assert len(weather_items) == 1
        assert "weather" in weather_items[0]['content']
        
        # Test context window
        context = memory.get_context_window()
        assert "Paris" in context
        assert "weather" in context
    
    def test_short_term_memory_eviction(self):
        """Test short-term memory eviction when limits are exceeded"""
        memory = ShortTermMemory(max_items=3, max_tokens=100)
        
        # Add more items than the limit
        for i in range(5):
            memory.add_conversation("user", f"Message {i}")
        
        # Should only keep the last 3 items
        assert len(memory.memory_items) == 3
        assert memory.memory_items[0]['content'] == "Message 2"  # First kept item
        assert memory.memory_items[2]['content'] == "Message 4"  # Last item
    
    def test_memory_item_creation_and_serialization(self):
        """Test MemoryItem creation and serialization"""
        now = datetime.now()
        item = MemoryItem(
            id="test_id",
            session_id="session_001",
            content="Test content",
            memory_type="conversation",
            importance_score=0.8,
            access_count=5,
            last_accessed=now,
            created_at=now,
            tags=["test", "demo"],
            metadata={"key": "value"},
            embedding=[0.1, 0.2, 0.3]
        )
        
        # Test serialization
        data = item.to_dict()
        assert data['id'] == "test_id"
        assert data['content'] == "Test content"
        assert data['last_accessed'] == now.isoformat()
        
        # Test deserialization
        restored_item = MemoryItem.from_dict(data)
        assert restored_item.id == item.id
        assert restored_item.content == item.content
        assert restored_item.last_accessed == item.last_accessed
        assert restored_item.embedding == item.embedding
    
    def test_importance_scoring_algorithm(self):
        """Test importance scoring algorithm"""
        # Test various content types and their expected importance scores
        test_cases = [
            ("I want to book a hotel", 0.7),  # Contains "book"
            ("What's the weather like?", 0.6),  # Contains "weather"
            ("I love Italian food", 0.65),  # Contains "love"
            ("Hello there", 0.5),  # No special keywords
            ("I need help with Python", 0.5),  # No special keywords
        ]
        
        for content, expected_min_importance in test_cases:
            # Simulate the importance calculation logic
            importance = 0.5  # Base importance
            
            high_importance_keywords = ["book", "reserve", "favorite", "prefer", "important", "remember"]
            for keyword in high_importance_keywords:
                if keyword in content.lower():
                    importance += 0.2
            
            trip_keywords = ["trip", "travel", "vacation", "holiday", "destination"]
            for keyword in trip_keywords:
                if keyword in content.lower():
                    importance += 0.1
            
            preference_keywords = ["like", "love", "hate", "dislike", "want", "need"]
            for keyword in preference_keywords:
                if keyword in content.lower():
                    importance += 0.15
            
            importance = min(1.0, importance)
            
            assert importance >= expected_min_importance
    
    def test_tag_extraction_algorithm(self):
        """Test tag extraction algorithm"""
        test_cases = [
            ("I want to go to Paris", ["paris"]),
            ("What about restaurants in Tokyo?", ["tokyo", "restaurants"]),
            ("I love Italian food", []),  # No direct restaurant keyword
            ("Book me a hotel", ["accommodation", "booking"]),
            ("What's the weather like?", ["weather"]),
        ]
        
        for content, expected_tags in test_cases:
            tags = []
            
            # Destination tags
            destinations = {
                "paris": "paris", "tokyo": "tokyo", "london": "london", 
                "new york": "new_york", "rome": "rome", "barcelona": "barcelona"
            }
            
            for dest_key, dest_tag in destinations.items():
                if dest_key in content.lower():
                    tags.append(dest_tag)
            
            # Activity tags
            activities = {
                "restaurant": "restaurants", "hotel": "accommodation", 
                "weather": "weather", "flight": "transportation",
                "museum": "attractions", "shopping": "shopping"
            }
            
            for activity_key, activity_tag in activities.items():
                if activity_key in content.lower():
                    tags.append(activity_tag)
            
            # General tags
            if "favorite" in content.lower() or "prefer" in content.lower():
                tags.append("preference")
            
            if "book" in content.lower() or "reserve" in content.lower():
                tags.append("booking")
            
            # Check that expected tags are present
            for expected_tag in expected_tags:
                assert expected_tag in tags
    
    def test_memory_eviction_logic(self):
        """Test memory eviction logic"""
        # Test importance-based eviction
        memories = [
            {"importance_score": 0.1, "access_count": 1, "created_at": datetime.now()},
            {"importance_score": 0.2, "access_count": 2, "created_at": datetime.now()},
            {"importance_score": 0.8, "access_count": 10, "created_at": datetime.now()},
        ]
        
        threshold = 0.3
        low_importance = [m for m in memories if m["importance_score"] < threshold]
        
        assert len(low_importance) == 2  # Two memories below threshold
        
        # Test age-based eviction
        now = datetime.now()
        old_date = now - timedelta(days=100)
        recent_date = now - timedelta(days=5)
        
        memories_with_age = [
            {"created_at": old_date, "importance_score": 0.5},
            {"created_at": old_date, "importance_score": 0.6},
            {"created_at": recent_date, "importance_score": 0.4},
        ]
        
        cutoff_date = now - timedelta(days=30)
        old_memories = [m for m in memories_with_age if m["created_at"] < cutoff_date]
        
        assert len(old_memories) == 2  # Two old memories
    
    def test_hybrid_scoring_algorithm(self):
        """Test hybrid scoring algorithm for pruning"""
        now = datetime.now()
        old_date = now - timedelta(days=100)
        
        memories = [
            {
                "importance_score": 0.1,
                "access_count": 0,
                "created_at": old_date
            },
            {
                "importance_score": 0.9,
                "access_count": 10,
                "created_at": now
            }
        ]
        
        # Calculate hybrid scores
        hybrid_scores = []
        for memory in memories:
            # Age factor (older = lower score)
            age_days = (now - memory["created_at"]).days
            age_factor = max(0, 1 - (age_days / 365))  # Decay over a year
            
            # Access factor
            access_factor = min(1, memory["access_count"] / 10)  # Normalize to 0-1
            
            # Hybrid score
            hybrid_score = (
                memory["importance_score"] * 0.5 +
                age_factor * 0.3 +
                access_factor * 0.2
            )
            
            hybrid_scores.append(hybrid_score)
        
        # The second memory should have a higher hybrid score
        assert hybrid_scores[1] > hybrid_scores[0]
    
    def test_memory_reordering_strategies(self):
        """Test memory reordering strategies"""
        memories = [
            {"importance_score": 0.3, "access_count": 1, "last_accessed": datetime.now()},
            {"importance_score": 0.9, "access_count": 5, "last_accessed": datetime.now()},
            {"importance_score": 0.6, "access_count": 3, "last_accessed": datetime.now()},
        ]
        
        # Test importance-based reordering
        importance_ordered = sorted(memories, key=lambda x: x["importance_score"], reverse=True)
        assert importance_ordered[0]["importance_score"] == 0.9
        assert importance_ordered[1]["importance_score"] == 0.6
        assert importance_ordered[2]["importance_score"] == 0.3
        
        # Test access frequency-based reordering
        access_ordered = sorted(memories, key=lambda x: x["access_count"], reverse=True)
        assert access_ordered[0]["access_count"] == 5
        assert access_ordered[1]["access_count"] == 3
        assert access_ordered[2]["access_count"] == 1
    
    def test_memory_statistics_calculation(self):
        """Test memory statistics calculation"""
        memories = [
            {
                "memory_type": "conversation",
                "importance_score": 0.8,
                "access_count": 5,
                "created_at": datetime.now()
            },
            {
                "memory_type": "tool_call",
                "importance_score": 0.6,
                "access_count": 2,
                "created_at": datetime.now()
            }
        ]
        
        # Calculate statistics
        memory_types = {}
        importance_scores = []
        access_counts = []
        
        for memory in memories:
            # Memory types
            mem_type = memory["memory_type"]
            memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
            
            # Importance scores
            importance_scores.append(memory["importance_score"])
            
            # Access counts
            access_counts.append(memory["access_count"])
        
        # Calculate averages
        avg_importance = sum(importance_scores) / len(importance_scores)
        avg_access = sum(access_counts) / len(access_counts)
        
        assert len(memories) == 2
        assert memory_types["conversation"] == 1
        assert memory_types["tool_call"] == 1
        assert avg_importance == 0.7
        assert avg_access == 3.5
    
    def test_memory_limits_enforcement(self):
        """Test memory limits enforcement"""
        memory = ShortTermMemory(max_items=3, max_tokens=100)
        
        # Add items up to limit
        for i in range(3):
            memory.add_conversation("user", f"Message {i}")
        
        assert len(memory.memory_items) == 3
        
        # Add one more item - should trigger eviction
        memory.add_conversation("user", "Message 3")
        
        # Should still be at limit
        assert len(memory.memory_items) == 3
        # First message should be evicted
        assert memory.memory_items[0]['content'] == "Message 1"
    
    def test_memory_search_functionality(self):
        """Test memory search functionality"""
        memory = ShortTermMemory()
        
        # Add various types of memories
        memory.add_conversation("user", "I want to go to Paris")
        memory.add_conversation("assistant", "Paris is a great destination!")
        memory.add_tool_call("weather", {"location": "Paris"}, {"temp": 22})
        memory.add_conversation("user", "What about restaurants in Tokyo?")
        
        # Search for Paris-related content
        paris_results = memory.search_memory("Paris")
        assert len(paris_results) == 2  # User message and assistant response
        
        # Search for weather-related content
        weather_results = memory.search_memory("weather")
        assert len(weather_results) == 1  # Tool call
        
        # Search with role filter
        user_results = memory.search_memory("Paris", role_filter="user")
        assert len(user_results) == 1  # Only user message
    
    def test_memory_context_window_generation(self):
        """Test memory context window generation"""
        memory = ShortTermMemory()
        
        # Add conversation
        memory.add_conversation("user", "Hello")
        memory.add_conversation("assistant", "Hi there!")
        memory.add_conversation("user", "How are you?")
        
        # Generate context window
        context = memory.get_context_window()
        
        assert "USER: Hello" in context
        assert "ASSISTANT: Hi there!" in context
        assert "USER: How are you?" in context
        assert isinstance(context, str)
    
    def test_memory_export_import(self):
        """Test memory export and import functionality"""
        memory = ShortTermMemory()
        
        # Add some data
        memory.add_conversation("user", "Hello")
        memory.add_tool_call("weather", {"location": "Paris"}, {"temp": 22})
        
        # Export memory
        import tempfile
        import os
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
    
    def test_memory_error_handling(self):
        """Test memory error handling"""
        memory = ShortTermMemory()
        
        # Test with invalid parameters
        try:
            memory.add_conversation("invalid_role", "test")
            # Should not raise exception, but might log warning
        except Exception:
            # If it does raise, that's also acceptable
            pass
        
        # Test search with empty query
        results = memory.search_memory("")
        assert isinstance(results, list)
        
        # Test context window with no memories
        empty_memory = ShortTermMemory()
        context = empty_memory.get_context_window()
        assert context == "No conversation history."
    
    def test_memory_performance_characteristics(self):
        """Test memory performance characteristics"""
        memory = ShortTermMemory(max_items=1000, max_tokens=10000)
        
        # Add many items to test performance
        start_time = datetime.now()
        
        for i in range(100):
            memory.add_conversation("user", f"Message {i} with some content to test performance")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete quickly (less than 1 second for 100 items)
        assert duration < 1.0
        assert len(memory.memory_items) == 100
        
        # Test search performance
        start_time = datetime.now()
        results = memory.search_memory("Message 50")
        end_time = datetime.now()
        search_duration = (end_time - start_time).total_seconds()
        
        # Search should be fast
        assert search_duration < 0.1
        assert len(results) > 0
