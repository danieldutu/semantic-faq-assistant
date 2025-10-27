#!/usr/bin/env python3
"""
Script to create embeddings for all FAQs that don't have embeddings yet.
"""
import sys
import os
import logging
import argparse
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import FAQ
from app.services.embeddings import generate_embedding
from app.celery_app import generate_embedding_async

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_embeddings(dry_run: bool = False, collection_name: Optional[str] = None, use_async: bool = False) -> None:
    """
    Create embeddings for FAQs that don't have embeddings.

    Args:
        dry_run: If True, only show what would be done
        collection_name: Optional collection name to filter by
        use_async: If True, use Celery for async processing

    Raises:
        Exception: If database operations or embedding generation fails
    """
    db = SessionLocal()
    try:
        # Find FAQs without embeddings
        query = db.query(FAQ).filter(FAQ.embedding.is_(None))

        if collection_name:
            query = query.filter(FAQ.collection_name == collection_name)

        faqs_without_embeddings = query.all()

        if not faqs_without_embeddings:
            logger.info("All FAQs already have embeddings!")
            return

        logger.info(f"Found {len(faqs_without_embeddings)} FAQs without embeddings")

        if dry_run:
            logger.info("DRY RUN - No changes will be made")
            for faq in faqs_without_embeddings:
                logger.info(f"  Would generate embedding for FAQ ID {faq.id}: {faq.question[:50]}...")
            return

        # Generate embeddings
        if use_async:
            logger.info(f"Queuing {len(faqs_without_embeddings)} embedding tasks (async mode)...")
            task_ids = []

            for idx, faq in enumerate(faqs_without_embeddings, 1):
                logger.info(f"Queuing {idx}/{len(faqs_without_embeddings)}: FAQ ID {faq.id}")
                task = generate_embedding_async.delay(faq.id, faq.question)
                task_ids.append(task.id)
                logger.info(f"  → Task queued: {task.id}")

            logger.info(f"✓ {len(task_ids)} embedding tasks queued")
            logger.info("  Embeddings will be generated asynchronously by Celery workers")
        else:
            logger.info(f"Generating embeddings (synchronous mode)...")

            for idx, faq in enumerate(faqs_without_embeddings, 1):
                logger.info(f"Processing {idx}/{len(faqs_without_embeddings)}: FAQ ID {faq.id}")

                try:
                    embedding = generate_embedding(faq.question)
                    faq.embedding = embedding
                    logger.info(f"  ✓ Generated embedding for: {faq.question[:50]}...")
                except Exception as e:
                    logger.error(f"  ✗ Failed to generate embedding: {str(e)}")
                    continue

            # Commit changes
            db.commit()
            logger.info(f"✓ Successfully created {len(faqs_without_embeddings)} embeddings")

    except Exception as e:
        logger.error(f"Error creating embeddings: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create embeddings for FAQs")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--collection", type=str, help="Only process FAQs from this collection")
    parser.add_argument("--sync", dest="use_async", action="store_false", default=True, help="Use synchronous mode instead of async (Celery is default)")

    args = parser.parse_args()

    logger.info("Starting embedding creation...")
    create_embeddings(dry_run=args.dry_run, collection_name=args.collection, use_async=args.use_async)
    logger.info("Embedding creation completed!")
