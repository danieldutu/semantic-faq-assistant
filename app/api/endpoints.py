import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.schemas.question import QuestionRequest, QuestionResponse, HealthResponse
from app.db.database import get_db
from app.core.auth import get_token
from app.core.config import settings
from app.services.similarity import find_best_match
from app.services.openai_service import get_openai_answer
from app.services.router import route_question, get_compliance_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint to verify service and database status.
    """
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        database=db_status,
        version="1.0.0"
    )


@router.post(
    "/ask-question",
    response_model=QuestionResponse,
    dependencies=[Depends(get_token)]
)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Main endpoint to answer user questions.

    Process:
    1. Route question to check if IT-related (AI Router)
    2. If IT-related, search for similar FAQ in database
    3. If similarity above threshold, return local answer
    4. Otherwise, forward to OpenAI API

    Authentication required via Authorization header.
    """
    user_question = request.user_question.strip()

    if not user_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty"
        )

    try:
        # Step 1: Route the question (AI Router - Bonus #5)
        route_type, should_continue = route_question(user_question)

        if not should_continue:
            # Question is off-topic, return compliance response
            logger.info(f"Returning compliance response for: '{user_question[:50]}...'")
            return QuestionResponse(
                source="compliance",
                matched_question="N/A",
                answer=get_compliance_response(),
                similarity_score=None
            )

        # Step 2: Search for similar FAQ
        faq, similarity_score, is_above_threshold = find_best_match(
            db=db,
            user_question=user_question,
            threshold=settings.similarity_threshold
        )

        # Step 3: Return local match or OpenAI fallback
        if is_above_threshold and faq:
            logger.info(
                f"Returning local answer (similarity: {similarity_score:.4f})"
            )
            return QuestionResponse(
                source="local",
                matched_question=faq.question,
                answer=faq.answer,
                similarity_score=round(similarity_score, 4)
            )
        else:
            # Forward to OpenAI API
            logger.info(
                f"Forwarding to OpenAI (similarity: {similarity_score:.4f} < threshold: {settings.similarity_threshold})"
            )
            openai_answer = get_openai_answer(user_question)

            return QuestionResponse(
                source="openai",
                matched_question="N/A",
                answer=openai_answer,
                similarity_score=round(similarity_score, 4) if faq else None
            )

    except Exception as e:
        logger.error(f"Error processing question: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing your question: {str(e)}"
        )
