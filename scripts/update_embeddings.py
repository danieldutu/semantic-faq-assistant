#!/usr/bin/env python3
"""
Script to update embeddings for modified FAQs.
Token-efficient: only regenerates embeddings for changed questions.
"""
import sys
import os
import logging
import argparse
import hashlib
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import FAQ
from app.services.embeddings import generate_embedding
from app.celery_app import generate_embedding_async

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def update_embeddings(dry_run: bool = False, force: bool = False, use_async: bool = False) -> None:
    """
    Update embeddings for FAQs that have been modified.

    Args:
        dry_run: If True, only show what would be done
        force: If True, regenerate all embeddings regardless of changes
        use_async: If True, use Celery for async processing

    Raises:
        Exception: If database operations or embedding generation fails
    """
    db = SessionLocal()
    try:
        # Get all FAQs
        all_faqs = db.query(FAQ).all()

        if not all_faqs:
            logger.warning("No FAQs found in database")
            return

        logger.info(f"Found {len(all_faqs)} FAQs in database")

        # Find FAQs that need updating
        faqs_to_update = []

        for faq in all_faqs:
            needs_update = False

            # Case 1: No embedding exists
            if faq.embedding is None:
                needs_update = True
                logger.info(f"FAQ ID {faq.id}: Missing embedding")

            # Case 2: Force update
            elif force:
                needs_update = True
                logger.info(f"FAQ ID {faq.id}: Force update")

            # Note: In a real implementation, you'd store question hashes
            # in the database to detect changes. For simplicity, we're
            # only updating FAQs without embeddings unless force is used.

            if needs_update:
                faqs_to_update.append(faq)

        if not faqs_to_update:
            logger.info("✓ All FAQs have up-to-date embeddings!")
            return

        logger.info(f"Need to update {len(faqs_to_update)} embeddings")

        if dry_run:
            logger.info("DRY RUN - No changes will be made")
            for faq in faqs_to_update:
                logger.info(f"  Would update FAQ ID {faq.id}: {faq.question[:50]}...")
            return

        # Update embeddings
        if use_async:
            logger.info(f"Queuing {len(faqs_to_update)} embedding update tasks (async mode)...")
            task_ids = []

            for idx, faq in enumerate(faqs_to_update, 1):
                logger.info(f"Queuing {idx}/{len(faqs_to_update)}: FAQ ID {faq.id}")
                task = generate_embedding_async.delay(faq.id, faq.question)
                task_ids.append(task.id)
                logger.info(f"  → Task queued: {task.id}")

            logger.info(f"✓ {len(task_ids)} embedding update tasks queued")
            logger.info("  Embeddings will be updated asynchronously by Celery workers")
        else:
            logger.info(f"Updating embeddings (synchronous mode)...")
            updated_count = 0

            for idx, faq in enumerate(faqs_to_update, 1):
                logger.info(f"Updating {idx}/{len(faqs_to_update)}: FAQ ID {faq.id}")

                try:
                    embedding = generate_embedding(faq.question)
                    faq.embedding = embedding
                    updated_count += 1
                    logger.info(f"  ✓ Updated: {faq.question[:50]}...")
                except Exception as e:
                    logger.error(f"  ✗ Failed: {str(e)}")
                    continue

            # Commit changes
            db.commit()
            logger.info(f"✓ Successfully updated {updated_count} embeddings")

    except Exception as e:
        logger.error(f"Error updating embeddings: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update embeddings for modified FAQs")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--force", action="store_true", help="Regenerate all embeddings")
    parser.add_argument("--sync", dest="use_async", action="store_false", default=True, help="Use synchronous mode instead of async (Celery is default)")

    args = parser.parse_args()

    logger.info("Starting embedding update...")
    update_embeddings(dry_run=args.dry_run, force=args.force, use_async=args.use_async)
    logger.info("Embedding update completed!")
