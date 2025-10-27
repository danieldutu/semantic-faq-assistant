import logging
from celery import Celery
from app.core.config import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "faq_assistant",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
)


@celery_app.task(name="generate_embedding_async")
def generate_embedding_async(question_id: int, question_text: str):
    """
    Async task to generate embedding for a FAQ question.

    Args:
        question_id: The FAQ ID
        question_text: The question text

    Returns:
        Dictionary with status and embedding
    """
    from app.services.embeddings import generate_embedding
    from app.db.database import SessionLocal
    from app.db.models import FAQ

    try:
        logger.info(f"Generating embedding for FAQ ID: {question_id}")

        # Generate embedding
        embedding = generate_embedding(question_text)

        # Update database
        db = SessionLocal()
        try:
            faq = db.query(FAQ).filter(FAQ.id == question_id).first()
            if faq:
                faq.embedding = embedding
                db.commit()
                logger.info(f"Successfully updated embedding for FAQ ID: {question_id}")
                return {"status": "success", "faq_id": question_id}
            else:
                logger.error(f"FAQ ID {question_id} not found")
                return {"status": "error", "message": "FAQ not found"}
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error generating embedding for FAQ ID {question_id}: {str(e)}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name="generate_embeddings_batch_async")
def generate_embeddings_batch_async(faq_data: list):
    """
    Async task to generate embeddings for multiple FAQ questions.

    Args:
        faq_data: List of dictionaries with 'id' and 'question' keys

    Returns:
        Dictionary with status and processed count
    """
    from app.services.embeddings import generate_embedding
    from app.db.database import SessionLocal
    from app.db.models import FAQ

    try:
        logger.info(f"Generating embeddings for {len(faq_data)} FAQs")
        processed = 0

        db = SessionLocal()
        try:
            for item in faq_data:
                faq_id = item["id"]
                question = item["question"]

                try:
                    embedding = generate_embedding(question)
                    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
                    if faq:
                        faq.embedding = embedding
                        processed += 1
                except Exception as e:
                    logger.error(f"Error processing FAQ ID {faq_id}: {str(e)}")

            db.commit()
            logger.info(f"Successfully processed {processed}/{len(faq_data)} embeddings")
            return {"status": "success", "processed": processed, "total": len(faq_data)}

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in batch embedding generation: {str(e)}")
        return {"status": "error", "message": str(e)}
