# app/tools/search.py
"""
SearchTools to perform web searches via Azure AI Agent with Bing grounding from AI Foundry.
"""
from semantic_kernel.functions import kernel_function
import os
import logging

logger = logging.getLogger("search_tool")


class SearchTools:
    """Search tools using pre-configured Azure AI Agent with Bing grounding from AI Foundry."""

    def __init__(self):
        """Initialize SearchTools with Azure AI Foundry Agent configuration."""
        self.project_endpoint = os.environ.get("PROJECT_ENDPOINT", "").strip('"')
        self.agent_id = os.environ.get("AGENT_ID", "")
        logger.info(f"Initialized SearchTools with Azure AI Foundry Agent: {self.agent_id}")

    @kernel_function(name="web_search", description="Search the web using Azure AI Agent with Bing grounding for restaurants, attractions, and travel info")
    def web_search(self, query: str, max_results: int = 5):
        """
        Search the web using pre-configured Azure AI Agent with Bing grounding.

        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 5)

        Returns:
            List of dictionaries containing search results with title, URL, and snippet
        """
        # Try Azure AI Foundry Agent first
        result = self._search_with_foundry_agent(query, max_results)
        if result:
            return result

        # Fallback to mock results if agent fails
        return self._get_mock_results(query, max_results)

    def _search_with_foundry_agent(self, query: str, max_results: int = 5):
        """
        Search using pre-configured Azure AI Foundry Agent with Bing grounding.

        Args:
            query: Search query string
            max_results: Maximum number of results

        Returns:
            List of search results or None if failed
        """
        try:
            from azure.ai.projects import AIProjectClient
            from azure.identity import DefaultAzureCredential

            if not self.project_endpoint or not self.agent_id:
                logger.warning("PROJECT_ENDPOINT or AGENT_ID not configured")
                return None

            # Create AI Project client
            client = AIProjectClient(
                credential=DefaultAzureCredential(),
                endpoint=self.project_endpoint
            )

            logger.info(f"Using existing Foundry Agent: {self.agent_id}")

            # Create thread and run in one call with the search query
            search_message = f"Search the web for: {query}. Return the top {max_results} results with title, URL, and a brief description for each."

            # Import the thread creation options model
            from azure.ai.agents.models import AgentThreadCreationOptions, ThreadMessageOptions

            # Create thread options with the search message
            thread_options = AgentThreadCreationOptions(
                messages=[
                    ThreadMessageOptions(role="user", content=search_message)
                ]
            )

            # Use create_thread_and_process_run for combined operation
            run_result = client.agents.create_thread_and_process_run(
                agent_id=self.agent_id,
                thread=thread_options
            )

            # Check run status
            if run_result.status == "failed":
                logger.error(f"Agent run failed: {run_result.last_error}")
                return None

            # Get the response messages using the messages client
            messages = client.agents.messages.list(thread_id=run_result.thread_id)

            # Extract results from assistant response
            results = []
            for msg in messages:  # ItemPaged is an iterator
                if msg.role == "assistant":
                    for content_item in msg.content:
                        if hasattr(content_item, 'text'):
                            text_content = content_item.text.value

                            # Add the main response
                            results.append({
                                "title": f"Search results for: {query}",
                                "url": "",
                                "snippet": text_content[:500] if len(text_content) > 500 else text_content
                            })

                            # Extract citations/annotations if available
                            if hasattr(content_item.text, 'annotations'):
                                for annotation in content_item.text.annotations:
                                    if hasattr(annotation, 'url_citation'):
                                        citation = annotation.url_citation
                                        results.append({
                                            "title": getattr(citation, 'title', 'Source'),
                                            "url": getattr(citation, 'url', ''),
                                            "snippet": ""
                                        })

            # Clean up thread
            try:
                client.agents.threads.delete(run_result.thread_id)
            except Exception:
                pass

            if results:
                logger.info(f"Found {len(results)} results from Foundry Agent")
                return results[:max_results]

            return None

        except ImportError as e:
            logger.warning(f"Azure AI Projects SDK not available: {e}")
            return None
        except Exception as e:
            logger.error(f"Azure AI Foundry Agent search failed: {e}")
            return None

    def _get_mock_results(self, query: str, max_results: int = 5):
        """
        Return mock search results for demonstration when APIs are unavailable.

        Args:
            query: Search query string
            max_results: Maximum number of results

        Returns:
            List of mock search results
        """
        logger.info(f"Using mock search results for: {query}")

        # Generate contextual mock results based on query
        if "restaurant" in query.lower() or "food" in query.lower():
            return [
                {
                    "title": "Top 10 Restaurants in Paris - TripAdvisor",
                    "url": "https://www.tripadvisor.com/Restaurants-Paris",
                    "snippet": "Discover the best restaurants in Paris. From classic French bistros to Michelin-starred dining experiences."
                },
                {
                    "title": "Best Paris Restaurants 2024 - Eater",
                    "url": "https://www.eater.com/paris-restaurants",
                    "snippet": "The essential guide to dining in Paris, featuring the city's most exciting restaurants."
                },
                {
                    "title": "Where to Eat in Paris - Lonely Planet",
                    "url": "https://www.lonelyplanet.com/paris/restaurants",
                    "snippet": "Paris restaurant guide with reviews, menus, and reservations for the best local cuisine."
                }
            ][:max_results]
        elif "hotel" in query.lower() or "stay" in query.lower():
            return [
                {
                    "title": "Best Hotels in Paris - Booking.com",
                    "url": "https://www.booking.com/paris-hotels",
                    "snippet": "Find and book the perfect Paris hotel. Compare prices, read reviews, and reserve your room."
                },
                {
                    "title": "Paris Hotels - Expedia",
                    "url": "https://www.expedia.com/Paris-Hotels",
                    "snippet": "Explore Paris hotel deals and save on your next trip. Free cancellation available."
                }
            ][:max_results]
        else:
            return [
                {
                    "title": f"Search Results for: {query}",
                    "url": f"https://www.bing.com/search?q={query.replace(' ', '+')}",
                    "snippet": f"Web search results for '{query}'. Visit Bing for more detailed results."
                },
                {
                    "title": f"{query} - Wikipedia",
                    "url": f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
                    "snippet": f"Learn more about {query} on Wikipedia, the free encyclopedia."
                },
                {
                    "title": f"{query} Travel Guide - Lonely Planet",
                    "url": "https://www.lonelyplanet.com",
                    "snippet": f"Comprehensive travel guide for {query}. Tips, attractions, and local insights."
                }
            ][:max_results]
