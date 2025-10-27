import logging
from typing import Optional, Tuple
from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.db.models import FAQ
from app.services.embeddings import generate_embedding

logger = logging.getLogger(__name__)


def search_similar_faq(
    db: Session,
    user_question: str,
    collection_name: Optional[str] = None
) -> Tuple[Optional[FAQ], float]:
    """
    Search for the most similar FAQ using pgVector cosine similarity.

    Uses a single optimized database query that leverages pgVector's built-in
    similarity search and IVFFlat index for O(log n) performance.

    Args:
        db: Database session
        user_question: The user's question
        collection_name: Optional collection name to filter by

    Returns:
        Tuple of (FAQ object or None, similarity score)

    Raises:
        Exception: If embedding generation fails (propagated from generate_embedding)
    """
    # Generate embedding for user's question
    query_embedding = generate_embedding(user_question)

    # Single optimized query using pgVector similarity search
    # This leverages the IVFFlat index for sub-linear performance
    query = db.query(
        FAQ,
        (1 - FAQ.embedding.cosine_distance(query_embedding)).label('similarity')
    ).filter(
        FAQ.embedding.isnot(None)
    )

    # Apply optional collection filter
    if collection_name:
        query = query.filter(FAQ.collection_name == collection_name)

    # Order by similarity (descending) and get the top result
    # pgVector index is used here for efficient nearest neighbor search
    result = query.order_by(desc('similarity')).first()

    if not result:
        logger.warning("No FAQs found in database")
        return None, 0.0

    # Unpack the result tuple: (FAQ object, similarity score)
    best_faq, similarity_score = result
    similarity_score = float(similarity_score)

    logger.info(
        f"Found similar FAQ (id={best_faq.id}) with similarity: {similarity_score:.4f}"
    )
    return best_faq, similarity_score


def find_best_match(
    db: Session,
    user_question: str,
    threshold: float,
    collection_name: Optional[str] = None
) -> Tuple[Optional[FAQ], float, bool]:
    """
    Find the best matching FAQ and determine if it meets the threshold.

    Args:
        db: Database session
        user_question: The user's question
        threshold: Minimum similarity threshold
        collection_name: Optional collection name to filter by

    Returns:
        Tuple of (FAQ object or None, similarity score, is_above_threshold)
    """
    faq, similarity_score = search_similar_faq(db, user_question, collection_name)

    if faq and similarity_score >= threshold:
        logger.info(
            f"Match above threshold ({similarity_score:.4f} >= {threshold}): {faq.question}"
        )
        return faq, similarity_score, True
    else:
        logger.info(
            f"No match above threshold (best: {similarity_score:.4f}, threshold: {threshold})"
        )
        return faq, similarity_score, False
