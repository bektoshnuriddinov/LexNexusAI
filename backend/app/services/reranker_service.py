"""Reranking service using Jina AI Reranker API."""
import os
from typing import List
import httpx


JINA_API_KEY = os.getenv("JINA_API_KEY", "")
JINA_RERANK_MODEL = os.getenv("JINA_RERANK_MODEL", "jina-reranker-v2-base-multilingual")
JINA_RERANK_ENABLED = os.getenv("JINA_RERANK_ENABLED", "false").lower() == "true"


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
    # Return original chunks if reranking disabled or no API key
    if not JINA_RERANK_ENABLED or not JINA_API_KEY:
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
                    "Authorization": f"Bearer {JINA_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": JINA_RERANK_MODEL,
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
        # Log error but don't fail - fall back to original ranking
        print(f"Reranking API error: {e}. Falling back to RRF ranking.")
        return chunks[:top_n]
    except (KeyError, IndexError) as e:
        # Handle unexpected response format
        print(f"Reranking response parsing error: {e}. Falling back to RRF ranking.")
        return chunks[:top_n]
