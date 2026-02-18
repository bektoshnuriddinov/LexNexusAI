"""Reranking service using Jina AI Reranker API."""
import os
import logging
from typing import List
import httpx


DEFAULT_JINA_RERANK_MODEL = "jina-reranker-v2-base-multilingual"

logger = logging.getLogger(__name__)


def get_reranker_settings() -> dict:
    """
    Get reranker settings from the global_settings table.
    Falls back to environment variables if not configured in DB.
    """
    from app.db.supabase import get_supabase_client
    from app.routers.settings import decrypt_value

    api_key = None
    model = None
    enabled = False

    try:
        supabase = get_supabase_client()
        result = supabase.table("global_settings").select(
            "jina_api_key, jina_rerank_model, jina_rerank_enabled"
        ).limit(1).maybe_single().execute()

        data = result.data if result else None
        if data:
            api_key = decrypt_value(data.get("jina_api_key"))
            model = data.get("jina_rerank_model")
            enabled = data.get("jina_rerank_enabled", False) or False
    except Exception as e:
        logger.warning(f"Could not load reranker settings from DB: {e}. Falling back to env vars.")

    # Fallback to environment variables
    if not api_key:
        api_key = os.getenv("JINA_API_KEY", "")
    if not model:
        model = os.getenv("JINA_RERANK_MODEL", DEFAULT_JINA_RERANK_MODEL)
    if not enabled:
        enabled = os.getenv("JINA_RERANK_ENABLED", "false").lower() == "true"

    return {"api_key": api_key, "model": model, "enabled": enabled}


async def rerank_chunks(
    query: str,
    chunks: List[dict],
    top_n: int = 5
) -> List[dict]:
    """
    Rerank chunks using Jina AI Reranker API.

    The reranker uses a cross-encoder model to score query-document pairs,
    providing more accurate relevance ranking than RRF alone.

    Args:
        query: User query
        chunks: List of chunks from hybrid search (must have 'content' field)
        top_n: Number of top results to return after reranking

    Returns:
        Reranked list of chunks with 'rerank_score' added

    Raises:
        httpx.HTTPError: If the API request fails
    """
    settings = get_reranker_settings()
    jina_api_key = settings["api_key"]
    jina_rerank_model = settings["model"]
    jina_rerank_enabled = settings["enabled"]

    # Return original chunks if reranking disabled or no API key
    if not jina_rerank_enabled or not jina_api_key:
        return chunks[:top_n]

    if not chunks:
        return []

    # Prepare documents for reranking (extract text content)
    documents = [chunk["content"] for chunk in chunks]

    try:
        # Call Jina Reranker API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.jina.ai/v1/rerank",
                headers={
                    "Authorization": f"Bearer {jina_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": jina_rerank_model,
                    "query": query,
                    "documents": documents,
                    "top_n": min(top_n, len(documents))  # Don't request more than available
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

        # Map reranked results back to original chunks
        reranked = []
        for item in result.get("results", []):
            original_index = item["index"]
            chunk = chunks[original_index].copy()
            chunk["rerank_score"] = item["relevance_score"]
            reranked.append(chunk)

        return reranked

    except httpx.HTTPError as e:
        logger.error(f"Reranking API error: {e}. Falling back to RRF ranking.")
        return chunks[:top_n]
    except (KeyError, IndexError) as e:
        logger.error(f"Reranking response parsing error: {e}. Falling back to RRF ranking.")
        return chunks[:top_n]
