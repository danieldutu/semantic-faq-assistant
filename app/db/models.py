from sqlalchemy import Column, Integer, String, Text, DateTime, func
from pgvector.sqlalchemy import Vector
from app.db.database import Base
from app.core.config import settings
from app.core.constants import DEFAULT_COLLECTION_NAME, MAX_COLLECTION_NAME_LENGTH


class FAQ(Base):
    """FAQ model for storing questions, answers, and embeddings."""

    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    embedding = Column(Vector(settings.embedding_dimension))
    collection_name = Column(String(MAX_COLLECTION_NAME_LENGTH), default=DEFAULT_COLLECTION_NAME)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<FAQ(id={self.id}, question='{self.question[:50]}...')>"


class Collection(Base):
    """Collection model for organizing FAQs."""

    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(MAX_COLLECTION_NAME_LENGTH), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Collection(id={self.id}, name='{self.name}')>"
