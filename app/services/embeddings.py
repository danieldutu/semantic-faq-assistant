import logging
from typing import List
from openai import OpenAI
from app.core.config import settings
from app.core.decorators import retry_on_api_error

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)


@retry_on_api_error()
def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for a single text using OpenAI API.

    Automatically retries with exponential backoff on failure (configured in decorators.py).

    Args:
        text: The text to generate embedding for

    Returns:
        A list of floats representing the embedding vector

    Raises:
        Exception: If embedding generation fails after all retry attempts
    """
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=text
    )
    embedding = response.data[0].embedding
    logger.info(f"Generated embedding for text: '{text[:50]}...'")
    return embedding


@retry_on_api_error()
def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in a batch using OpenAI API.

    Automatically retries with exponential backoff on failure (configured in decorators.py).

    Args:
        texts: List of texts to generate embeddings for

    Returns:
        List of embedding vectors

    Raises:
        Exception: If embedding generation fails after all retry attempts
    """
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=texts
    )
    embeddings = [item.embedding for item in response.data]
    logger.info(f"Generated {len(embeddings)} embeddings in batch")
    return embeddings
