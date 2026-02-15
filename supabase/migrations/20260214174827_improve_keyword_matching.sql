-- Improve keyword matching to handle partial matches and number searches
-- Makes search much more lenient to find relevant chunks even with format differences

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
        -- Use the best of: full-text rank, trigram similarity, or simple word presence
        GREATEST(
            -- Full-text search score
            COALESCE(ts_rank(c.content_tsv, websearch_to_tsquery('english', query_text)), 0),
            -- Trigram similarity (very lenient threshold)
            CASE WHEN similarity(c.content, query_text) > 0.05
                THEN similarity(c.content, query_text) * 0.7
                ELSE 0
            END,
            -- Partial word matching - check if query words appear in content
            CASE WHEN c.content ILIKE '%' || regexp_replace(query_text, '[^0-9a-zA-Z\s]', '', 'g') || '%'
                THEN 0.3
                ELSE 0
            END
        )::double precision AS rank
    FROM chunks c
    WHERE c.user_id = p_user_id
      AND (
          -- Match if ANY of these conditions are true:
          -- 1. Full-text search matches
          c.content_tsv @@ websearch_to_tsquery('english', query_text)
          -- 2. Trigram similarity > 0.05 (very lenient)
          OR similarity(c.content, query_text) > 0.05
          -- 3. Content contains any significant word from query (3+ chars)
          OR c.content ILIKE '%' || (
              SELECT string_agg(word, '%')
              FROM unnest(string_to_array(query_text, ' ')) AS word
              WHERE length(word) >= 3
              LIMIT 1
          ) || '%'
      )
      AND (metadata_filters IS NULL OR c.metadata @> metadata_filters)
    ORDER BY rank DESC
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION keyword_search_chunks IS
'Improved keyword search with very lenient matching - handles partial words, numbers, and format variations';
