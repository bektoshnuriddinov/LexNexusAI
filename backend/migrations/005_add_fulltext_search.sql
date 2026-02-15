-- ============================================================================
-- Add Full-Text Search (Module 7: Hybrid Search & Reranking)
-- ============================================================================

-- This migration adds PostgreSQL full-text search capabilities to the chunks table
-- for keyword-based search alongside vector search

-- ============================================================================
-- PART 1: Add tsvector column for full-text search
-- ============================================================================

-- Add generated tsvector column that automatically updates when content changes
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS content_tsv tsvector
  GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;

-- Create GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS idx_chunks_content_tsv ON chunks USING GIN (content_tsv);

-- ============================================================================
-- PART 2: Keyword Search Function
-- ============================================================================

-- Function for full-text keyword search
CREATE OR REPLACE FUNCTION keyword_search_chunks(
    query_text text,
    match_count int,
    p_user_id uuid,
    metadata_filters jsonb DEFAULT NULL
) RETURNS TABLE (
    id uuid,
    document_id uuid,
    content text,
    chunk_index int,
    metadata jsonb,
    rank float
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.document_id, c.content, c.chunk_index, c.metadata,
           ts_rank(c.content_tsv, websearch_to_tsquery('english', query_text)) AS rank
    FROM chunks c
    WHERE c.user_id = p_user_id
      AND c.content_tsv @@ websearch_to_tsquery('english', query_text)
      AND (metadata_filters IS NULL OR c.metadata @> metadata_filters)
    ORDER BY rank DESC
    LIMIT match_count;
END;
$$;

-- Add function comment
COMMENT ON FUNCTION keyword_search_chunks IS
'Full-text keyword search on chunks using PostgreSQL tsvector. Returns chunks ranked by ts_rank.';

-- ============================================================================
-- PART 3: Hybrid Search Function with RRF
-- ============================================================================

-- Function that combines vector search + keyword search using Reciprocal Rank Fusion (RRF)
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

-- Add function comment
COMMENT ON FUNCTION hybrid_search_chunks IS
'Hybrid search combining vector similarity and keyword matching using Reciprocal Rank Fusion (RRF). Returns top results ranked by RRF score.';

-- ============================================================================
-- PART 4: Add Reranker Settings to Global Settings
-- ============================================================================

-- Add reranker configuration columns to global_settings table
ALTER TABLE global_settings ADD COLUMN IF NOT EXISTS jina_api_key TEXT;
ALTER TABLE global_settings ADD COLUMN IF NOT EXISTS jina_rerank_model TEXT DEFAULT 'jina-reranker-v2-base-multilingual';
ALTER TABLE global_settings ADD COLUMN IF NOT EXISTS jina_rerank_enabled BOOLEAN DEFAULT FALSE;

-- Add comments
COMMENT ON COLUMN global_settings.jina_api_key IS 'Jina AI API key for reranking service (encrypted)';
COMMENT ON COLUMN global_settings.jina_rerank_model IS 'Jina AI reranker model name';
COMMENT ON COLUMN global_settings.jina_rerank_enabled IS 'Whether reranking is enabled for hybrid search';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify tsvector column exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'chunks'
        AND column_name = 'content_tsv'
    ) THEN
        RAISE NOTICE 'SUCCESS: content_tsv column added to chunks table';
    ELSE
        RAISE WARNING 'FAILED: content_tsv column not found';
    END IF;
END $$;

-- Verify GIN index exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_indexes
        WHERE tablename = 'chunks'
        AND indexname = 'idx_chunks_content_tsv'
    ) THEN
        RAISE NOTICE 'SUCCESS: GIN index created on content_tsv';
    ELSE
        RAISE WARNING 'FAILED: GIN index not found';
    END IF;
END $$;

-- Verify functions exist
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_proc
        WHERE proname = 'keyword_search_chunks'
    ) THEN
        RAISE NOTICE 'SUCCESS: keyword_search_chunks function created';
    ELSE
        RAISE WARNING 'FAILED: keyword_search_chunks function not found';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_proc
        WHERE proname = 'hybrid_search_chunks'
    ) THEN
        RAISE NOTICE 'SUCCESS: hybrid_search_chunks function created';
    ELSE
        RAISE WARNING 'FAILED: hybrid_search_chunks function not found';
    END IF;
END $$;
