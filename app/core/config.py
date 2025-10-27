from pydantic_settings import BaseSettings
from typing import Optional


# Embedding model dimensions mapping
# IMPORTANT: Changing embedding models requires database migration
EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,  # Legacy model
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI Configuration
    openai_api_key: str
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"

    # Database Configuration
    database_url: str

    # Application Configuration
    similarity_threshold: float = 0.85
    api_secret_key: str

    # Rate Limiting
    max_requests_per_minute: int = 50

    # Celery Configuration (Optional)
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def embedding_dimension(self) -> int:
        """
        Get the vector dimension for the configured embedding model.

        Returns:
            int: The dimension size for the embedding model

        Raises:
            ValueError: If the embedding model is not supported
        """
        if self.embedding_model not in EMBEDDING_DIMENSIONS:
            supported_models = list(EMBEDDING_DIMENSIONS.keys())
            raise ValueError(
                f"Unsupported embedding model: '{self.embedding_model}'. "
                f"Supported models: {supported_models}. "
                f"Note: Changing models requires database migration."
            )
        return EMBEDDING_DIMENSIONS[self.embedding_model]


# Global settings instance
settings = Settings()
