# lesson-9-maintaining-long-term-agent-memory-in-python/exercises/solution/long_term_memory/ai.py

import os
import logging
from typing import Optional

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureTextEmbedding
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Internal cached kernel and services
_kernel: Optional[Kernel] = None
_chat_service: Optional[AzureChatCompletion] = None
_embedding_service: Optional[AzureTextEmbedding] = None


def get_openai_kernel(enable_ai_scoring: bool = True) -> Optional[Kernel]:
    """
    Get or create a Semantic Kernel with Azure OpenAI chat + embedding services.
    Returns None if required environment variables are missing or AI scoring is disabled.
    """
    global _kernel, _chat_service, _embedding_service

    if _kernel is None and enable_ai_scoring:
        try:
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION")
            key = os.getenv("AZURE_OPENAI_KEY")
            chat_deploy = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
            embed_deploy = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT")

            if not all([endpoint, api_version, key, chat_deploy, embed_deploy]):
                logger.warning("⚠️ Missing Azure OpenAI env vars, disabling AI scoring")
                return None

            _kernel = Kernel()

            _chat_service = AzureChatCompletion(
                deployment_name=chat_deploy,
                endpoint=endpoint,
                api_key=key,
                api_version=api_version,
            )
            _embedding_service = AzureTextEmbedding(
                deployment_name=embed_deploy,
                endpoint=endpoint,
                api_key=key,
                api_version=api_version,
            )

            _kernel.add_service(_chat_service)
            _kernel.add_service(_embedding_service)

            logger.info("✅ OpenAI kernel initialized with chat + embedding services")

        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI kernel: {e}")
            return None

    return _kernel


def get_chat_service() -> Optional[AzureChatCompletion]:
    """Return the AzureChatCompletion service if initialized."""
    return _chat_service


def get_embedding_service() -> Optional[AzureTextEmbedding]:
    """Return the AzureTextEmbedding service if initialized."""
    return _embedding_service
