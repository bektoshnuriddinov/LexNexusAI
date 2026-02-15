-- Fix type mismatch in hybrid_search_chunks function
-- Issue: Column 8 (rrf_score) was returning numeric instead of double precision
-- Cause: ROW_NUMBER() returns bigint, and integer division produces numeric type
-- Solution: Cast rank values to double precision before division

CREATE OR REPLACE FUNCTION hybrid_search_chunks(
    query_text text,
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 20,
    final_count int DEFAULT 5,
    p_user_id uuid DEFAULT NULL,
    metadata_filters jsonb DEFAULT NULL,
    rrf_k int DEFAULT 60
) RETURNS TABLE (
    id uuid,
    document_id uuid,
    content text,
    chunk_index int,
    metadata jsonb,
    vector_similarity float,
    keyword_rank float,
    rrf_score float
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH vector_results AS (
        -- Get vector search results with rankings
        SELECT v.id, v.similarity,
               ROW_NUMBER() OVER (ORDER BY v.similarity DESC) as rank
        FROM match_chunks(query_embedding, match_threshold, match_count, p_user_id, metadata_filters) v
    ),
    keyword_results AS (
        -- Get keyword search results with rankings
        SELECT k.id, k.rank,
               ROW_NUMBER() OVER (ORDER BY k.rank DESC) as rank_position
        FROM keyword_search_chunks(query_text, match_count, p_user_id, metadata_filters) k
    ),
    combined AS (
        -- Combine both results using Reciprocal Rank Fusion (RRF)
        -- RRF score = sum of (1 / (k + rank)) for each search method
        -- Cast rank values to double precision to ensure correct type inference
        SELECT
            COALESCE(v.id, k.id) as id,
            COALESCE(v.similarity, 0)::double precision as vector_similarity,
            COALESCE(k.rank, 0)::double precision as keyword_rank,
            (COALESCE(1.0 / (rrf_k + v.rank::double precision), 0) +
             COALESCE(1.0 / (rrf_k + k.rank_position::double precision), 0))::double precision as rrf_score
        FROM vector_results v
        FULL OUTER JOIN keyword_results k ON v.id = k.id
    )
    SELECT c.id, c.document_id, c.content, c.chunk_index, c.metadata,
           combined.vector_similarity, combined.keyword_rank, combined.rrf_score
    FROM combined
    JOIN chunks c ON c.id = combined.id
    ORDER BY combined.rrf_score DESC
    LIMIT final_count;
END;
$$;

COMMENT ON FUNCTION hybrid_search_chunks IS
'Hybrid search combining vector similarity and keyword matching using Reciprocal Rank Fusion (RRF). Returns top results ranked by RRF score. Fixed type mismatch for rrf_score column.';
