# app/tools/search.py
from semantic_kernel.functions import kernel_function
import requests
import os

class SearchTools:
    @kernel_function(name="web_search", description="Search the web using Bing Search API v7 for restaurants and attractions")
    def web_search(self, query: str, max_results: int = 5):
        """
        Search the web using Bing Search API.

        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 5)

        Returns:
            List of dictionaries containing search results with title, URL, and snippet
        """
        try:
            # Get API key from environment variables
            api_key = os.environ.get("BING_KEY")
            if not api_key:
                return [{"error": "BING_KEY not set in environment variables"}]

            # Construct API URL with query parameters
            base_url = "https://api.bing.microsoft.com/v7.0/search"
            params = {
                "q": query,
                "count": max_results,
                "textDecorations": True,
                "textFormat": "HTML"
            }

            # Set proper headers with API key
            headers = {
                "Ocp-Apim-Subscription-Key": api_key
            }

            # Make API request
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse response and format results
            data = response.json()
            results = []

            if "webPages" in data and "value" in data["webPages"]:
                for item in data["webPages"]["value"][:max_results]:
                    results.append({
                        "title": item.get("name", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("snippet", "")
                    })

            return results if results else [{"info": "No search results found"}]

        except requests.exceptions.Timeout:
            return [{"error": "Bing Search API request timed out"}]
        except requests.exceptions.RequestException as e:
            return [{"error": f"Bing Search API request failed: {str(e)}"}]
        except Exception as e:
            return [{"error": f"Unexpected error during web search: {str(e)}"}]