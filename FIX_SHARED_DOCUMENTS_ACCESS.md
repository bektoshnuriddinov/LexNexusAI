# Fix: Shared Documents Access

**Date:** 2026-02-15
**Issue:** Regular users couldn't query documents - only admin could use RAG
**Root Cause:** Architecture was set up for "each user uploads their own documents" instead of "admin uploads, everyone uses"

---

## Problem Details

### What Was Happening:
1. ✅ **Admin account:** Could upload documents and query them successfully
2. ❌ **Regular user accounts:** Couldn't get RAG responses - system said no documents available

### Root Causes:

**1. RLS Policies (Database Level)**
```sql
-- OLD: Users could only see THEIR OWN documents
CREATE POLICY "users_own_documents" ON documents
FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "users_own_chunks" ON chunks
FOR ALL USING (auth.uid() = user_id);
```
Result: Regular users couldn't see admin's uploaded documents.

**2. Backend Check (Code Level)**
```python
# OLD: Checked if CURRENT USER has documents
def user_has_documents(user_id: str) -> bool:
    result = supabase.table("documents").select("id").eq(
        "user_id", user_id  # ← Filtered by current user
    ).eq("status", "completed").execute()
    return (result.count or 0) > 0
```
Result: Regular users had count=0, so RAG tools weren't provided.

**3. Search Function (Database Level)**
```sql
-- OLD: Filtered chunks by user_id
WHERE c.user_id = p_user_id  -- ← Only returned user's own chunks
```
Result: Even if tools were provided, search would return no results.

---

## Solution: Shared Access Model

### New Architecture:
- 👨‍💼 **Admin:** Uploads documents for the entire system
- 👥 **All Users:** Can query ALL documents uploaded by admin
- 🔒 **Security:** Only admins can upload/delete, users can only read

---

## Changes Made

### 1. Database Migration

**File:** `supabase/migrations/20260215000000_shared_documents_access.sql`

#### New RLS Policies:

**Documents Table:**
```sql
-- All authenticated users can READ
CREATE POLICY "authenticated_users_view_documents"
ON documents FOR SELECT
USING (auth.role() = 'authenticated');

-- Only admins can INSERT/UPDATE/DELETE
CREATE POLICY "admins_insert_documents"
ON documents FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid() AND is_admin = true
    )
);
```

**Chunks Table:**
```sql
-- All authenticated users can READ
CREATE POLICY "authenticated_users_view_chunks"
ON chunks FOR SELECT
USING (auth.role() = 'authenticated');

-- Only admins can INSERT/DELETE
CREATE POLICY "admins_insert_chunks"
ON chunks FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid() AND is_admin = true
    )
);
```

**Storage Bucket:**
```sql
-- All authenticated users can READ files
CREATE POLICY "authenticated_users_read_documents"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'documents'
    AND auth.role() = 'authenticated'
);

-- Only admins can UPLOAD/DELETE files
CREATE POLICY "admins_upload_documents"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'documents'
    AND EXISTS (
        SELECT 1 FROM user_profiles
        WHERE id = auth.uid() AND is_admin = true
    )
);
```

#### Updated Search Function:

```sql
-- Removed user_id filtering from hybrid_search_chunks
-- Now searches ALL chunks regardless of who uploaded them
CREATE OR REPLACE FUNCTION hybrid_search_chunks(...)
...
-- OLD: WHERE c.user_id = p_user_id
-- NEW: No user_id filter (searches all chunks)
```

### 2. Backend Code Updates

**File:** `backend/app/routers/chat.py`

**Before:**
```python
def user_has_documents(user_id: str) -> bool:
    """Check if user has any completed documents for RAG."""
    result = supabase.table("documents").select("id", count="exact").eq(
        "user_id", user_id  # ← Problem: filtered by user
    ).eq("status", "completed").execute()
    return (result.count or 0) > 0

# Only provide tools if user has documents
tools = RAG_TOOLS if user_has_documents(current_user.id) else None
```

**After:**
```python
def system_has_documents() -> bool:
    """Check if system has any completed documents for RAG (shared access model)."""
    supabase = get_supabase_client()
    # Check if ANY documents exist (not filtered by user)
    result = supabase.table("documents").select("id", count="exact").eq(
        "status", "completed"
    ).limit(1).execute()
    return (result.count or 0) > 0

# Only provide tools if system has documents (shared access model)
tools = RAG_TOOLS if system_has_documents() else None
```

**File:** `backend/app/services/retrieval_service.py`

Updated documentation to clarify that `user_id` is now only used for logging, not filtering:

```python
Args:
    query: Search query text
    user_id: User ID for logging/context (not used for filtering)  # ← Updated
    ...
```

---

## How to Apply

### Step 1: Apply Database Migration

```bash
cd supabase
supabase db push
```

This will:
- ✅ Drop old restrictive RLS policies
- ✅ Create new shared access policies
- ✅ Update hybrid_search_chunks function
- ✅ Allow all users to read all documents

### Step 2: Restart Backend

```powershell
powershell -File scripts/restart-backend.ps1
```

This applies the code changes:
- ✅ New `system_has_documents()` function
- ✅ Updated search documentation

### Step 3: Test

**Test as Admin:**
1. Sign in as admin
2. Upload a document (e.g., law file)
3. Wait for processing to complete
4. Ask a question → Should get response ✅

**Test as Regular User:**
1. Sign out admin
2. Sign in as regular user (e.g., test2@test.com)
3. Ask a question about the document admin uploaded
4. Should get response ✅ (this should now work!)

---

## Verification Steps

### 1. Check RLS Policies

```sql
-- Run in Supabase SQL Editor
SELECT schemaname, tablename, policyname, roles, cmd, qual
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN ('documents', 'chunks')
ORDER BY tablename, policyname;
```

**Expected policies:**
- `authenticated_users_view_documents` - SELECT for all users
- `admins_insert_documents` - INSERT for admins only
- `admins_update_documents` - UPDATE for admins only
- `admins_delete_documents` - DELETE for admins only
- `authenticated_users_view_chunks` - SELECT for all users
- `admins_insert_chunks` - INSERT for admins only
- `admins_delete_chunks` - DELETE for admins only

### 2. Test Document Upload (Admin Only)

```bash
# As admin user
curl -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -F "file=@test.txt"

# Expected: Success (200 OK)
```

```bash
# As regular user
curl -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer $USER_TOKEN" \
  -F "file=@test.txt"

# Expected: Error (403 Forbidden) - RLS will block this
```

### 3. Test Document Search (All Users)

```bash
# As regular user - should now work!
curl -X POST http://localhost:8000/threads/$THREAD_ID/messages \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "46-modda"}'

# Expected: Success - gets results from admin's documents
```

---

## Permissions Summary

| Action | Admin | Regular User |
|--------|-------|--------------|
| **Upload documents** | ✅ Yes | ❌ No |
| **View all documents** | ✅ Yes | ✅ Yes |
| **Search all documents** | ✅ Yes | ✅ Yes |
| **Delete documents** | ✅ Yes | ❌ No |
| **Update documents** | ✅ Yes | ❌ No |
| **Chat with RAG** | ✅ Yes | ✅ Yes |

---

## Rollback Plan

If issues occur, revert changes:

### 1. Revert Database Migration

```sql
-- Restore old policies
DROP POLICY IF EXISTS "authenticated_users_view_documents" ON documents;
DROP POLICY IF EXISTS "authenticated_users_view_chunks" ON chunks;

CREATE POLICY "users_own_documents" ON documents
FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "users_own_chunks" ON chunks
FOR ALL USING (auth.uid() = user_id);
```

### 2. Revert Code Changes

```bash
git checkout HEAD~1 -- backend/app/routers/chat.py
git checkout HEAD~1 -- backend/app/services/retrieval_service.py
powershell -File scripts/restart-backend.ps1
```

---

## Benefits of New Architecture

✅ **Single Source of Truth**
- Admin maintains one set of legal documents
- All users get consistent information

✅ **Simplified Management**
- No need to duplicate documents for each user
- Easier to update documents (admin updates once)

✅ **Better Security**
- Clear separation: admins manage, users consume
- RLS enforces permissions at database level

✅ **Scalability**
- Can support many users without duplicating data
- One document ingestion serves all users

---

## Next Steps

After verifying everything works:

1. ✅ Test with multiple user accounts
2. ✅ Verify regular users can query admin's documents
3. ✅ Verify regular users CANNOT upload documents
4. ✅ Test document deletion (admin only)
5. ✅ Update documentation if needed

---

**Status:** ✅ Ready to apply
**Risk Level:** Medium - Database schema and RLS changes
**Testing Required:** Yes - Test both admin and user accounts
**Rollback Available:** Yes - See rollback plan above
