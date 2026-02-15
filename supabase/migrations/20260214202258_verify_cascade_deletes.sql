-- ============================================================================
-- Verify cascade delete constraints (Module 6: Multi-Format Support)
-- ============================================================================

-- This migration verifies that chunks table has proper CASCADE delete constraint
-- When a document is deleted, all its chunks should be automatically removed

-- Verify that the foreign key constraint exists with CASCADE delete
DO $$
BEGIN
    -- Check if the constraint exists with CASCADE
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.referential_constraints rc
        JOIN information_schema.table_constraints tc
            ON tc.constraint_name = rc.constraint_name
        WHERE tc.table_name = 'chunks'
            AND tc.constraint_type = 'FOREIGN KEY'
            AND rc.delete_rule = 'CASCADE'
    ) THEN
        RAISE NOTICE 'Foreign key constraint with CASCADE not found, will be added';

        -- Drop existing constraint if it exists without CASCADE
        ALTER TABLE chunks
        DROP CONSTRAINT IF EXISTS chunks_document_id_fkey;

        -- Add constraint with CASCADE delete
        ALTER TABLE chunks
        ADD CONSTRAINT chunks_document_id_fkey
        FOREIGN KEY (document_id)
        REFERENCES documents(id)
        ON DELETE CASCADE;

        RAISE NOTICE 'CASCADE constraint added successfully';
    ELSE
        RAISE NOTICE 'CASCADE constraint already exists - no action needed';
    END IF;
END $$;

-- Add comment for documentation
COMMENT ON CONSTRAINT chunks_document_id_fkey ON chunks IS
'Cascade delete: when a document is deleted, all its chunks are automatically removed to prevent orphaned data';

-- Verify the constraint
DO $$
DECLARE
    v_delete_rule TEXT;
BEGIN
    SELECT rc.delete_rule INTO v_delete_rule
    FROM information_schema.referential_constraints rc
    JOIN information_schema.table_constraints tc
        ON tc.constraint_name = rc.constraint_name
    WHERE tc.table_name = 'chunks'
        AND tc.constraint_type = 'FOREIGN KEY';

    IF v_delete_rule = 'CASCADE' THEN
        RAISE NOTICE 'Verification successful: CASCADE delete rule is active';
    ELSE
        RAISE WARNING 'Verification failed: Expected CASCADE, got %', v_delete_rule;
    END IF;
END $$;
