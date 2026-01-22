#!/usr/bin/env python3
"""
Knowledge Base Ingestion Script

This script ingests credit card knowledge snippets into the Cosmos DB vector database.
Run this script before using the knowledge tool to ensure the RAG system has data to retrieve.

Usage:
    python scripts/ingest_knowledge.py
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.rag.ingest import ingest_sample_data
from app.utils.logger import setup_logger

logger = setup_logger("ingest_script")


def main():
    """Main function to run knowledge ingestion."""
    print("=" * 60)
    print("AI Travel Concierge - Knowledge Base Ingestion")
    print("=" * 60)
    print()

    print("This script will ingest credit card knowledge snippets into Cosmos DB.")
    print("The knowledge base will be used for RAG-based card recommendations.")
    print()

    # Confirm with user
    confirm = input("Do you want to proceed with ingestion? (y/n): ")
    if confirm.lower() != 'y':
        print("Ingestion cancelled.")
        return

    print()
    print("Starting ingestion...")
    print("-" * 60)

    try:
        # Run sample data ingestion
        stats = ingest_sample_data()

        print()
        print("-" * 60)
        print("Ingestion completed successfully!")
        print()
        print(f"Total snippets: {stats['total']}")
        print(f"Successfully ingested: {stats['success_count']}")
        print(f"Errors: {stats['error_count']}")
        print()

        if stats['error_count'] > 0:
            print("⚠️  Some snippets failed to ingest. Check logs for details.")
        else:
            print("✅ All snippets ingested successfully!")

        print()
        print("The knowledge base is now ready to use with the KnowledgeTools plugin.")
        print("=" * 60)

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Error during ingestion: {e}")
        print()
        print("Please check:")
        print("1. Your .env file has correct Cosmos DB credentials")
        print("2. Cosmos DB is accessible and properly configured")
        print("3. Azure OpenAI service is accessible for generating embeddings")
        print("=" * 60)
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
