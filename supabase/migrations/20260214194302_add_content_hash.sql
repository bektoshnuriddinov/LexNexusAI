-- ============================================================================
-- Add content_hash column for document deduplication (Module 4: Record Manager)
-- ============================================================================

-- Add content_hash column to documents table
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS content_hash TEXT;

-- Create index for fast duplicate lookups
-- Used to check if document with same content already exists for a user
CREATE INDEX IF NOT EXISTS idx_documents_user_hash
ON documents(user_id, content_hash);

-- Create index for filename lookups (for update detection)
-- Used to detect when user uploads a file with same name but different content
CREATE INDEX IF NOT EXISTS idx_documents_user_filename
ON documents(user_id, filename);
