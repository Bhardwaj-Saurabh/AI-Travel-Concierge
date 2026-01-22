# app/rag/retriever.py
from typing import List, Dict, Any
import os
import math
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from app.utils.config import validate_all_config
from app.utils.logger import setup_logger
from app.rag.ingest import embed_texts, get_cosmos_client

logger = setup_logger("rag_retriever")


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score between -1 and 1
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def retrieve(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve relevant knowledge snippets using vector search.

    Args:
        query: Search query string
        k: Number of top results to return (default: 5)

    Returns:
        List of dictionaries containing matched snippets with content, metadata, and relevance scores
    """
    try:
        logger.info(f"Retrieving top {k} results for query: {query}")

        # Step 1: Generate embedding for the query
        logger.info("Generating query embedding...")
        query_embeddings = embed_texts([query])

        if not query_embeddings or len(query_embeddings) == 0:
            logger.error("Failed to generate query embedding")
            return [{"error": "Failed to generate query embedding"}]

        query_embedding = query_embeddings[0]

        # Step 2: Connect to Cosmos DB
        logger.info("Connecting to Cosmos DB...")
        _, _, container = get_cosmos_client()

        # Step 3: Retrieve all documents (in production, use vector search built into Cosmos DB)
        # Note: Cosmos DB for NoSQL supports vector search with VectorDistance function
        # This is a simplified version using client-side similarity calculation

        logger.info("Fetching documents from Cosmos DB...")
        query_spec = {
            "query": "SELECT * FROM c WHERE c.pk = @pk",
            "parameters": [
                {"name": "@pk", "value": "knowledge"}
            ]
        }

        items = list(container.query_items(
            query=query_spec,
            enable_cross_partition_query=False
        ))

        logger.info(f"Retrieved {len(items)} documents from database")

        # Step 4: Calculate similarity scores for each document
        results_with_scores = []

        for item in items:
            if "embedding" not in item:
                logger.warning(f"Document {item.get('id')} has no embedding, skipping")
                continue

            # Calculate cosine similarity
            similarity = cosine_similarity(query_embedding, item["embedding"])

            results_with_scores.append({
                "content": item.get("content", ""),
                "metadata": {
                    **item.get("metadata", {}),
                    "relevance_score": round(similarity, 4),
                    "doc_id": item.get("id", "unknown")
                },
                "similarity": similarity
            })

        # Step 5: Sort by similarity (highest first) and return top-k
        results_with_scores.sort(key=lambda x: x["similarity"], reverse=True)
        top_results = results_with_scores[:k]

        # Remove the similarity field from final results (it's in metadata as relevance_score)
        final_results = [
            {
                "content": r["content"],
                "metadata": r["metadata"]
            }
            for r in top_results
        ]

        logger.info(f"Returning top {len(final_results)} results")

        if not final_results:
            logger.warning("No results found for query")
            return [{
                "content": "No relevant knowledge found for this query",
                "metadata": {
                    "source": "knowledge_base",
                    "relevance_score": 0.0
                }
            }]

        return final_results

    except CosmosResourceNotFoundError as e:
        logger.error(f"Cosmos DB resource not found: {e}")
        return [{
            "error": "Knowledge base not found. Please run data ingestion first.",
            "metadata": {"source": "error"}
        }]
    except Exception as e:
        logger.error(f"Error during retrieval: {e}", exc_info=True)
        return [{
            "error": str(e),
            "metadata": {"source": "error"}
        }]


def retrieve_with_cosmos_vector_search(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve using Cosmos DB's native vector search capability (VectorDistance).

    Note: This requires Cosmos DB to be configured with vector indexing policy.
    This is a more advanced implementation that leverages server-side vector search.

    Args:
        query: Search query string
        k: Number of top results to return

    Returns:
        List of dictionaries containing matched snippets
    """
    try:
        # Generate query embedding
        query_embeddings = embed_texts([query])
        query_embedding = query_embeddings[0]

        # Connect to Cosmos DB
        _, _, container = get_cosmos_client()

        # Cosmos DB vector search query using VectorDistance
        # This is the SQL syntax for vector similarity search in Cosmos DB
        vector_query = {
            "query": """
                SELECT TOP @k c.id, c.content, c.metadata,
                VectorDistance(c.embedding, @embedding) AS SimilarityScore
                FROM c
                WHERE c.pk = @pk
                ORDER BY VectorDistance(c.embedding, @embedding)
            """,
            "parameters": [
                {"name": "@k", "value": k},
                {"name": "@pk", "value": "knowledge"},
                {"name": "@embedding", "value": query_embedding}
            ]
        }

        # Execute query
        items = list(container.query_items(
            query=vector_query,
            enable_cross_partition_query=False
        ))

        # Format results
        results = [
            {
                "content": item.get("content", ""),
                "metadata": {
                    **item.get("metadata", {}),
                    "relevance_score": round(1 - item.get("SimilarityScore", 1.0), 4),  # Convert distance to similarity
                    "doc_id": item.get("id", "unknown")
                }
            }
            for item in items
        ]

        return results if results else [{"error": "No results found"}]

    except Exception as e:
        logger.error(f"Error in vector search: {e}")
        # Fallback to client-side similarity calculation
        return retrieve(query, k)