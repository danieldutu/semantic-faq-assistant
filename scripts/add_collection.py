#!/usr/bin/env python3
"""
Script to add a new FAQ collection from a JSON file.
"""
import sys
import os
import logging
import argparse
import json
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.db.models import FAQ, Collection
from app.services.embeddings import generate_embedding
from app.celery_app import generate_embedding_async

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_collection(
    json_file: str,
    collection_name: str,
    collection_description: Optional[str] = None,
    dry_run: bool = False,
    use_async: bool = False
) -> None:
    """
    Add a new FAQ collection from a JSON file.

    JSON format:
    [
        {
            "question": "Question text",
            "answer": "Answer text"
        },
        ...
    ]

    Args:
        json_file: Path to JSON file with FAQ data
        collection_name: Name for the new collection
        collection_description: Optional description for the collection
        dry_run: If True, only show what would be done
        use_async: If True, use Celery for async processing

    Raises:
        FileNotFoundError: If the JSON file doesn't exist
        json.JSONDecodeError: If the JSON file is invalid
        Exception: If database operations fail
    """
    # Load JSON file
    try:
        with open(json_file, 'r') as f:
            faq_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {json_file}")
        return
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {str(e)}")
        return

    if not isinstance(faq_data, list):
        logger.error("JSON must be a list of FAQ objects")
        return

    logger.info(f"Loaded {len(faq_data)} FAQs from {json_file}")

    # Validate FAQ data
    for idx, faq in enumerate(faq_data):
        if not isinstance(faq, dict) or 'question' not in faq or 'answer' not in faq:
            logger.error(f"Invalid FAQ at index {idx}: must have 'question' and 'answer' fields")
            return

    if dry_run:
        logger.info("DRY RUN - No changes will be made")
        logger.info(f"Would create collection: {collection_name}")
        for idx, faq in enumerate(faq_data, 1):
            logger.info(f"  {idx}. {faq['question'][:50]}...")
        return

    # Add to database
    db = SessionLocal()
    try:
        # Check if collection already exists
        existing_collection = db.query(Collection).filter(
            Collection.name == collection_name
        ).first()

        if existing_collection:
            logger.warning(f"Collection '{collection_name}' already exists")
            response = input("Continue adding FAQs to this collection? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Operation cancelled")
                return
        else:
            # Create new collection
            collection = Collection(
                name=collection_name,
                description=collection_description or f"FAQ collection: {collection_name}"
            )
            db.add(collection)
            db.commit()
            logger.info(f"✓ Created collection: {collection_name}")

        # Add FAQs with embeddings
        if use_async:
            logger.info(f"Adding {len(faq_data)} FAQs (async mode)...")
            task_ids = []

            for idx, faq_item in enumerate(faq_data, 1):
                logger.info(f"Queuing FAQ {idx}/{len(faq_data)}: {faq_item['question'][:50]}...")

                # Create FAQ entry without embedding first
                faq = FAQ(
                    question=faq_item['question'],
                    answer=faq_item['answer'],
                    embedding=None,
                    collection_name=collection_name
                )
                db.add(faq)
                db.flush()  # Get the ID without committing

                # Queue async task
                task = generate_embedding_async.delay(faq.id, faq_item['question'])
                task_ids.append(task.id)
                logger.info(f"  → Task queued: {task.id}")

            db.commit()
            logger.info(f"✓ Added {len(faq_data)} FAQs to collection '{collection_name}'")
            logger.info(f"✓ {len(task_ids)} embedding tasks queued")
            logger.info("  Embeddings will be generated asynchronously by Celery workers")
        else:
            logger.info(f"Adding {len(faq_data)} FAQs (synchronous mode)...")
            added_count = 0

            for idx, faq_item in enumerate(faq_data, 1):
                logger.info(f"Processing FAQ {idx}/{len(faq_data)}: {faq_item['question'][:50]}...")

                try:
                    # Generate embedding
                    embedding = generate_embedding(faq_item['question'])

                    # Create FAQ entry
                    faq = FAQ(
                        question=faq_item['question'],
                        answer=faq_item['answer'],
                        embedding=embedding,
                        collection_name=collection_name
                    )

                    db.add(faq)
                    added_count += 1
                    logger.info(f"  ✓ Added FAQ with embedding")

                except Exception as e:
                    logger.error(f"  ✗ Failed to add FAQ: {str(e)}")
                    continue

            # Commit all changes
            db.commit()
            logger.info(f"✓ Successfully added {added_count}/{len(faq_data)} FAQs to collection '{collection_name}'")

    except Exception as e:
        logger.error(f"Error adding collection: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add a new FAQ collection from JSON")
    parser.add_argument("json_file", type=str, help="Path to JSON file with FAQ data")
    parser.add_argument("--name", type=str, required=True, help="Collection name")
    parser.add_argument("--description", type=str, help="Collection description")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--sync", dest="use_async", action="store_false", default=True, help="Use synchronous mode instead of async (Celery is default)")

    args = parser.parse_args()

    logger.info("Starting collection addition...")
    add_collection(
        json_file=args.json_file,
        collection_name=args.name,
        collection_description=args.description,
        dry_run=args.dry_run,
        use_async=args.use_async
    )
    logger.info("Collection addition completed!")
