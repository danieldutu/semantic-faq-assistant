import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text

from app.api import endpoints
from app.db.database import init_db, SessionLocal
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting FAQ Assistant API")
    logger.info(f"Using embedding model: {settings.embedding_model}")
    logger.info(f"Embedding dimension: {settings.embedding_dimension}")
    logger.info(f"Using chat model: {settings.chat_model}")
    logger.info(f"Similarity threshold: {settings.similarity_threshold}")

    # Initialize database (ensure tables exist)
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")

    # Validate embedding dimension matches database schema
    db = SessionLocal()
    try:
        # Query the database schema to get the vector dimension
        result = db.execute(text("""
            SELECT atttypmod
            FROM pg_attribute
            WHERE attrelid = 'faqs'::regclass
            AND attname = 'embedding'
        """))
        row = result.fetchone()

        if row and row[0] > 0:
            # atttypmod for vector columns is the dimension itself in pgvector
            db_dimension = row[0]
            config_dimension = settings.embedding_dimension

            if db_dimension != config_dimension:
                error_msg = (
                    f"CRITICAL: Embedding dimension mismatch detected!\n"
                    f"  - Database schema expects: {db_dimension} dimensions\n"
                    f"  - Config model '{settings.embedding_model}' produces: {config_dimension} dimensions\n"
                    f"  - This will cause embedding insertion failures.\n"
                    f"  - To fix: Run database migration or change EMBEDDING_MODEL in .env"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            else:
                logger.info(f"✓ Embedding dimension validation passed: {config_dimension}D")
    except ValueError:
        # Re-raise dimension mismatch errors
        raise
    except Exception as e:
        # Log but don't fail on validation errors (e.g., table doesn't exist yet)
        logger.warning(f"Could not validate embedding dimension: {str(e)}")
    finally:
        db.close()

    yield

    # Shutdown
    logger.info("Shutting down FAQ Assistant API")


# Create FastAPI application
app = FastAPI(
    title="FAQ Assistant API",
    description=(
        "Semantic FAQ Assistant that answers questions using similarity search "
        "and OpenAI fallback. Features AI routing for IT-related questions."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(endpoints.router, tags=["FAQ"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to FAQ Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
