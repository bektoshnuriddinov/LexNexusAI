-- ============================================================================
-- SHARED DOCUMENTS ACCESS
-- Allow all authenticated users to read documents uploaded by admins
-- Only admins can create/update/delete documents
-- ============================================================================

-- Drop old restrictive policies
DROP POLICY IF EXISTS "users_own_documents" ON documents;
DROP POLICY IF EXISTS "users_own_chunks" ON chunks;
DROP POLICY IF EXISTS "users_upload_own_documents" ON storage.objects;
DROP POLICY IF EXISTS "users_read_own_documents" ON storage.objects;
DROP POLICY IF EXISTS "users_delete_own_documents" ON storage.objects;

-- ============================================================================
-- NEW DOCUMENT POLICIES: All users can READ, only admins can WRITE
-- ============================================================================

-- All authenticated users can view all documents
CREATE POLICY "authenticated_users_view_documents"
ON documents FOR SELECT
USING (auth.role() = 'authenticated');

-- Only admins can insert documents
CREATE POLICY "admins_insert_documents"
ON documents FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid() AND is_admin = true
    )
);

-- Only admins can update documents
CREATE POLICY "admins_update_documents"
ON documents FOR UPDATE
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid() AND is_admin = true
    )
);

-- Only admins can delete documents
CREATE POLICY "admins_delete_documents"
ON documents FOR DELETE
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid() AND is_admin = true
    )
);

-- ============================================================================
-- NEW CHUNK POLICIES: All users can READ, only admins can WRITE
-- ============================================================================

-- All authenticated users can view all chunks
CREATE POLICY "authenticated_users_view_chunks"
ON chunks FOR SELECT
USING (auth.role() = 'authenticated');

-- Only admins can insert chunks
CREATE POLICY "admins_insert_chunks"
ON chunks FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid() AND is_admin = true
    )
);

-- Only admins can delete chunks (via cascade)
CREATE POLICY "admins_delete_chunks"
ON chunks FOR DELETE
USING (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid() AND is_admin = true
    )
);

-- ============================================================================
-- STORAGE POLICIES: Admins only
-- ============================================================================

-- Only admins can upload documents
CREATE POLICY "admins_upload_documents"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'documents'
    AND EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid() AND is_admin = true
    )
);

-- All authenticated users can read documents
CREATE POLICY "authenticated_users_read_documents"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'documents'
    AND auth.role() = 'authenticated'
);

-- Only admins can delete documents
CREATE POLICY "admins_delete_storage_documents"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'documents'
    AND EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid() AND is_admin = true
    )
);

-- ============================================================================
-- UPDATE SEARCH FUNCTIONS: Remove user_id filter
-- ============================================================================

-- Update hybrid_search_chunks to search ALL documents (not filtered by user)
-- This will be called with p_user_id but we'll ignore it for the filter
CREATE OR REPLACE FUNCTION hybrid_search_chunks(
    query_text TEXT,
    query_embedding vector(1536),
    match_threshold float,
    match_count int,
    final_count int,
    p_user_id uuid,
    metadata_filters jsonb DEFAULT NULL,
    rrf_k int DEFAULT 60
) RETURNS TABLE (
    id uuid,
    document_id uuid,
    content text,
    chunk_index int,
    metadata jsonb,
    vector_similarity double precision,
    keyword_rank real,
    rrf_score double precision
) LANGUAGE plpgsql AS $$
DECLARE
    vector_results RECORD;
    keyword_results RECORD;
BEGIN
    -- Reciprocal Rank Fusion (RRF) combining vector and keyword search
    -- Note: Removed user_id filter to allow searching all documents
    RETURN QUERY
    WITH vector_search AS (
        SELECT
            c.id,
            c.document_id,
            c.content,
            c.chunk_index,
            c.metadata,
            1 - (c.embedding <=> query_embedding) AS similarity,
            ROW_NUMBER() OVER (ORDER BY c.embedding <=> query_embedding) AS rank
        FROM chunks c
        WHERE 1 - (c.embedding <=> query_embedding) > match_threshold
            AND (metadata_filters IS NULL OR c.metadata @> metadata_filters)
        ORDER BY c.embedding <=> query_embedding
        LIMIT match_count
    ),
    keyword_search AS (
        SELECT
            c.id,
            c.document_id,
            c.content,
            c.chunk_index,
            c.metadata,
            ts_rank(to_tsvector('russian', c.content), plainto_tsquery('russian', query_text)) AS rank_score,
            ROW_NUMBER() OVER (ORDER BY ts_rank(to_tsvector('russian', c.content), plainto_tsquery('russian', query_text)) DESC) AS rank
        FROM chunks c
        WHERE to_tsvector('russian', c.content) @@ plainto_tsquery('russian', query_text)
            AND (metadata_filters IS NULL OR c.metadata @> metadata_filters)
        ORDER BY rank_score DESC
        LIMIT match_count
    ),
    rrf_scores AS (
        SELECT
            COALESCE(v.id, k.id) AS id,
            COALESCE(v.document_id, k.document_id) AS document_id,
            COALESCE(v.content, k.content) AS content,
            COALESCE(v.chunk_index, k.chunk_index) AS chunk_index,
            COALESCE(v.metadata, k.metadata) AS metadata,
            COALESCE(v.similarity, 0) AS vector_similarity,
            COALESCE(k.rank_score, 0) AS keyword_rank,
            (COALESCE(1.0 / (rrf_k + v.rank), 0.0) + COALESCE(1.0 / (rrf_k + k.rank), 0.0))::double precision AS rrf_score
        FROM vector_search v
        FULL OUTER JOIN keyword_search k ON v.id = k.id
    )
    SELECT
        rrf.id,
        rrf.document_id,
        rrf.content,
        rrf.chunk_index,
        rrf.metadata,
        rrf.vector_similarity,
        rrf.keyword_rank,
        rrf.rrf_score
    FROM rrf_scores rrf
    ORDER BY rrf.rrf_score DESC
    LIMIT final_count;
END;
$$;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON POLICY "authenticated_users_view_documents" ON documents IS
'All authenticated users can view all documents (admin-uploaded documents are shared)';

COMMENT ON POLICY "authenticated_users_view_chunks" ON chunks IS
'All authenticated users can search all chunks (enables RAG for all users)';

COMMENT ON POLICY "admins_insert_documents" ON documents IS
'Only admins can upload new documents';

COMMENT ON FUNCTION hybrid_search_chunks IS
'Hybrid search across ALL documents - no user_id filtering (shared document model)';
