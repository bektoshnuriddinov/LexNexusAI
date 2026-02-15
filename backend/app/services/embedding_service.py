"""Embedding service using configured provider."""
from typing import Any

from fastapi import HTTPException, status

from app.db.supabase import get_supabase_client
from app.services.langsmith import get_traced_async_openai_client
from app.routers.settings import decrypt_value


def get_global_embedding_settings() -> dict[str, Any]:
    """
    Get global embedding settings from the global_settings table.
    Falls back to environment variables if global_settings is not configured.

    Returns dict with keys: model, base_url, api_key, dimensions
    Raises HTTPException(503) if no API key is configured.
    """
    from app.config import get_settings

    supabase = get_supabase_client()
    api_key = None
    model = None
    base_url = None
    dimensions = None

    try:
        result = supabase.table("global_settings").select(
            "embedding_model, embedding_base_url, embedding_api_key, embedding_dimensions"
        ).limit(1).maybe_single().execute()

        data = result.data if result else None
        if data:
            api_key = decrypt_value(data.get("embedding_api_key"))
            model = data.get("embedding_model")
            base_url = data.get("embedding_base_url")
            dimensions = data.get("embedding_dimensions")
    except Exception:
        # Table doesn't exist or query failed - will fall back to env vars
        pass

    # Fallback to environment variables
    if not api_key:
        settings = get_settings()
        api_key = settings.embedding_api_key or settings.openai_api_key
        model = model or settings.embedding_model
        base_url = base_url or settings.embedding_base_url or None
        dimensions = dimensions or settings.embedding_dimensions

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding not configured. Set EMBEDDING_API_KEY in .env or configure via Settings UI."
        )

    return {
        "model": model or "text-embedding-3-small",
        "base_url": base_url,
        "api_key": api_key,
        "dimensions": dimensions or 1536,
    }


async def get_embeddings(texts: list[str], user_id: str | None = None) -> list[list[float]]:
    """Generate embeddings for a list of texts using global settings."""
    emb_settings = get_global_embedding_settings()
    model = emb_settings["model"]
    dimensions = emb_settings["dimensions"]

    client = get_traced_async_openai_client(
        base_url=emb_settings["base_url"],
        api_key=emb_settings["api_key"],
    )

    response = await client.embeddings.create(
        model=model,
        input=texts,
        dimensions=dimensions,
    )
    return [item.embedding for item in response.data]
