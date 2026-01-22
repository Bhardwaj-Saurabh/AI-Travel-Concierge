# app/rag/ingest.py
from typing import List, Dict, Any
import os
import uuid
import asyncio
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from semantic_kernel.connectors.ai.open_ai import AzureTextEmbedding
from app.utils.config import validate_all_config
from app.utils.logger import setup_logger

logger = setup_logger("rag_ingest")


def create_embedding_service() -> AzureTextEmbedding:
    """Create Azure Text Embedding service for generating embeddings."""
    config = validate_all_config()
    azure_config = config["azure"]

    embedding_service = AzureTextEmbedding(
        deployment_name=azure_config["AZURE_OPENAI_EMBED_DEPLOYMENT"],
        endpoint=azure_config["AZURE_OPENAI_ENDPOINT"],
        api_key=azure_config["AZURE_OPENAI_KEY"],
        api_version=azure_config["AZURE_OPENAI_API_VERSION"]
    )

    return embedding_service


async def embed_texts_async(texts: List[str], embedding_service: AzureTextEmbedding) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using Azure OpenAI.

    Args:
        texts: List of text strings to embed
        embedding_service: Azure Text Embedding service instance

    Returns:
        List of embedding vectors (each vector is a list of floats)
    """
    embeddings = []

    for text in texts:
        try:
            # Generate embedding for single text
            result = await embedding_service.generate_embeddings([text])
            if result and len(result) > 0:
                embeddings.append(result[0])
            else:
                logger.warning(f"No embedding generated for text: {text[:50]}...")
                embeddings.append([0.0] * 1536)  # Fallback to zero vector (dimension 1536 for text-embedding-3-small)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            embeddings.append([0.0] * 1536)

    return embeddings


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Synchronous wrapper for embed_texts_async.

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding vectors
    """
    embedding_service = create_embedding_service()
    return asyncio.run(embed_texts_async(texts, embedding_service))


def get_cosmos_client() -> tuple:
    """
    Get Cosmos DB client and container.

    Returns:
        Tuple of (client, database, container)
    """
    config = validate_all_config()
    cosmos_config = config["cosmos"]

    # Get Cosmos DB credentials
    endpoint = cosmos_config["COSMOS_ENDPOINT"]
    key = os.environ.get("COSMOS_KEY")
    database_name = cosmos_config["COSMOS_DB"]
    container_name = cosmos_config["COSMOS_CONTAINER"]

    # Create client
    client = CosmosClient(endpoint, credential=key)

    # Get or create database
    database = client.create_database_if_not_exists(id=database_name)

    # Get or create container with vector indexing policy
    # Note: Vector indexing requires specific configuration in Cosmos DB
    try:
        container = database.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path="/pk"),
            offer_throughput=400
        )
    except Exception as e:
        logger.warning(f"Could not create container with vector policy: {e}")
        # Try to get existing container
        container = database.get_container_client(container_name)

    return client, database, container


def upsert_snippet(snippet: Dict[str, Any], embedding: List[float]) -> bool:
    """
    Store a single snippet with its embedding in Cosmos DB.

    Args:
        snippet: Dictionary containing snippet data (must have 'id', 'content', and optionally 'metadata')
        embedding: Embedding vector for the snippet content

    Returns:
        True if successful, False otherwise
    """
    try:
        _, _, container = get_cosmos_client()

        # Prepare document for Cosmos DB
        document = {
            "id": snippet.get("id", str(uuid.uuid4())),
            "pk": snippet.get("pk", "knowledge"),  # Partition key
            "content": snippet.get("content", ""),
            "metadata": snippet.get("metadata", {}),
            "embedding": embedding
        }

        # Upsert document
        container.upsert_item(document)
        logger.info(f"Upserted snippet: {document['id']}")
        return True

    except Exception as e:
        logger.error(f"Error upserting snippet: {e}")
        return False


def ingest_snippets(snippets: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Ingest multiple knowledge snippets into the vector database.

    Args:
        snippets: List of snippet dictionaries, each containing:
            - id (optional): Unique identifier
            - content: Text content to embed and store
            - metadata (optional): Additional metadata
            - pk (optional): Partition key (defaults to 'knowledge')

    Returns:
        Dictionary with ingestion statistics (success_count, error_count)
    """
    logger.info(f"Starting ingestion of {len(snippets)} snippets...")

    stats = {
        "success_count": 0,
        "error_count": 0,
        "total": len(snippets)
    }

    try:
        # Extract text content from snippets
        texts = [snippet.get("content", "") for snippet in snippets]

        # Generate embeddings for all texts
        logger.info("Generating embeddings...")
        embeddings = embed_texts(texts)

        # Upsert each snippet with its embedding
        logger.info("Upserting snippets to Cosmos DB...")
        for i, (snippet, embedding) in enumerate(zip(snippets, embeddings)):
            # Ensure snippet has an ID
            if "id" not in snippet:
                snippet["id"] = str(uuid.uuid4())

            # Ensure snippet has partition key
            if "pk" not in snippet:
                snippet["pk"] = "knowledge"

            # Upsert snippet
            if upsert_snippet(snippet, embedding):
                stats["success_count"] += 1
            else:
                stats["error_count"] += 1

            # Log progress every 10 snippets
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i + 1}/{len(snippets)} snippets processed")

        logger.info(f"Ingestion completed: {stats['success_count']} successful, {stats['error_count']} errors")
        return stats

    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        stats["error_count"] = stats["total"] - stats["success_count"]
        return stats


def ingest_sample_data():
    """Ingest sample credit card knowledge snippets for testing."""
    sample_snippets = [
        {
            "id": "cc-sapphire-travel",
            "content": "Chase Sapphire Reserve offers 3x points on travel and dining worldwide, with no foreign transaction fees. Great for international travelers.",
            "metadata": {
                "source": "chase_benefits",
                "card": "Chase Sapphire Reserve",
                "category": "travel",
                "mcc": "3000-3999"
            }
        },
        {
            "id": "cc-amex-platinum-flights",
            "content": "Amex Platinum provides 5x points on flights booked directly with airlines or through Amex Travel, no FX fees on international purchases.",
            "metadata": {
                "source": "amex_benefits",
                "card": "Amex Platinum",
                "category": "airlines",
                "mcc": "3000-3999"
            }
        },
        {
            "id": "cc-venture-x-hotels",
            "content": "Capital One Venture X gives 10x miles on hotels and rental cars through Capital One Travel, 2x miles on everything else, zero foreign transaction fees.",
            "metadata": {
                "source": "capital_one_benefits",
                "card": "Capital One Venture X",
                "category": "hotels",
                "mcc": "4000-4999"
            }
        },
        {
            "id": "cc-sapphire-dining",
            "content": "For restaurant spending (MCC 5812), Chase Sapphire Reserve earns 3x points per dollar with no FX fees, ideal for dining abroad.",
            "metadata": {
                "source": "chase_benefits",
                "card": "Chase Sapphire Reserve",
                "category": "dining",
                "mcc": "5812"
            }
        },
        {
            "id": "cc-comparison-fx",
            "content": "Premium travel cards like Chase Sapphire Reserve, Amex Platinum, and Capital One Venture X all have 0% foreign transaction fees, while standard cards typically charge 3%.",
            "metadata": {
                "source": "comparison",
                "category": "foreign_fees"
            }
        }
    ]

    logger.info("Ingesting sample credit card knowledge data...")
    stats = ingest_snippets(sample_snippets)
    logger.info(f"Sample data ingestion completed: {stats}")
    return stats


if __name__ == "__main__":
    # Run sample data ingestion
    ingest_sample_data()