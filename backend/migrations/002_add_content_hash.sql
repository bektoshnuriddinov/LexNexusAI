-- Add content_hash column to documents table
-- This enables deduplication by detecting when the same file is uploaded multiple times

ALTER TABLE documents
ADD COLUMN content_hash TEXT;

-- Create index for fast duplicate lookups
-- Used to check if document with same content already exists for a user
CREATE INDEX idx_documents_user_hash
ON documents(user_id, content_hash);

-- Create index for filename lookups (for update detection)
-- Used to detect when user uploads a file with same name but different content
CREATE INDEX idx_documents_user_filename
ON documents(user_id, filename);
