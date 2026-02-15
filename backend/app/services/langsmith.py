"""LangSmith tracing configuration for OpenAI API calls."""
import os
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Set LangSmith environment variables BEFORE importing langsmith
if settings.langsmith_api_key:
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    os.environ["LANGSMITH_ENDPOINT"] = "https://eu.api.smith.langchain.com"
else:
    logger.warning("LangSmith API key not configured - tracing disabled")

# Import langsmith AFTER setting env vars
import langsmith
from langsmith.wrappers import wrap_openai
from openai import OpenAI, AsyncOpenAI

# Log LangSmith configuration for debugging
if settings.langsmith_api_key:
    api_key_preview = settings.langsmith_api_key[:8] + "..." if len(settings.langsmith_api_key) > 8 else "***"
    logger.info(f"LangSmith enabled: project={settings.langsmith_project}")
    logger.debug(f"LangSmith SDK version: {langsmith.__version__}")
    logger.debug(f"LangSmith API key: {api_key_preview}")

    # Test LangSmith connectivity on startup
    try:
        from langsmith import Client
        ls_client = Client()
        logger.debug("LangSmith client initialized")

        # Test trace
        with langsmith.trace("startup_test", project_name=settings.langsmith_project) as run:
            run.end(outputs={"status": "LangSmith connection verified"})
        logger.debug("LangSmith test trace sent")
    except Exception as e:
        logger.error(f"LangSmith startup test failed: {e}")
        logger.error("Traces may not appear in dashboard")


def get_traced_openai_client(base_url: str | None = None, api_key: str | None = None) -> OpenAI:
    """
    Get an OpenAI client wrapped with LangSmith tracing.

    Args:
        base_url: Optional base URL for the API (e.g., OpenRouter, Ollama)
        api_key: Optional API key (falls back to openai_api_key)
    """
    effective_key = api_key or settings.openai_api_key
    client = OpenAI(api_key=effective_key, base_url=base_url or None)

    if settings.langsmith_api_key:
        wrapped = wrap_openai(client)
        logger.debug(f"OpenAI client wrapped with LangSmith (base_url={base_url})")
        return wrapped

    return client


def get_traced_async_openai_client(base_url: str | None = None, api_key: str | None = None) -> AsyncOpenAI:
    """
    Get an AsyncOpenAI client wrapped with LangSmith tracing.

    Args:
        base_url: Optional base URL for the API (e.g., OpenRouter, Ollama)
        api_key: Optional API key (falls back to openai_api_key)
    """
    effective_key = api_key or settings.openai_api_key
    client = AsyncOpenAI(api_key=effective_key, base_url=base_url or None)

    if settings.langsmith_api_key:
        try:
            wrapped = wrap_openai(client)
            logger.debug(f"AsyncOpenAI wrapped with LangSmith (base_url={base_url or 'default'}, project={settings.langsmith_project})")
            return wrapped
        except Exception as e:
            logger.error(f"Failed to wrap AsyncOpenAI client: {e}")
            return client
    else:
        logger.warning("LangSmith tracing disabled (no API key)")
        return client
