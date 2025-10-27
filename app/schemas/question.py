from pydantic import BaseModel, Field
from typing import Optional


class QuestionRequest(BaseModel):
    """Request model for asking a question."""

    user_question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The user's question to be answered",
        examples=["How do I reset my account?"]
    )


class QuestionResponse(BaseModel):
    """Response model for question answers."""

    source: str = Field(
        ...,
        description="Source of the answer: 'local', 'openai', or 'compliance'",
        examples=["local"]
    )
    matched_question: str = Field(
        ...,
        description="The matched question from FAQ database or 'N/A'",
        examples=["How can I restore my account to its default settings?"]
    )
    answer: str = Field(
        ...,
        description="The answer to the user's question",
        examples=["In the account settings, there should be an option labeled 'Restore Default'."]
    )
    similarity_score: Optional[float] = Field(
        None,
        description="Similarity score for local matches (0-1)",
        examples=[0.92]
    )


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., examples=["healthy"])
    database: str = Field(..., examples=["connected"])
    version: str = Field(..., examples=["1.0.0"])
