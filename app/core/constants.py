"""
Application-wide constants and magic numbers.

This module centralizes all hardcoded values to improve maintainability
and prevent inconsistencies across the codebase.
"""

# ============================================================================
# Collection Configuration
# ============================================================================

DEFAULT_COLLECTION_NAME = "default"
"""Default collection name for FAQs when none is specified."""

DEFAULT_COLLECTION_DESCRIPTION = "Default FAQ collection"
"""Default description for the default collection."""

MAX_COLLECTION_NAME_LENGTH = 100
"""Maximum length for collection names in the database."""


# ============================================================================
# OpenAI API Configuration
# ============================================================================

# Classifier (AI Router) Configuration
CLASSIFIER_TEMPERATURE = 0.0
"""Temperature for AI Router classification (0.0 = deterministic)."""

CLASSIFIER_MAX_TOKENS = 10
"""Maximum tokens for AI Router response (binary classification only)."""

# Chat Completion Configuration
CHAT_TEMPERATURE = 0.7
"""Temperature for chat completions (0.7 = creative but controlled)."""

CHAT_MAX_TOKENS = 300
"""Maximum tokens for chat completion responses."""


# ============================================================================
# Retry Configuration
# ============================================================================

RETRY_MAX_ATTEMPTS = 3
"""Maximum number of retry attempts for failed API calls."""

RETRY_MIN_WAIT = 2
"""Minimum wait time (seconds) between retry attempts."""

RETRY_MAX_WAIT = 10
"""Maximum wait time (seconds) between retry attempts."""

RETRY_MULTIPLIER = 1
"""Multiplier for exponential backoff between retries."""


# ============================================================================
# Compliance Messages
# ============================================================================

COMPLIANCE_MESSAGE = "This is not really what I was trained for, therefore I cannot answer. Try again."
"""Message returned when user asks off-topic questions."""
