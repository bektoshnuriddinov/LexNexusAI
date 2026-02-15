"""Hybrid search (vector + keyword) with optional reranking."""
import logging
from app.db.supabase import get_supabase_client
from app.services.embedding_service import get_embeddings
from app.services.reranker_service import rerank_chunks

logger = logging.getLogger(__name__)


def normalize_query(query: str) -> str:
    """
    Normalize query text to handle common variations and typos.
    Particularly important for Uzbek text with apostrophes.
    """
    # Replace ALL apostrophe/quote variants with standard apostrophe
    # Uzbek text uses many Unicode variants: ʻ (U+02BB), ʼ (U+02BC), ' (U+2019), etc.
    apostrophe_variants = [
        "'", "ʻ", "'", "`", "ʼ", "´", "ʹ", "ˈ", "'", "‛", "′", "ʹ",  # Various apostrophes
        "ʻ", "ʼ", "ˊ", "ˋ", "˴"  # Modifier letters
    ]
    normalized = query
    for variant in apostrophe_variants:
        normalized = normalized.replace(variant, "'")

    # Also remove apostrophes entirely to create a fallback version
    # This helps match "talim" with "ta'lim"
    return normalized


async def search_documents(
    query: str,
    user_id: str,
    top_k: int = 20,  # Return 20 chunks for complete answers (was 10)
    threshold: float = 0.0,  # No threshold - return any matches (was 0.2)
    metadata_filters: dict | None = None,
    use_reranking: bool = True
) -> list[dict]:
    """
    Search user's documents using hybrid search (vector + keyword) with optional reranking.

    Hybrid search combines:
    1. Vector search (semantic similarity via embeddings)
    2. Keyword search (exact term matching via PostgreSQL full-text search)
    3. RRF fusion (Reciprocal Rank Fusion to combine rankings)
    4. Reranking (cross-encoder model for final relevance scoring)

    Args:
        query: Search query text
        user_id: User ID for RLS filtering
        top_k: Number of final results to return
        threshold: Minimum similarity threshold for vector search
        metadata_filters: Optional metadata filters (e.g., {"document_type": "tutorial"})
        use_reranking: Whether to apply reranking (default True)

    Returns:
        List of reranked chunks with relevance scores
    """
    logger.info(f"🔍 SEARCH START - Query: '{query}' | User: {user_id[:8]}...")

    # Normalize query to handle apostrophe variations
    normalized_query = normalize_query(query)
    logger.info(f"📝 Normalized query: '{query}' → '{normalized_query}'")

    # Get embeddings for both original and normalized query to improve matching
    queries_to_embed = [normalized_query]
    if normalized_query != query:
        queries_to_embed.append(query)

    logger.info(f"🧮 Generating embeddings for {len(queries_to_embed)} query variant(s)...")
    embeddings = await get_embeddings(queries_to_embed, user_id=user_id)
    query_embedding = embeddings[0]  # Use normalized query embedding
    logger.info(f"✓ Embedding generated: {len(query_embedding)} dimensions")

    # Call hybrid search RPC (combines vector + keyword + RRF)
    supabase = get_supabase_client()
    rpc_params = {
        "query_text": normalized_query,  # Use normalized query for text search
        "query_embedding": query_embedding,  # Already indexed above
        "match_threshold": threshold,
        "match_count": 50,  # Retrieve more candidates
        "final_count": 30,  # Return more from RRF
        "p_user_id": user_id,
        "metadata_filters": metadata_filters,
        "rrf_k": 60  # RRF constant (standard value)
    }

    logger.info(f"🔎 Calling hybrid_search_chunks RPC with threshold={threshold}, match_count={rpc_params['match_count']}, final_count={rpc_params['final_count']}")
    result = supabase.rpc("hybrid_search_chunks", rpc_params).execute()
    chunks = result.data or []

    logger.info(f"📊 Hybrid search returned {len(chunks)} chunks")

    if not chunks:
        logger.warning("⚠️  NO CHUNKS FOUND - search returned empty")
        return []

    # Log chunk details
    for i, chunk in enumerate(chunks[:3], 1):  # Log first 3
        logger.info(f"  Chunk {i}: vec_sim={chunk.get('vector_similarity', 0):.3f}, "
                   f"kw_rank={chunk.get('keyword_rank', 0):.3f}, "
                   f"rrf={chunk.get('rrf_score', 0):.4f}")

    # Apply reranking if enabled
    if use_reranking:
        logger.info(f"🔄 Applying reranking (top_n={top_k})...")
        chunks = await rerank_chunks(query, chunks, top_n=top_k)
        logger.info(f"✓ Reranking complete - {len(chunks)} chunks after reranking")
        # Normalize: use rerank_score as similarity
        for chunk in chunks:
            chunk['similarity'] = chunk.get('rerank_score', chunk.get('rrf_score', 0))
    else:
        logger.info(f"⏭️  Skipping reranking - using top {top_k} RRF results")
        chunks = chunks[:top_k]
        # Normalize: use rrf_score as similarity
        for chunk in chunks:
            chunk['similarity'] = chunk.get('rrf_score', 0)

    logger.info(f"✅ SEARCH COMPLETE - Returning {len(chunks)} chunks")
    return chunks
