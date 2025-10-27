#!/usr/bin/env python3
"""
Script to seed the FAQ database with initial questions and generate embeddings.
"""
import sys
import os
import logging
import json
import argparse
from typing import List, Dict, Any, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import FAQ
from app.services.embeddings import generate_embedding
from app.celery_app import generate_embedding_async
from app.core.constants import DEFAULT_COLLECTION_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_faqs_from_json(json_path: str) -> List[Dict[str, str]]:
    """Load FAQ data from JSON file.

    Args:
        json_path: Path to the JSON file containing FAQ data

    Returns:
        List of dictionaries with 'question' and 'answer' keys

    Raises:
        FileNotFoundError: If the JSON file doesn't exist
        json.JSONDecodeError: If the JSON file is invalid
    """
    try:
        with open(json_path, 'r') as f:
            faqs = json.load(f)
        logger.info(f"Loaded {len(faqs)} FAQs from {json_path}")
        return faqs
    except FileNotFoundError:
        logger.error(f"FAQ file not found: {json_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in FAQ file: {str(e)}")
        raise


def seed_faqs(json_path: Optional[str] = None, force: bool = False, use_async: bool = False) -> None:
    """Seed the database with FAQs and generate embeddings.

    Args:
        json_path: Path to JSON file with FAQ data (defaults to data/faqs.json)
        force: If True, delete existing FAQs without prompting
        use_async: If True, use Celery for async embedding generation (default: False)

    Raises:
        Exception: If database operations fail
    """
    # Default JSON path
    if json_path is None:
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(script_dir, 'data', 'faqs.json')

    # Load FAQ data from JSON
    faq_database = load_faqs_from_json(json_path)

    db = SessionLocal()
    try:
        # Check if FAQs already exist
        existing_count = db.query(FAQ).count()
        if existing_count > 0:
            logger.warning(f"Database already contains {existing_count} FAQs")

            if not force:
                response = input("Do you want to delete existing FAQs and reseed? (yes/no): ")
                if response.lower() != 'yes':
                    logger.info("Seeding cancelled")
                    return
            else:
                logger.info("Force mode enabled, deleting existing FAQs")

            # Delete existing FAQs
            db.query(FAQ).delete()
            db.commit()
            logger.info("Deleted existing FAQs")

        # Insert FAQs with embeddings
        if use_async:
            logger.info(f"Seeding {len(faq_database)} FAQs (async mode with Celery)...")
            task_ids = []

            for idx, faq_data in enumerate(faq_database, 1):
                logger.info(f"Queuing FAQ {idx}/{len(faq_database)}: {faq_data['question'][:50]}...")

                # Create FAQ entry without embedding first
                faq = FAQ(
                    question=faq_data['question'],
                    answer=faq_data['answer'],
                    embedding=None,
                    collection_name=DEFAULT_COLLECTION_NAME
                )
                db.add(faq)
                db.flush()  # Get the ID without committing

                # Queue async task
                task = generate_embedding_async.delay(faq.id, faq_data['question'])
                task_ids.append(task.id)
                logger.info(f"  → Task queued: {task.id}")

            db.commit()
            logger.info(f"✓ {len(faq_database)} FAQs created, {len(task_ids)} embedding tasks queued")
            logger.info("  Embeddings will be generated asynchronously by Celery workers")
        else:
            logger.info(f"Seeding {len(faq_database)} FAQs (synchronous mode)...")

            for idx, faq_data in enumerate(faq_database, 1):
                logger.info(f"Processing FAQ {idx}/{len(faq_database)}: {faq_data['question'][:50]}...")

                # Generate embedding synchronously
                try:
                    embedding = generate_embedding(faq_data['question'])
                except Exception as e:
                    logger.error(f"Failed to generate embedding: {str(e)}")
                    continue

                # Create FAQ entry
                faq = FAQ(
                    question=faq_data['question'],
                    answer=faq_data['answer'],
                    embedding=embedding,
                    collection_name=DEFAULT_COLLECTION_NAME
                )

                db.add(faq)

            # Commit all changes
            db.commit()

            # Verify
            final_count = db.query(FAQ).count()
            logger.info(f"✓ Successfully seeded {final_count} FAQs with embeddings")

    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Seed the FAQ database from JSON file')
    parser.add_argument(
        '--json',
        type=str,
        default=None,
        help='Path to JSON file with FAQ data (default: data/faqs.json)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force reseed without prompting (deletes existing FAQs)'
    )
    parser.add_argument(
        '--sync',
        dest='use_async',
        action='store_false',
        default=True,
        help='Use synchronous mode instead of async (Celery is default)'
    )

    args = parser.parse_args()

    logger.info("Starting database seeding...")
    seed_faqs(json_path=args.json, force=args.force, use_async=args.use_async)
    logger.info("Database seeding completed!")
