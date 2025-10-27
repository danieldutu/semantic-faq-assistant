"""
Reusable decorators for the application.
"""
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.constants import (
    RETRY_MAX_ATTEMPTS,
    RETRY_MIN_WAIT,
    RETRY_MAX_WAIT,
    RETRY_MULTIPLIER
)


def retry_on_api_error():
    """
    Retry decorator for API calls with exponential backoff.

    Retries failed API calls up to RETRY_MAX_ATTEMPTS times with exponential
    backoff between attempts. Configuration is centralized in constants.py.

    Returns:
        A tenacity retry decorator configured with application defaults

    Example:
        @retry_on_api_error()
        def call_external_api():
            # API call that might fail
            pass
    """
    return retry(
        stop=stop_after_attempt(RETRY_MAX_ATTEMPTS),
        wait=wait_exponential(
            multiplier=RETRY_MULTIPLIER,
            min=RETRY_MIN_WAIT,
            max=RETRY_MAX_WAIT
        ),
        reraise=True
    )
