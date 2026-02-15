-- ============================================================================
-- Add metadata columns for document metadata extraction (Module 5: Metadata Extraction)
-- ============================================================================

-- Add metadata column to documents table
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- Add metadata column to chunks table (inherits from parent document)
ALTER TABLE chunks
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

-- Create GIN index for fast JSONB queries on chunks (primary query target)
CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON chunks USING GIN (metadata);

-- Create GIN index for fast JSONB queries on documents
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN (metadata);

-- Update match_chunks function to support metadata filtering
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
        1 - (c.embedding <=> query_embedding) AS similarity
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
