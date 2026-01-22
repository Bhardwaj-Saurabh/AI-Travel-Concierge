# app/tools/knowledge.py
from semantic_kernel.functions import kernel_function
from app.rag.retriever import retrieve

class KnowledgeTools:
    @kernel_function(name="get_card_recommendation", description="Get card recommendation from knowledge base using RAG vector search")
    def get_card_recommendation(self, mcc: str, country: str):
        """
        Get card recommendation from knowledge base using vector search.

        Args:
            mcc: Merchant Category Code (e.g., "5812" for restaurants)
            country: Country code (e.g., "US", "FR")

        Returns:
            Dictionary containing card recommendation from knowledge base with benefit and source
        """
        try:
            # Construct search query based on MCC and country
            query = f"Credit card benefits for MCC {mcc} in {country} with best rewards and no foreign transaction fees"

            # Use retrieve() function to search knowledge base (top 3 results)
            results = retrieve(query, k=3)

            # Check if we got valid results
            if not results or "error" in results[0]:
                return {
                    "card": "No recommendation available",
                    "benefit": "Knowledge base search returned no results",
                    "source": "RAG knowledge base",
                    "query": query
                }

            # Parse and format retrieved knowledge
            # Take the most relevant result
            top_result = results[0]

            # Extract recommendation from content
            content = top_result.get("content", "")
            metadata = top_result.get("metadata", {})

            # Simple parsing - in production, this would use more sophisticated NLP
            # For now, return the raw content as the benefit
            return {
                "card": "Knowledge Base Recommendation",
                "benefit": content,
                "source": metadata.get("source", "RAG knowledge base"),
                "relevance_score": metadata.get("relevance_score", 0.0),
                "query": query,
                "num_results": len(results)
            }

        except Exception as e:
            return {"error": f"Error retrieving knowledge: {str(e)}"}