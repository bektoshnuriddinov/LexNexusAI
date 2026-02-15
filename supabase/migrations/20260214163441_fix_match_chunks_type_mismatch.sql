-- Fix type mismatch in match_chunks function
-- Issue: Column 6 (similarity) in hybrid_search_chunks was returning real instead of double precision
-- Cause: The cosine distance operator (<=>)  returns real (single precision), not double precision
-- Solution: Cast similarity to double precision explicitly

CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding vector(1536),
    match_threshold float,
    match_count int,
    user_id_param uuid,
    metadata_filters jsonb DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    content text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.document_id,
        c.content,
        c.metadata,
        (1 - (c.embedding <=> query_embedding))::double precision AS similarity
    FROM chunks c
    WHERE
        c.user_id = user_id_param
        AND 1 - (c.embedding <=> query_embedding) > match_threshold
        -- Apply metadata filters if provided (JSONB containment operator)
        AND (
            metadata_filters IS NULL
            OR c.metadata @> metadata_filters
        )
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Also fix keyword_search_chunks function
-- Issue: ts_rank returns real, not double precision
-- Solution: Cast rank to double precision explicitly

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
           ts_rank(c.content_tsv, websearch_to_tsquery('english', query_text))::double precision AS rank
    FROM chunks c
    WHERE c.user_id = p_user_id
      AND c.content_tsv @@ websearch_to_tsquery('english', query_text)
      AND (metadata_filters IS NULL OR c.metadata @> metadata_filters)
    ORDER BY rank DESC
    LIMIT match_count;
END;
$$;
