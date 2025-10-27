import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnableBranch
from app.core.config import settings
from app.core.constants import (
    CLASSIFIER_TEMPERATURE,
    CLASSIFIER_MAX_TOKENS,
    COMPLIANCE_MESSAGE
)

logger = logging.getLogger(__name__)

# Initialize LangChain ChatOpenAI for classification
classifier_llm = ChatOpenAI(
    model=settings.chat_model,
    temperature=CLASSIFIER_TEMPERATURE,
    max_tokens=CLASSIFIER_MAX_TOKENS,
    openai_api_key=settings.openai_api_key
)

# Create classification prompt template
classification_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a classification system. Your task is to determine if a question is related to "
     "IT, account management, security, passwords, profiles, settings, notifications, or user accounts. "
     "Respond with ONLY 'IT_RELATED' if the question is IT/account-related, or 'OFF_TOPIC' if it's not. "
     "Examples of IT-related topics: password reset, account settings, profile changes, email changes, "
     "security, authentication, notifications, data recovery. "
     "Examples of non-IT topics: weather, recipes, jokes, general knowledge, sports, entertainment."),
    ("user", "Classify this question: {question}")
])

# Create LangChain classification chain
classification_chain = classification_prompt | classifier_llm


def classify_question(user_question: str) -> bool:
    """
    Classify whether a question is IT/account-related using LangChain.

    Args:
        user_question: The user's question

    Returns:
        True if the question is IT-related, False otherwise
    """
    try:
        result = classification_chain.invoke({"question": user_question})
        classification = result.content.strip().upper()
        is_it_related = "IT_RELATED" in classification or "YES" in classification

        logger.info(
            f"Question classified as {'IT-related' if is_it_related else 'non-IT-related'}: "
            f"'{user_question[:50]}...'"
        )

        return is_it_related

    except Exception as e:
        logger.error(f"Error in question classification: {str(e)}")
        # Default to IT-related on error to avoid blocking legitimate questions
        return True


def get_compliance_response() -> str:
    """
    Get the standard compliance agent response for off-topic questions.

    Returns:
        Compliance agent response message
    """
    return COMPLIANCE_MESSAGE


def route_question(user_question: str) -> tuple[str, bool]:
    """
    Route a question based on whether it's IT-related using LangChain.

    This implements the AI Router using LangChain routing patterns.

    Args:
        user_question: The user's question

    Returns:
        Tuple of (route_type, should_continue)
        - route_type: 'it_related' or 'compliance'
        - should_continue: True if should proceed to FAQ/OpenAI, False if already handled
    """
    is_it_related = classify_question(user_question)

    if is_it_related:
        logger.info("Question routed to FAQ system")
        return "it_related", True
    else:
        logger.info("Question routed to compliance agent")
        return "compliance", False
