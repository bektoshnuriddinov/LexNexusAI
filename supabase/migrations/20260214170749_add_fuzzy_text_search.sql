-- Add fuzzy text search support for handling misspellings
-- Enables pg_trgm extension for trigram similarity matching

-- Enable pg_trgm extension for fuzzy text matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Update keyword_search_chunks to be more forgiving with misspellings
-- Uses OR logic to combine exact matches with fuzzy matches
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
    SELECT
        c.id,
        c.document_id,
        c.content,
        c.chunk_index,
        c.metadata,
        -- Combine full-text search rank with trigram similarity for fuzzy matching
        GREATEST(
            ts_rank(c.content_tsv, websearch_to_tsquery('english', query_text)),
            similarity(c.content, query_text) * 0.5  -- Weight trigram similarity lower
        )::double precision AS rank
    FROM chunks c
    WHERE c.user_id = p_user_id
      AND (
          -- Match either full-text search OR trigram similarity
          c.content_tsv @@ websearch_to_tsquery('english', query_text)
          OR similarity(c.content, query_text) > 0.1  -- Low threshold for fuzzy matches
      )
      AND (metadata_filters IS NULL OR c.metadata @> metadata_filters)
    ORDER BY rank DESC
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION keyword_search_chunks IS
'Full-text keyword search with fuzzy matching support. Handles misspellings using trigram similarity.';

-- Create GIN index for trigram similarity (speeds up fuzzy matching)
CREATE INDEX IF NOT EXISTS idx_chunks_content_trgm ON chunks USING GIN (content gin_trgm_ops);
