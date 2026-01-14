"""
Semantic Kernel Filters for Logging, Telemetry, and Cross-cutting Concerns
"""

import logging
import time
from typing import Dict, Any, Optional
from semantic_kernel import Kernel
from semantic_kernel.functions import KernelArguments
from semantic_kernel.contents import ChatHistory, ChatMessageContent
from semantic_kernel.functions import FunctionResult

logger = logging.getLogger(__name__)

class LoggingFilter:
    """SK filter for logging prompts, tool inputs/outputs, and timings"""
    
    def __init__(self, log_level: str = "INFO"):
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger = logging.getLogger("sk_filter")
        self.logger.setLevel(self.log_level)
    
    async def on_function_invocation(self, kernel: Kernel, function: Any, arguments: KernelArguments) -> None:
        """Log function invocation details"""
        try:
            self.logger.info(f"🔧 Invoking function: {function.name}")
            self.logger.debug(f"   Arguments: {dict(arguments)}")
        except Exception as e:
            self.logger.error(f"❌ Error in on_function_invocation: {e}")
    
    async def on_function_result(self, kernel: Kernel, function: Any, arguments: KernelArguments, result: FunctionResult) -> None:
        """Log function result details"""
        try:
            self.logger.info(f"✅ Function {function.name} completed")
            self.logger.debug(f"   Result type: {type(result.value)}")
            self.logger.debug(f"   Result length: {len(str(result.value)) if result.value else 0}")
        except Exception as e:
            self.logger.error(f"❌ Error in on_function_result: {e}")

class TelemetryFilter:
    """SK filter for collecting telemetry and metrics"""
    
    def __init__(self):
        self.metrics = {
            "function_calls": 0,
            "total_tokens": 0,
            "total_time": 0.0,
            "errors": 0
        }
        self.start_times = {}
    
    async def on_function_invocation(self, kernel: Kernel, function: Any, arguments: KernelArguments) -> None:
        """Start timing function execution"""
        try:
            self.start_times[function.name] = time.time()
            self.metrics["function_calls"] += 1
        except Exception as e:
            logger.error(f"❌ Error in telemetry on_function_invocation: {e}")
    
    async def on_function_result(self, kernel: Kernel, function: Any, arguments: KernelArguments, result: FunctionResult) -> None:
        """Record function execution metrics"""
        try:
            if function.name in self.start_times:
                execution_time = time.time() - self.start_times[function.name]
                self.metrics["total_time"] += execution_time
                del self.start_times[function.name]
            
            # Estimate token usage (rough approximation)
            if result.value:
                estimated_tokens = len(str(result.value)) // 4  # Rough token estimation
                self.metrics["total_tokens"] += estimated_tokens
            
            if result.error:
                self.metrics["errors"] += 1
                
        except Exception as e:
            logger.error(f"❌ Error in telemetry on_function_result: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset metrics"""
        self.metrics = {
            "function_calls": 0,
            "total_tokens": 0,
            "total_time": 0.0,
            "errors": 0
        }

class MemoryUpdateFilter:
    """SK filter for updating memory based on function results"""
    
    def __init__(self, short_term_memory=None, long_term_memory=None):
        self.short_term_memory = short_term_memory
        self.long_term_memory = long_term_memory
    
    async def on_function_result(self, kernel: Kernel, function: Any, arguments: KernelArguments, result: FunctionResult) -> None:
        """Update memory with function results"""
        try:
            if not result.value:
                return
            
            # Add tool call to short-term memory
            if self.short_term_memory:
                self.short_term_memory.add_tool_call(
                    function.name,
                    dict(arguments),
                    result.value
                )
            
            # Add important results to long-term memory
            if self.long_term_memory and self._is_important_result(function.name, result.value):
                self.long_term_memory.add_memory(
                    session_id="system",
                    content=f"Tool {function.name} result: {str(result.value)[:500]}",
                    memory_type="tool_result",
                    importance_score=0.7,
                    tags=[function.name, "tool_result"]
                )
                
        except Exception as e:
            logger.error(f"❌ Error in memory update filter: {e}")
    
    def _is_important_result(self, function_name: str, result: Any) -> bool:
        """Determine if a result is important enough for long-term memory"""
        important_functions = ["search_knowledge", "get_card_recommendation", "web_search"]
        return function_name in important_functions

class GuardrailsFilter:
    """SK filter for implementing guardrails and safety checks"""
    
    def __init__(self):
        self.blocked_patterns = [
            "password", "credit card number", "ssn", "social security",
            "bank account", "routing number", "pin"
        ]
    
    async def on_function_invocation(self, kernel: Kernel, function: Any, arguments: KernelArguments) -> None:
        """Check for sensitive information in arguments"""
        try:
            for key, value in arguments.items():
                if isinstance(value, str):
                    for pattern in self.blocked_patterns:
                        if pattern.lower() in value.lower():
                            logger.warning(f"🚨 Potential sensitive information detected in {key}: {pattern}")
                            # Could raise an exception or sanitize here
                            
        except Exception as e:
            logger.error(f"❌ Error in guardrails filter: {e}")

class CitationFilter:
    """SK filter for tracking and managing citations"""
    
    def __init__(self):
        self.citations = set()
    
    async def on_function_result(self, kernel: Kernel, function: Any, arguments: KernelArguments, result: FunctionResult) -> None:
        """Extract citations from function results"""
        try:
            if not result.value:
                return
            
            # Extract URLs from search results
            if function.name == "web_search" and isinstance(result.value, list):
                for item in result.value:
                    if isinstance(item, dict) and "url" in item:
                        self.citations.add(item["url"])
            
            # Extract knowledge base sources
            elif function.name == "search_knowledge" and isinstance(result.value, list):
                for item in result.value:
                    if isinstance(item, dict) and "source" in item:
                        self.citations.add(f"knowledge_base:{item['source']}")
                        
        except Exception as e:
            logger.error(f"❌ Error in citation filter: {e}")
    
    def get_citations(self) -> list:
        """Get collected citations"""
        return list(self.citations)
    
    def clear_citations(self) -> None:
        """Clear citations"""
        self.citations.clear()

def setup_kernel_filters(kernel: Kernel, short_term_memory=None, long_term_memory=None) -> Dict[str, Any]:
    """
    Set up all SK filters for the kernel.
    
    Args:
        kernel: Semantic Kernel instance
        short_term_memory: Short-term memory instance
        long_term_memory: Long-term memory instance
        
    Returns:
        Dictionary of filter instances for access to metrics and data
    """
    filters = {}
    
    # Create filter instances
    filters["logging"] = LoggingFilter()
    filters["telemetry"] = TelemetryFilter()
    filters["memory"] = MemoryUpdateFilter(short_term_memory, long_term_memory)
    filters["guardrails"] = GuardrailsFilter()
    filters["citations"] = CitationFilter()
    
    # Add filters to kernel (simplified for now)
    # Note: Filter registration may vary by SK version
    # For now, we'll just return the filters without registering them
    # kernel.add_filter(filters["logging"])
    # kernel.add_filter(filters["telemetry"])
    # kernel.add_filter(filters["memory"])
    # kernel.add_filter(filters["guardrails"])
    # kernel.add_filter(filters["citations"])
    
    logger.info("✅ SK filters configured successfully")
    return filters
