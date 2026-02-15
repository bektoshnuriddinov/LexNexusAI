# Progress

Track your progress through the masterclass. Update this file as you complete modules - Claude Code reads this to understand where you are in the project.

## Convention
- `[ ]` = Not started
- `[-]` = In progress
- `[x]` = Completed

## Modules

### Module 1: App Shell + Observability
- [x] Backend Setup - FastAPI skeleton with health endpoint
- [x] Supabase Client - Backend Supabase client wrapper
- [x] Database Schema - threads and messages tables with RLS
- [x] Auth Middleware - JWT verification and /auth/me endpoint
- [x] Frontend Setup - Vite + React + Tailwind + shadcn/ui
- [x] Frontend Supabase Client
- [x] Auth UI - Sign in/sign up forms
- [x] OpenAI Assistant Service - Responses API integration
- [x] Thread API - CRUD endpoints
- [x] Chat API with SSE - Streaming messages
- [x] Thread List UI
- [x] Chat View UI
- [x] Main App Assembly
- [x] LangSmith Tracing

**Status: COMPLETE ✓**

### Module 2: BYO Retrieval + Provider Abstraction
- [x] Phase 1: Provider Abstraction - ChatCompletions API with configurable base_url/api_key
- [x] Phase 2: Database Schema - pgvector extension, documents/chunks tables, RLS, match_chunks function, storage bucket
- [x] Phase 3: Ingestion Pipeline - embedding_service, chunking_service, ingestion_service, documents router
- [x] Phase 4: Retrieval Tool - retrieval_service, tool_executor, RAG_TOOLS definition, tool-calling loop in chat
- [x] Phase 5: Ingestion UI + Realtime - DocumentsPage, DocumentUpload, DocumentList, useRealtimeDocuments hook

**Status: COMPLETE ✓**

## Validation Summary
- [x] Supabase project linked via CLI (project ref: dkbbhbpluvtimzzyavyg)
- [x] SQL migration applied via `supabase db push`
- [x] Backend venv created and dependencies installed
- [x] Backend server running (health endpoint validated)
- [x] Frontend .env file created
- [x] Frontend npm install completed
- [x] Frontend dev server verified working
- [x] Service startup scripts created (`scripts/start-*.ps1`)
- [x] Playwright MCP configured for browser testing
- [x] Auth flow tested - Sign in/sign up working
- [x] Thread creation and chat tested - Messages streaming correctly
- [x] LangSmith tracing configured (verify traces in LangSmith dashboard)

## Module 2 Validation
- [x] Database migrations applied (pgvector, documents, chunks tables, storage bucket)
- [x] Backend starts with new LLM service (ChatCompletions API)
- [x] Documents page accessible with upload zone and document list
- [x] File upload works (.txt/.md), status updates in real-time via Supabase Realtime
- [x] Ingestion pipeline: upload → chunk → embed → store in pgvector
- [x] RAG retrieval: chat calls search_documents tool, retrieves relevant chunks, cites sources
- [x] Tool-calling loop with max 3 rounds works correctly

### Validation Suite
- [x] Test fixture files created (.agent/validation/fixtures/)
- [x] Full validation suite written (.agent/validation/full-suite.md)
- [x] 36 API tests (curl-based) covering health, auth, threads, chat, documents, settings, errors
- [x] 23 E2E browser tests (Playwright MCP) covering auth, chat, navigation, documents, RAG, isolation
- [x] Cleanup section to reset state after test runs
- [x] CLAUDE.md updated with test suite maintenance instructions for future agents

**Status: COMPLETE**

### Module 3: Admin User Management
- [x] Database Schema - user_profiles table with RLS policies
- [x] Backend Admin API - POST /admin/users, GET /admin/users endpoints
- [x] Auth Update - get_current_user now queries user_profiles for admin status
- [x] Frontend Auth - Removed sign-up toggle, sign-in only
- [x] Admin Page - User management UI at /admin route
- [x] User Menu - Added "User Management" link for admins

**Status: COMPLETE ✓** (Migration needs manual application)

### Module 4: Record Manager (PRD Module 3)
- [x] Database Migration - Add content_hash column and indexes
- [x] Hashing Utility - SHA-256 content hashing function
- [x] Duplicate Detection - Check for exact duplicates before ingestion
- [x] Update Detection - Handle same filename, different content
- [x] Schema Update - Add content_hash to DocumentResponse
- [x] Backfill Script - Script to update existing documents
- [x] Validation Suite Update - Add API-41, API-42, API-43, E2E-28

**Status: COMPLETE ✓** (Migration needs manual application)

### Module 5: Metadata Extraction (PRD Module 4)
- [x] Database Migration - Add metadata JSONB columns and GIN indexes
- [x] Metadata Schema - Define DocumentMetadata Pydantic model
- [x] Extraction Service - LLM-powered structured metadata extraction
- [x] Ingestion Integration - Extract metadata during document processing
- [x] Metadata Inheritance - Chunks inherit metadata from parent document
- [x] Retrieval Enhancement - Update match_chunks to support metadata filters
- [x] Tool Definition Update - Add metadata_filters parameter to search_documents tool
- [x] UI Display - Show metadata badges on document cards
- [x] Backfill Script - Extract metadata for existing documents
- [x] Validation Suite Update - Add API-44, API-45, API-46, E2E-29

**Status: COMPLETE ✓** (Migration needs manual application)

### Module 6: Multi-Format Support (PRD Module 5)
- [x] Install Libraries - pypdf, python-docx, beautifulsoup4, html2text
- [x] Create Extraction Service - Multi-format text extraction functions
- [x] Update File Type Validation - Accept .pdf, .docx, .html files
- [x] Update Ingestion Service - Use new extraction service
- [x] Create Test Fixtures - Sample HTML file (PDF/DOCX need manual creation)
- [x] Verify Cascade Deletes - Ensure chunks deleted with documents
- [x] Add File Type Icons - Visual indicators in UI
- [x] Validation Suite Update - Add API-47, API-48, API-49, API-50, API-51, E2E-30

**Status: COMPLETE ✓** (Manual test file creation pending)

## Module 6 Notes (Multi-Format Support)
- Plan file created: `.agent/plans/9.multi-format-support.md`
- ✅ Libraries installed: pypdf (4.0.1), python-docx (1.1.0), beautifulsoup4 (4.12.3), html2text (2024.2.26)
- ✅ Extraction service created: `backend/app/services/extraction_service.py`
- ✅ Supported formats: PDF, DOCX, HTML (in addition to TXT, MD)
- ✅ File type validation updated: accepts .pdf, .docx, .html, .htm extensions
- ✅ MAX_FILE_SIZE increased to 50 MB for PDFs
- ✅ Ingestion service updated to use new extraction service
- ✅ Migration created: `backend/migrations/004_verify_cascade_deletes.sql`
- ✅ UI file type icons added: 📄 (PDF), 📝 (DOCX), 🌐 (HTML), 📋 (MD)
- ✅ HTML test file created: `.agent/validation/fixtures/test_document.html`
- ✅ Validation suite updated: Added API-47, API-48, API-49, API-50, API-51, E2E-30 (total: 81 tests)
- ⚠️ PDF and DOCX test files need manual creation (instructions in CREATE_TEST_FILES.md)
- Edge cases handled: scanned PDFs, corrupt files, password-protected PDFs, empty files
- HTML extraction converts to Markdown (preserves structure)

### Module 7: Hybrid Search & Reranking (PRD Module 6)
- [x] Add Full-Text Search to Database Schema - tsvector column, GIN index, keyword_search_chunks function
- [x] Create Hybrid Search Function with RRF - Combine vector + keyword search with Reciprocal Rank Fusion
- [x] Add Reranker Service - Jina AI API integration for cross-encoder reranking
- [x] Update Retrieval Service for Hybrid Search - Use hybrid_search_chunks RPC with reranking
- [x] Update Global Settings for Reranker - Add Jina API key and reranker config to settings
- [x] Update RAG Tool Definition - Update search_documents tool description for hybrid search
- [x] Add Comparison Tests to Validation Suite - Add API-52, API-53, API-54, API-55, E2E-31
- [x] Update PROGRESS.md and Documentation

**Status: COMPLETE ✓** (Migration needs manual application)

## Module 7 Notes (Hybrid Search & Reranking)
- Plan file created: `.agent/plans/10.hybrid-search-reranking.md`
- ✅ Migration created: `backend/migrations/005_add_fulltext_search.sql` and `supabase/migrations/20260214210000_add_fulltext_search.sql`
- ⚠️ **Action Required:** Apply migration using Supabase CLI: `supabase db push`
- ⚠️ **Action Required:** Sign up for Jina AI API (free tier): https://jina.ai/reranker
- ⚠️ **Action Required:** Configure Jina API key in Settings UI after reranking is enabled
- ✅ Full-text search: PostgreSQL tsvector with GIN index for fast keyword matching
- ✅ Hybrid search function: `hybrid_search_chunks` combines vector + keyword with RRF algorithm
- ✅ RRF (Reciprocal Rank Fusion): k=60, merges rankings from both search methods
- ✅ Reranker service: `backend/app/services/reranker_service.py` using Jina AI API
- ✅ Reranker settings: Added jina_api_key, jina_rerank_model, jina_rerank_enabled to global_settings
- ✅ Retrieval service updated: Now uses hybrid_search_chunks RPC instead of match_chunks
- ✅ Settings UI updated: Reranker configuration section added to admin settings
- ✅ RAG tool description updated: Mentions hybrid search and reranking capabilities
- ✅ Validation suite updated: Added API-52, API-53, API-54, API-55, E2E-31 (total: 86 tests)
- ✅ Test fixture created: `.agent/validation/fixtures/hybrid_search_test.txt` (FastAPI configuration guide)
- Benefits: Better handling of technical terms, acronyms, exact matches, semantic understanding
- Cost: Jina free tier 10k rerank calls/month (1 call per chat message)
- Performance: Hybrid search is slightly slower than vector-only but more accurate
- Fallback: Reranking gracefully falls back to RRF-only if API fails or is disabled

## Module 5 Notes (Metadata Extraction)
- Migration file created: `backend/migrations/003_add_metadata.sql` and `supabase/migrations/20260214200109_add_metadata.sql`
- ⚠️ **Action Required:** Apply migration using Supabase CLI: `supabase db push`
- ⚠️ **Action Required:** Verify global LLM settings are configured for metadata extraction
- Metadata schema: DocumentMetadata with 8 fields (document_type, topics, languages, frameworks, date_references, entities, summary, technical_level)
- Uses OpenAI structured outputs via `beta.chat.completions.parse`
- Extracts metadata from first 8000 characters (cost optimization)
- JSONB storage with GIN indexes for fast filtering
- match_chunks function updated to support metadata_filters parameter
- RAG tool enhanced with metadata filter examples and documentation
- UI displays color-coded metadata badges (blue=type, green=topics, purple=languages, orange=tools)
- Backfill script: `backend/app/scripts/backfill_metadata.py`
- Validation suite updated: 3 new API tests, 1 new E2E test (total: 75 tests)
- Cost: ~$0.002 per document with 8000 char truncation

## Module 4 Notes (Record Manager)
- Migration file created: `backend/migrations/002_add_content_hash.sql`
- ⚠️ **Action Required:** Apply migration using Supabase CLI: `supabase db push`
- Content hashing implemented using SHA-256
- Deduplication logic: exact duplicate returns existing document (no re-processing)
- Update detection: same filename + different content → deletes old chunks, re-processes
- Backfill script created at `backend/app/scripts/backfill_hashes.py`
- Validation suite updated: 3 new API tests, 1 new E2E test (total: 71 tests)

## Module 3 Notes (Admin User Management)
- Migration file created: `supabase/migrations/20260214175926_add_user_profiles.sql`
- ⚠️ **Action Required:** Apply migration using Supabase CLI: `supabase db push`
- ⚠️ **Action Required:** Verify SUPABASE_SERVICE_ROLE_KEY is in backend/.env
- email-validator package installed for EmailStr validation
- Public sign-up is now disabled - only admins can create users
- Admin detection moved from hardcoded email to database field

## Notes
- Test user created: test@test.com (see CLAUDE.md for credentials)
- Migration updated to use `gen_random_uuid()` instead of `uuid_generate_v4()`
- All core Module 1 functionality validated and working

## Service URLs
- **Frontend:** http://localhost:5173
- **Backend:** http://localhost:8000
- **Backend Health:** http://localhost:8000/health

## Windows/MINGW Notes
- npm commands produce no output in MINGW/Git Bash
- Always use PowerShell for npm and service commands
- See `scripts/` folder for ready-to-use startup scripts
- CLAUDE.md has been updated with service startup instructions
