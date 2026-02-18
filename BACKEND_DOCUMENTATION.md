# RAG Masterclass Backend Documentation

Complete technical documentation for the RAG Masterclass backend system.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [API Endpoints](#api-endpoints)
4. [Data Models (Pydantic Schemas)](#data-models-pydantic-schemas)
5. [Services](#services)
6. [Document Upload Process](#document-upload-process)
7. [Chat Process](#chat-process)
8. [Database Schema](#database-schema)
9. [Configuration](#configuration)
10. [Authentication & Authorization](#authentication--authorization)

---

## System Overview

**Purpose**: A Retrieval-Augmented Generation (RAG) system for legal document Q&A.

**Key Features**:
- Multi-format document ingestion (PDF, DOCX, TXT, MD, HTML)
- Hybrid search (vector + keyword) with reranking
- Real-time chat with streaming responses
- Multi-tenant with admin controls
- LLM/Embedding provider abstraction via global settings

**Tech Stack**:
- **Framework**: FastAPI (Python)
- **Database**: Supabase (Postgres + pgvector)
- **LLM**: OpenAI-compatible APIs (OpenAI, OpenRouter)
- **Embeddings**: OpenAI-compatible embedding APIs
- **Reranking**: Jina AI Reranker API (optional)
- **Observability**: LangSmith

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                       │
├─────────────────────────────────────────────────────────────────┤
│  Routers (API Endpoints)                                         │
│  ├─ auth.py          - User authentication & profile             │
│  ├─ threads.py       - Thread CRUD operations                    │
│  ├─ chat.py          - Chat messages & streaming                 │
│  ├─ documents.py     - Document upload & management              │
│  ├─ settings.py      - Global LLM/embedding settings             │
│  └─ admin.py         - Admin user management                     │
├─────────────────────────────────────────────────────────────────┤
│  Services (Business Logic)                                       │
│  ├─ ingestion_service.py    - Document processing orchestration  │
│  ├─ extraction_service.py   - Multi-format text extraction       │
│  ├─ chunking_service.py     - Text splitting                     │
│  ├─ metadata_service.py     - LLM-based metadata extraction      │
│  ├─ embedding_service.py    - Embedding generation               │
│  ├─ llm_service.py          - Chat completions & streaming       │
│  ├─ retrieval_service.py    - Hybrid search (vector + keyword)   │
│  ├─ reranker_service.py     - Cross-encoder reranking            │
│  └─ tool_executor.py        - LLM tool call execution            │
├─────────────────────────────────────────────────────────────────┤
│  Models                                                          │
│  └─ schemas.py       - Pydantic models for request/response      │
├─────────────────────────────────────────────────────────────────┤
│  Database Layer                                                  │
│  └─ supabase.py      - Supabase client initialization            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Supabase (PostgreSQL + pgvector)              │
│  Tables: threads, messages, documents, chunks,                   │
│          user_profiles, global_settings                          │
│  Functions: hybrid_search_chunks, keyword_search_chunks,         │
│             match_chunks                                         │
│  Storage: documents bucket (file storage)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### Base URL
```
http://localhost:8000
```

### Authentication
All endpoints (except `/health`) require Bearer token authentication:
```
Authorization: Bearer <supabase_jwt_token>
```

---

### 1. Health Check

#### `GET /health`
**Purpose**: Check if the API is running.

**Authentication**: None required

**Response**:
```json
{
  "status": "ok"
}
```

---

### 2. Authentication Endpoints

#### `GET /auth/me`
**Purpose**: Get current authenticated user's information.

**Authentication**: Required

**Response**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "is_admin": false
}
```

**Models Used**:
- Response: `User` (from dependencies.py)

---

### 3. Thread Endpoints

#### `GET /threads`
**Purpose**: List all threads for the current user.

**Authentication**: Required

**Response**: `list[ThreadResponse]`
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "title": "New Chat",
    "created_at": "2026-02-17T10:00:00Z",
    "updated_at": "2026-02-17T10:00:00Z"
  }
]
```

**Models Used**:
- Response: `ThreadResponse` (schemas.py)

---

#### `POST /threads`
**Purpose**: Create a new thread.

**Authentication**: Required

**Request Body**: `ThreadCreate`
```json
{
  "title": "My New Chat"  // optional, defaults to "New Chat"
}
```

**Response**: `ThreadResponse` (same as above)

**Models Used**:
- Request: `ThreadCreate` (schemas.py)
- Response: `ThreadResponse` (schemas.py)

---

#### `GET /threads/{thread_id}`
**Purpose**: Get a specific thread.

**Authentication**: Required

**Path Parameters**:
- `thread_id` (uuid) - The thread ID

**Response**: `ThreadResponse`

**Models Used**:
- Response: `ThreadResponse` (schemas.py)

---

#### `PATCH /threads/{thread_id}`
**Purpose**: Update a thread's title.

**Authentication**: Required

**Path Parameters**:
- `thread_id` (uuid) - The thread ID

**Request Body**: `ThreadUpdate`
```json
{
  "title": "Updated Title"
}
```

**Response**: `ThreadResponse`

**Models Used**:
- Request: `ThreadUpdate` (schemas.py)
- Response: `ThreadResponse` (schemas.py)

---

#### `DELETE /threads/{thread_id}`
**Purpose**: Delete a thread and all its messages (cascade).

**Authentication**: Required

**Path Parameters**:
- `thread_id` (uuid) - The thread ID

**Response**: 204 No Content

---

### 4. Chat Endpoints

#### `GET /threads/{thread_id}/messages`
**Purpose**: Get all messages in a thread.

**Authentication**: Required

**Path Parameters**:
- `thread_id` (uuid) - The thread ID

**Response**: `list[MessageResponse]`
```json
[
  {
    "id": "uuid",
    "thread_id": "uuid",
    "user_id": "uuid",
    "role": "user",
    "content": "What is Article 46?",
    "created_at": "2026-02-17T10:00:00Z"
  },
  {
    "id": "uuid",
    "thread_id": "uuid",
    "user_id": "uuid",
    "role": "assistant",
    "content": "Article 46 states...",
    "created_at": "2026-02-17T10:00:05Z"
  }
]
```

**Models Used**:
- Response: `list[MessageResponse]` (schemas.py)

---

#### `POST /threads/{thread_id}/messages`
**Purpose**: Send a message and receive streamed assistant response.

**Authentication**: Required

**Path Parameters**:
- `thread_id` (uuid) - The thread ID

**Request Body**: `MessageCreate`
```json
{
  "content": "What is Article 46 about?"
}
```

**Response**: Server-Sent Events (SSE) stream

**SSE Event Types**:
1. `text_delta` - Streaming text chunks
   ```
   event: text_delta
   data: {"content": "Article 46"}
   ```

2. `done` - Response complete
   ```
   event: done
   data: {}
   ```

3. `error` - Error occurred
   ```
   event: error
   data: {"error": "Error message"}
   ```

**Models Used**:
- Request: `MessageCreate` (schemas.py)
- Response: SSE stream

**Process**:
1. User message stored in database
2. Full conversation history loaded
3. LLM streaming response generated (with tool calling)
4. Assistant message stored when complete
5. Thread `updated_at` timestamp updated

---

### 5. Document Endpoints

#### `POST /documents/upload`
**Purpose**: Upload a document for ingestion (admin only).

**Authentication**: Admin required

**Request**: `multipart/form-data`
- `file` (UploadFile) - The document file

**Supported File Types**:
- `.txt` - Plain text
- `.md` - Markdown
- `.pdf` - PDF documents
- `.docx` - Microsoft Word
- `.html`, `.htm` - HTML files

**File Size Limit**: 50 MB

**Response**: `DocumentResponse`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "filename": "document.pdf",
  "file_type": "application/pdf",
  "file_size": 1024000,
  "storage_path": "user-id/file-id.pdf",
  "status": "processing",
  "error_message": null,
  "chunk_count": 0,
  "content_hash": "sha256-hash",
  "metadata": {
    "document_type": "documentation",
    "topics": ["legal", "procurement"],
    "summary": "Document about procurement law"
  },
  "created_at": "2026-02-17T10:00:00Z",
  "updated_at": "2026-02-17T10:00:00Z"
}
```

**Status Values**:
- `pending` - Awaiting processing
- `processing` - Currently being processed
- `completed` - Successfully processed
- `failed` - Processing failed (see `error_message`)

**Models Used**:
- Response: `DocumentResponse` (schemas.py)

**Deduplication**:
- Exact duplicate (same content hash): Returns existing document
- Same filename, different content: Updates existing document

---

#### `GET /documents`
**Purpose**: List all documents for the current user.

**Authentication**: Required

**Response**: `list[DocumentResponse]`

**Models Used**:
- Response: `list[DocumentResponse]` (schemas.py)

---

#### `DELETE /documents/{document_id}`
**Purpose**: Delete a document and its storage file (admin only).

**Authentication**: Admin required

**Path Parameters**:
- `document_id` (uuid) - The document ID

**Response**:
```json
{
  "status": "deleted"
}
```

**Note**: Chunks are cascade-deleted automatically via foreign key.

---

### 6. Settings Endpoints

#### `GET /settings`
**Purpose**: Get global LLM and embedding settings (masked API keys).

**Authentication**: Required

**Response**: `GlobalSettingsResponse`
```json
{
  "llm_model": "gpt-4o",
  "llm_base_url": "https://api.openai.com/v1",
  "llm_api_key": "***xyz1",
  "embedding_model": "text-embedding-3-small",
  "embedding_base_url": "https://api.openai.com/v1",
  "embedding_api_key": "***abc2",
  "embedding_dimensions": 1536,
  "has_chunks": true,
  "jina_api_key": "***def3",
  "jina_rerank_model": "jina-reranker-v2-base-multilingual",
  "jina_rerank_enabled": true
}
```

**Models Used**:
- Response: `GlobalSettingsResponse` (settings.py)

---

#### `PUT /settings`
**Purpose**: Update global settings (admin only).

**Authentication**: Admin required

**Request Body**: `GlobalSettingsUpdate`
```json
{
  "llm_model": "gpt-4o",
  "llm_base_url": "https://openrouter.ai/api/v1",
  "llm_api_key": "sk-...",
  "embedding_model": "text-embedding-3-small",
  "embedding_base_url": null,
  "embedding_api_key": "sk-...",
  "embedding_dimensions": 1536,
  "jina_api_key": "jina_...",
  "jina_rerank_model": "jina-reranker-v2-base-multilingual",
  "jina_rerank_enabled": true
}
```

**Response**: `GlobalSettingsResponse` (same as GET)

**Important Notes**:
- API keys are encrypted before storage
- Masked values (e.g., `***xyz1`) are ignored during update
- Embedding settings cannot be changed if chunks exist
- All fields are optional

**Models Used**:
- Request: `GlobalSettingsUpdate` (settings.py)
- Response: `GlobalSettingsResponse` (settings.py)

---

### 7. Admin Endpoints

#### `POST /admin/users`
**Purpose**: Create a new user (admin only).

**Authentication**: Admin required

**Request Body**: `CreateUserRequest`
```json
{
  "email": "newuser@example.com",
  "password": "secure-password",
  "is_admin": false
}
```

**Response**: `UserResponse`
```json
{
  "id": "uuid",
  "email": "newuser@example.com",
  "is_admin": false,
  "created_at": "2026-02-17T10:00:00Z"
}
```

**Models Used**:
- Request: `CreateUserRequest` (admin.py)
- Response: `UserResponse` (admin.py)

---

#### `GET /admin/users`
**Purpose**: List all users (admin only).

**Authentication**: Admin required

**Response**: `list[UserResponse]`

**Models Used**:
- Response: `list[UserResponse]` (admin.py)

---

#### `PATCH /admin/users/{user_id}/admin`
**Purpose**: Toggle admin status for a user (admin only).

**Authentication**: Admin required

**Path Parameters**:
- `user_id` (uuid) - The user ID

**Request Body**: `ToggleAdminRequest`
```json
{
  "is_admin": true
}
```

**Response**: `UserResponse`

**Models Used**:
- Request: `ToggleAdminRequest` (admin.py)
- Response: `UserResponse` (admin.py)

---

## Data Models (Pydantic Schemas)

All models are defined in `backend/app/models/schemas.py`.

### DocumentMetadata
**Purpose**: Structured metadata extracted from document content via LLM.

**Fields**:
```python
document_type: Literal[
    "tutorial", "guide", "reference", "blog_post",
    "research_paper", "documentation", "report", "other"
]

topics: list[str]  # Max 5 main topics

programming_languages: list[str]  # Languages mentioned

frameworks_tools: list[str]  # Max 5 frameworks/tools

date_references: str | None  # Time period mentioned

key_entities: list[str]  # Max 5 people/companies/orgs

summary: str  # One-sentence summary (max 200 chars)

technical_level: Literal["beginner", "intermediate", "advanced", "expert"]
```

**Usage**: Stored in `documents.metadata` JSONB column, inherited by chunks.

---

### ThreadCreate
**Purpose**: Request body for creating a new thread.

**Fields**:
```python
title: str | None = "New Chat"
```

---

### ThreadResponse
**Purpose**: Response body for thread operations.

**Fields**:
```python
id: str  # UUID
user_id: str  # UUID
title: str
created_at: datetime
updated_at: datetime
```

---

### ThreadUpdate
**Purpose**: Request body for updating thread title.

**Fields**:
```python
title: str
```

---

### MessageCreate
**Purpose**: Request body for sending a message.

**Fields**:
```python
content: str  # The message text
```

---

### MessageResponse
**Purpose**: Response body for message operations.

**Fields**:
```python
id: str  # UUID
thread_id: str  # UUID
user_id: str  # UUID
role: str  # "user" or "assistant"
content: str  # Message text
created_at: datetime
```

---

### DocumentResponse
**Purpose**: Response body for document operations.

**Fields**:
```python
id: str  # UUID
user_id: str  # UUID
filename: str
file_type: str  # MIME type
file_size: int  # Bytes
storage_path: str  # Supabase storage path
status: str  # "pending", "processing", "completed", "failed"
error_message: str | None
chunk_count: int  # Number of chunks created
content_hash: str | None  # SHA-256 hash
metadata: dict | None  # DocumentMetadata as dict
created_at: datetime
updated_at: datetime
```

---

## Services

Services contain the business logic for document processing, LLM calls, and search.

### 1. ingestion_service.py

**Purpose**: Orchestrates the document ingestion pipeline.

#### Functions

##### `hash_file_content(file_bytes: bytes) -> str`
**Purpose**: Calculate SHA-256 hash for deduplication.

**Parameters**:
- `file_bytes` - Raw file content

**Returns**: Hex-encoded SHA-256 hash

**Usage**: Called during upload to detect duplicate files.

---

##### `async process_document(document_id: str, user_id: str) -> None`
**Purpose**: Background task that processes an uploaded document.

**Parameters**:
- `document_id` - Document UUID
- `user_id` - User UUID

**Process**:
1. Update status to "processing"
2. Download file from Supabase Storage
3. Extract text (calls `extraction_service.extract_text`)
4. Extract metadata (calls `metadata_service.extract_metadata`)
5. Chunk text (calls `chunking_service.chunk_text`)
6. Generate embeddings in batches (calls `embedding_service.get_embeddings`)
7. Store chunks with embeddings in database
8. Update document status to "completed"

**Error Handling**: On failure, sets status to "failed" and stores error message.

**Batch Size**: 50 chunks per embedding batch.

---

### 2. extraction_service.py

**Purpose**: Extract text from various file formats.

#### Functions

##### `normalize_text(text: str) -> str`
**Purpose**: Normalize legal document notation (superscripts).

**Example**:
```
Input:  "497²⁶"
Output: "497²⁶ (497-26)"
```

**Purpose**: Preserves original formatting while adding searchable version.

---

##### `extract_text_from_pdf(file_bytes: bytes) -> str`
**Purpose**: Extract text from PDF files.

**Library**: `pypdf.PdfReader`

**Process**:
1. Parse PDF
2. Extract text from each page
3. Join pages with double newlines
4. Normalize superscripts

**Raises**: `ValueError` if extraction fails or PDF is empty/scanned.

---

##### `extract_text_from_docx(file_bytes: bytes) -> str`
**Purpose**: Extract text from DOCX files.

**Library**: `python-docx.Document`

**Process**:
1. Parse DOCX
2. Extract text from paragraphs
3. Extract text from tables
4. Join with double newlines
5. Normalize superscripts

**Raises**: `ValueError` if extraction fails or DOCX is empty.

---

##### `extract_text_from_html(file_bytes: bytes) -> str`
**Purpose**: Extract text from HTML files.

**Libraries**:
- `html2text` - HTML to Markdown conversion
- `BeautifulSoup` - Fallback plain text extraction

**Process**:
1. Decode HTML (UTF-8 with error handling)
2. Convert to Markdown (preserves structure)
3. If empty, fallback to BeautifulSoup plain text
4. Normalize superscripts

**Raises**: `ValueError` if extraction fails or HTML is empty.

---

##### `extract_text(file_bytes: bytes, file_type: str) -> str`
**Purpose**: Main dispatcher for text extraction.

**Parameters**:
- `file_bytes` - Raw file content
- `file_type` - MIME type

**Supported Types**:
- `text/plain` - Direct UTF-8 decode
- `text/markdown` - Direct UTF-8 decode
- `application/pdf` - Calls `extract_text_from_pdf`
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document` - Calls `extract_text_from_docx`
- `text/html` - Calls `extract_text_from_html`

**Returns**: Extracted text

**Raises**: `ValueError` for unsupported types or extraction failures.

---

### 3. chunking_service.py

**Purpose**: Split text into overlapping chunks.

#### Functions

##### `chunk_text(text: str, chunk_size: int = 5000, chunk_overlap: int = 1000, separators: list[str] | None = None) -> list[str]`
**Purpose**: Recursive character text splitter.

**Parameters**:
- `text` - Text to split
- `chunk_size` - Max characters per chunk (default 5000)
- `chunk_overlap` - Overlap between chunks (default 1000)
- `separators` - Separators to try in order (default: `["\n\n", "\n", ". ", " "]`)

**Algorithm**:
1. If text ≤ chunk_size, return as single chunk
2. Find best separator (first one that appears in text)
3. Split text by separator
4. Merge splits into chunks ≤ chunk_size
5. Add overlap from previous chunk to next chunk
6. Recursively split any chunks still > chunk_size

**Returns**: List of text chunks

**Purpose**: Keeps related content together while ensuring search overlap.

---

### 4. metadata_service.py

**Purpose**: Extract structured metadata from documents using LLM.

#### Functions

##### `async extract_metadata(text_content: str, filename: str) -> DocumentMetadata`
**Purpose**: Use LLM to extract metadata from document.

**Parameters**:
- `text_content` - Full document text (truncated to 8000 chars)
- `filename` - Original filename

**Process**:
1. Get LLM settings from `global_settings` table
2. Decrypt API key
3. Create OpenAI client
4. Truncate content to 8000 chars for cost optimization
5. Call LLM with structured output (Pydantic schema)
6. Parse response into `DocumentMetadata`

**LLM Model**: Uses `global_settings.llm_model`

**Prompt**: Asks LLM to identify document type, topics, languages, frameworks, dates, entities, summary, and technical level.

**Fallback**: On error, returns default metadata with document type "other".

**Returns**: `DocumentMetadata` object

---

### 5. embedding_service.py

**Purpose**: Generate embeddings using configured provider.

#### Functions

##### `get_global_embedding_settings() -> dict[str, Any]`
**Purpose**: Get embedding configuration from database or environment.

**Process**:
1. Query `global_settings` table
2. Decrypt API key
3. Fall back to environment variables if not configured
4. Raise HTTPException(503) if no API key

**Returns**:
```python
{
    "model": "text-embedding-3-small",
    "base_url": "https://api.openai.com/v1",  # or None
    "api_key": "sk-...",
    "dimensions": 1536
}
```

---

##### `async get_embeddings(texts: list[str], user_id: str | None = None) -> list[list[float]]`
**Purpose**: Generate embeddings for a list of texts.

**Parameters**:
- `texts` - List of strings to embed
- `user_id` - (Unused, kept for compatibility)

**Process**:
1. Get embedding settings
2. Create traced OpenAI client (LangSmith tracing)
3. Call embeddings API
4. Extract embedding vectors

**Returns**: List of embedding vectors (each is `list[float]`)

**Provider Support**: Any OpenAI-compatible embedding API.

---

### 6. llm_service.py

**Purpose**: Chat completions with streaming and tool calling.

#### Constants

##### `SYSTEM_PROMPT`
**Purpose**: Detailed instructions for the legal assistant LLM.

**Key Instructions**:
- Handle multiple sources intelligently
- Always cite sources
- Examine all chunks carefully
- Copy everything exactly (preserve superscripts!)
- Generate long, complete responses (500-3000+ words)
- Detect incomplete articles and combine chunks
- Ask for clarification on ambiguous queries
- Use `search_documents` tool for retrieval

---

##### `RAG_TOOLS`
**Purpose**: Tool definition for function calling.

**Tool**: `search_documents`

**Parameters**:
- `query` (string, required) - Search query
- `metadata_filters` (object, optional) - JSONB filters
  - `document_type`
  - `topics`
  - `programming_languages`
  - `frameworks_tools`
  - `technical_level`

**Description**: Searches documents using hybrid search, returns top 20 chunks.

---

#### Functions

##### `get_global_llm_settings() -> dict[str, Any]`
**Purpose**: Get LLM configuration from database or environment.

**Process**:
1. Query `global_settings` table
2. Decrypt API key
3. Fall back to environment variables if not configured
4. Raise HTTPException(503) if no API key

**Returns**:
```python
{
    "model": "gpt-4o",
    "base_url": "https://api.openai.com/v1",  # or None
    "api_key": "sk-..."
}
```

---

##### `async astream_chat_response(messages: list[dict], tools: list[dict] | None = None, user_id: str | None = None) -> AsyncGenerator[dict[str, Any], None]`
**Purpose**: Stream chat response with tool calling support.

**Parameters**:
- `messages` - List of message dicts (`{"role": "user|assistant|tool", "content": "..."}`)
- `tools` - Optional tool definitions (e.g., `RAG_TOOLS`)
- `user_id` - (Unused, kept for compatibility)

**Process**:
1. Get LLM settings
2. Create traced OpenAI client
3. Call streaming chat completions API
   - Model: from settings
   - Messages: `[system_prompt, *messages]`
   - Stream: `True`
   - Max tokens: 16000
   - Temperature: 0.0 (for exact copying)
4. Stream response chunks

**Event Types Yielded**:
1. `{"type": "text_delta", "content": "chunk"}` - Text chunk
2. `{"type": "tool_calls", "tool_calls": [...]}` - Tool calls requested
3. `{"type": "response_completed", "content": "full_response"}` - Done
4. `{"type": "error", "error": "message"}` - Error

**Provider Support**: Any OpenAI-compatible chat API.

---

### 7. retrieval_service.py

**Purpose**: Hybrid search combining vector and keyword search.

#### Functions

##### `normalize_query(query: str) -> str`
**Purpose**: Normalize query text to handle variations.

**Normalization**:
1. Convert superscripts to regular numbers: `509⁶` → `509 6`
2. Replace all apostrophe variants with standard `'`
3. Clean up extra whitespace

**Purpose**: Improves search matching for Uzbek text and legal notation.

---

##### `async search_documents(query: str, user_id: str, top_k: int = 20, threshold: float = 0.0, metadata_filters: dict | None = None, use_reranking: bool = True) -> list[dict]`
**Purpose**: Main search function using hybrid search + reranking.

**Parameters**:
- `query` - Search query text
- `user_id` - User ID (for logging, NOT filtering - all users see all docs)
- `top_k` - Number of final results (default 20)
- `threshold` - Minimum vector similarity (default 0.0)
- `metadata_filters` - Optional JSONB filters
- `use_reranking` - Whether to apply reranking (default True)

**Process**:
1. Normalize query
2. Generate embeddings for normalized query
3. Call `hybrid_search_chunks` RPC function
   - Combines vector search (pgvector)
   - Keyword search (PostgreSQL full-text search)
   - Reciprocal Rank Fusion (RRF) to merge results
4. If reranking enabled, call `rerank_chunks`
5. Normalize scores (use `rerank_score` or `rrf_score` as `similarity`)
6. Return top_k results

**Returns**: List of chunks with scores
```python
[
    {
        "id": "uuid",
        "document_id": "uuid",
        "content": "Article 46...",
        "chunk_index": 0,
        "metadata": {...},
        "similarity": 0.95  # rerank_score or rrf_score
    }
]
```

**Database Function Called**: `hybrid_search_chunks` (PostgreSQL)

---

### 8. reranker_service.py

**Purpose**: Cross-encoder reranking using Jina AI API.

#### Functions

##### `async rerank_chunks(query: str, chunks: List[dict], top_n: int = 5) -> List[dict]`
**Purpose**: Rerank search results using cross-encoder model.

**Parameters**:
- `query` - User query
- `chunks` - List of chunks from hybrid search (must have `content` field)
- `top_n` - Number of results to return

**Process**:
1. Check if reranking is enabled (`JINA_RERANK_ENABLED` env var)
2. Extract text content from chunks
3. Call Jina AI Reranker API
   - Endpoint: `https://api.jina.ai/v1/rerank`
   - Model: `jina-reranker-v2-base-multilingual`
4. Map reranked results back to original chunks
5. Add `rerank_score` field

**Returns**: Reranked chunks with scores

**Fallback**: On API error, returns original RRF ranking.

**Environment Variables**:
- `JINA_API_KEY` - Jina AI API key
- `JINA_RERANK_MODEL` - Model name (default: `jina-reranker-v2-base-multilingual`)
- `JINA_RERANK_ENABLED` - "true" or "false"

---

### 9. tool_executor.py

**Purpose**: Execute LLM tool calls (currently only `search_documents`).

#### Functions

##### `async execute_tool_call(tool_call: dict, user_id: str) -> str`
**Purpose**: Execute a tool and return result as string.

**Parameters**:
- `tool_call` - Dict with `{"name": "search_documents", "arguments": "{...}"}`
- `user_id` - User ID

**Process**:
1. Parse tool name and arguments
2. If `search_documents`:
   - Call `retrieval_service.search_documents`
   - Format results with source tags
   - Return formatted string
3. Otherwise, return error

**Result Format**:
```
[Source: filename.pdf] (similarity: 0.95)
Article 46 content...

---

[Source: filename.pdf] (similarity: 0.92)
More Article 46 content...
```

**Returns**: Formatted search results as string for LLM context.

---

## Document Upload Process

**Endpoint**: `POST /documents/upload`

**Step-by-Step Flow**:

### Step 1: Upload & Validation (documents.py router)
```
1. User uploads file via multipart/form-data
2. Validate file extension (.txt, .md, .pdf, .docx, .html)
3. Read file content into memory
4. Validate file size (max 50 MB)
5. Validate file is not empty
6. Calculate SHA-256 content hash
7. Determine MIME type from extension
```

### Step 2: Deduplication Check
```
8. Query database for existing document with same content_hash
   - If found: Return existing document (no processing)
9. Query database for document with same filename
   - If found AND content changed:
     a. Delete old chunks
     b. Delete old file from storage
     c. Re-use document ID and storage path
   - If found AND content same: Return existing document
```

### Step 3: Storage Upload
```
10. If new file:
    a. Generate UUID for file
    b. Create storage path: {user_id}/{file_id}.{ext}
    c. Upload to Supabase Storage "documents" bucket
11. If updating:
    a. Use existing storage path
    b. Upload new content to same path
```

### Step 4: Database Record
```
12. If new:
    a. Insert document record with status "pending"
13. If updating:
    a. Update document record with new hash, status "processing"
```

### Step 5: Background Processing (ingestion_service.py)
```
14. Add background task: process_document(document_id, user_id)
15. Return document response immediately (status "processing")
```

**Background Task Process**:

### Step 6: Download
```
16. Update document status to "processing"
17. Download file from Supabase Storage
```

### Step 7: Text Extraction (extraction_service.py)
```
18. Call extract_text(file_bytes, file_type)
    - PDF: pypdf.PdfReader
    - DOCX: python-docx.Document
    - HTML: html2text + BeautifulSoup
    - TXT/MD: UTF-8 decode
19. Normalize superscripts: 497²⁶ → "497²⁶ (497-26)"
20. Validate text is not empty
```

### Step 8: Metadata Extraction (metadata_service.py)
```
21. Call extract_metadata(text, filename)
22. Truncate text to 8000 chars
23. Get LLM settings from global_settings
24. Call LLM with structured output prompt
25. Parse DocumentMetadata:
    - document_type
    - topics
    - programming_languages
    - frameworks_tools
    - date_references
    - key_entities
    - summary
    - technical_level
26. Store metadata in documents table
```

### Step 9: Chunking (chunking_service.py)
```
27. Call chunk_text(text, chunk_size=5000, chunk_overlap=1000)
28. Recursive character splitting:
    a. Try separators: ["\n\n", "\n", ". ", " "]
    b. Split text
    c. Merge splits into chunks ≤ 5000 chars
    d. Add 1000 char overlap
29. Validate chunks are not empty
```

### Step 10: Embedding Generation (embedding_service.py)
```
30. Process chunks in batches of 50
31. For each batch:
    a. Get embedding settings from global_settings
    b. Create OpenAI client (with LangSmith tracing)
    c. Call embeddings.create(texts=batch)
    d. Extract embedding vectors (1536 dimensions)
```

### Step 11: Chunk Storage
```
32. For each chunk:
    a. Create chunk record:
       - document_id
       - user_id
       - content (text)
       - chunk_index (position in document)
       - embedding (vector)
       - metadata (inherits from document + adds chunk_index, filename)
    b. Insert into chunks table
33. Update chunk_count on document
```

### Step 12: Completion
```
34. Update document status to "completed"
35. Supabase Realtime broadcasts status change to frontend
```

### Error Handling
```
If any step fails:
- Update document status to "failed"
- Store error message in documents.error_message
- Broadcast to frontend via Realtime
```

**Database Tables Involved**:
- `documents` - Document metadata and status
- `chunks` - Text chunks with embeddings
- `storage.objects` - File storage
- `global_settings` - LLM/embedding configuration

**External APIs Called**:
- Embedding API (OpenAI-compatible)
- LLM API (for metadata extraction)
- LangSmith (tracing)

---

## Chat Process

**Endpoint**: `POST /threads/{thread_id}/messages`

**Step-by-Step Flow**:

### Step 1: Verify Access (chat.py router)
```
1. Verify user owns the thread
2. If not found, return 404
```

### Step 2: Store User Message
```
3. Insert user message into messages table:
   - thread_id
   - user_id
   - role: "user"
   - content: user's question
   - created_at: now()
```

### Step 3: Load Conversation History
```
4. Query all messages for thread, ordered by created_at
5. Format as list of {"role": "user|assistant", "content": "..."}
```

### Step 4: Check for Documents
```
6. Query documents table: count completed documents
7. If count > 0:
   - tools = RAG_TOOLS (enable search_documents)
8. Else:
   - tools = None (no retrieval)
```

### Step 5: Start Streaming Response (llm_service.py)
```
9. Create Server-Sent Events (SSE) generator
10. Initialize tool calling loop (max 3 rounds)
```

### Step 6: LLM Request
```
11. Get LLM settings from global_settings
12. Create traced OpenAI client (LangSmith)
13. Call chat.completions.create:
    - model: from settings
    - messages: [system_prompt, *conversation_history]
    - stream: True
    - max_completion_tokens: 16000
    - temperature: 0.0
    - tools: RAG_TOOLS (if documents exist)
```

### Step 7: Stream Response
```
14. For each chunk in stream:
    a. If text delta:
       - Append to full_response
       - Yield SSE event: {"type": "text_delta", "content": "chunk"}

    b. If tool_calls:
       - Buffer tool call fragments
       - When complete:
         * Add assistant message with tool_calls to history
         * Jump to Step 8 (Tool Execution)

    c. If finish_reason == "stop":
       - Jump to Step 9 (Save Response)
```

### Step 8: Tool Execution (tool_executor.py)
```
15. For each tool call:
    a. Parse tool name and arguments
    b. If "search_documents":
       - Call retrieval_service.search_documents:
         * Normalize query
         * Generate embeddings
         * Call hybrid_search_chunks RPC:
           - Vector search (pgvector cosine similarity)
           - Keyword search (PostgreSQL full-text search)
           - Reciprocal Rank Fusion (RRF)
         * If reranking enabled:
           - Call Jina AI Reranker API
           - Rerank top 20 results
         * Return top 20 chunks

       - Format results:
         "[Source: filename.pdf] (similarity: 0.95)\nArticle 46..."

       - Add tool result to conversation history:
         {"role": "tool", "tool_call_id": "id", "content": "results"}
```

### Step 9: Tool Calling Loop
```
16. Increment round counter
17. If rounds < 3:
    - Go back to Step 6 with updated conversation history
    - LLM will read tool results and generate final response
18. Else:
    - Force exit loop
```

### Step 10: Save Assistant Response
```
19. If full_response not empty:
    a. Insert assistant message into messages table:
       - thread_id
       - user_id
       - role: "assistant"
       - content: full_response
       - created_at: now()

    b. Update thread.updated_at to now()
```

### Step 11: Complete Stream
```
20. Yield final SSE event: {"type": "done"}
21. Close SSE connection
```

### Error Handling
```
If any error occurs:
- Yield SSE event: {"type": "error", "error": "message"}
- Close connection
```

**Database Tables Involved**:
- `messages` - Store user and assistant messages
- `threads` - Update timestamp
- `chunks` - Search via hybrid_search_chunks
- `documents` - Check if retrieval available
- `global_settings` - LLM configuration

**Database Functions Called**:
- `hybrid_search_chunks(query_text, query_embedding, ...) -> chunks`
  - Calls `match_chunks` for vector search
  - Calls `keyword_search_chunks` for keyword search
  - Applies Reciprocal Rank Fusion (RRF)

**External APIs Called**:
- LLM API (streaming chat completions)
- Embedding API (for query embedding)
- Jina AI Reranker API (optional)
- LangSmith (tracing)

**SSE Event Timeline**:
```
event: text_delta
data: {"content": "Article"}

event: text_delta
data: {"content": " 46"}

event: text_delta
data: {"content": " states..."}

...

event: done
data: {}
```

**Tool Calling Example**:

**Round 1**: User asks "What is Article 46?"
```
LLM Response: [tool_call: search_documents("Article 46")]
Backend: Execute search, get 20 chunks
Backend: Add tool results to conversation
```

**Round 2**: LLM with tool results
```
LLM Response: [text] "**Manba:** Document.pdf\n\n46-modda. ..."
Backend: Stream response to user
Backend: Save assistant message
```

---

## Database Schema

**Database**: PostgreSQL with pgvector extension

### Tables

#### threads
**Purpose**: Chat conversation threads.

```sql
CREATE TABLE threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT DEFAULT 'New Chat',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Indexes**:
- `idx_threads_user_id` on `user_id`
- `idx_threads_updated_at` on `updated_at DESC`

**RLS**: Enabled - users can only access their own threads.

---

#### messages
**Purpose**: Store user and assistant messages.

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Indexes**:
- `idx_messages_thread_id` on `thread_id`
- `idx_messages_created_at` on `created_at`

**RLS**: Enabled - users can only access their own messages.

**Cascade**: Deleting a thread deletes all messages.

---

#### documents
**Purpose**: Store uploaded document metadata.

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    storage_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    chunk_count INTEGER DEFAULT 0,
    content_hash TEXT,  -- SHA-256 hash
    metadata JSONB DEFAULT '{}',  -- DocumentMetadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Indexes**:
- `idx_documents_user_id` on `user_id`
- `idx_documents_status` on `status`

**RLS**: Enabled - users can only access their own documents.

**Realtime**: Enabled - broadcasts status changes to frontend.

---

#### chunks
**Purpose**: Store document chunks with embeddings.

```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding vector(1536),  -- pgvector type
    metadata JSONB DEFAULT '{}',
    content_tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Indexes**:
- `idx_chunks_document_id` on `document_id`
- `idx_chunks_user_id` on `user_id`
- `idx_chunks_embedding` USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
- `idx_chunks_content_tsv` USING GIN (content_tsv)

**RLS**: Enabled - users can only access their own chunks.

**Cascade**: Deleting a document deletes all chunks.

---

#### user_profiles
**Purpose**: Store user profiles with admin status.

```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);
```

**RLS**: Enabled
- Users can view own profile
- Admins can view all profiles
- Admins can create profiles

**Trigger**: Auto-creates profile on user signup.

---

#### global_settings
**Purpose**: Store global LLM and embedding settings (single row).

```sql
CREATE TABLE global_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    llm_model TEXT,
    llm_base_url TEXT,
    llm_api_key TEXT,  -- Encrypted
    embedding_model TEXT,
    embedding_base_url TEXT,
    embedding_api_key TEXT,  -- Encrypted
    embedding_dimensions INTEGER,
    jina_api_key TEXT,  -- Encrypted
    jina_rerank_model TEXT,
    jina_rerank_enabled BOOLEAN,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**RLS**: Enabled
- All authenticated users can read
- Only admins can update (enforced in backend)

---

### Functions

#### match_chunks
**Purpose**: Vector similarity search.

```sql
CREATE FUNCTION match_chunks(
    query_embedding vector(1536),
    match_threshold float,
    match_count int,
    p_user_id uuid,
    metadata_filters jsonb DEFAULT NULL
) RETURNS TABLE (
    id uuid, document_id uuid, content text,
    chunk_index int, metadata jsonb, similarity float
)
```

**Algorithm**:
1. Filter chunks by user_id
2. Calculate cosine similarity: `1 - (embedding <=> query_embedding)`
3. Filter by similarity > threshold
4. Filter by metadata (JSONB containment)
5. Order by similarity DESC
6. Limit to match_count

---

#### keyword_search_chunks
**Purpose**: Full-text keyword search.

```sql
CREATE FUNCTION keyword_search_chunks(
    query_text text,
    match_count int,
    p_user_id uuid,
    metadata_filters jsonb DEFAULT NULL
) RETURNS TABLE (
    id uuid, document_id uuid, content text,
    chunk_index int, metadata jsonb, rank float
)
```

**Algorithm**:
1. Filter chunks by user_id
2. Convert query to tsquery: `websearch_to_tsquery('english', query_text)`
3. Match against content_tsv: `content_tsv @@ query`
4. Calculate rank: `ts_rank(content_tsv, query)`
5. Filter by metadata (JSONB containment)
6. Order by rank DESC
7. Limit to match_count

---

#### hybrid_search_chunks
**Purpose**: Hybrid search combining vector + keyword with RRF.

```sql
CREATE FUNCTION hybrid_search_chunks(
    query_text text,
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 20,
    final_count int DEFAULT 5,
    p_user_id uuid DEFAULT NULL,
    metadata_filters jsonb DEFAULT NULL,
    rrf_k int DEFAULT 60
) RETURNS TABLE (
    id uuid, document_id uuid, content text,
    chunk_index int, metadata jsonb,
    vector_similarity float, keyword_rank float, rrf_score float
)
```

**Algorithm**:
1. **Vector Search**: Call `match_chunks`, rank results
2. **Keyword Search**: Call `keyword_search_chunks`, rank results
3. **RRF Fusion**: For each unique chunk ID:
   ```
   rrf_score = (1 / (k + vector_rank)) + (1 / (k + keyword_rank))
   ```
4. Join with chunks table to get full data
5. Order by rrf_score DESC
6. Limit to final_count

**Parameters**:
- `rrf_k` (default 60) - RRF constant, controls fusion balance

---

### Storage Bucket

#### documents
**Purpose**: Store uploaded document files.

**Access Control**:
- Users can upload to `{user_id}/` folder
- Users can read from `{user_id}/` folder
- Users can delete from `{user_id}/` folder

---

## Configuration

### Environment Variables

**File**: `.env` in project root

#### Required

```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_ROLE_KEY=eyJxxx...

# LangSmith (optional but recommended)
LANGSMITH_API_KEY=lsv2_xxx...
LANGSMITH_PROJECT=rag-masterclass
```

#### Optional (Fallbacks)

```env
# LLM Settings (fallback if global_settings not configured)
LLM_API_KEY=sk-xxx...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o

# Embedding Settings (fallback if global_settings not configured)
EMBEDDING_API_KEY=sk-xxx...
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

# Legacy OpenAI Key (used as fallback for both LLM and Embedding)
OPENAI_API_KEY=sk-xxx...

# Settings Encryption (for encrypting API keys in database)
SETTINGS_ENCRYPTION_KEY=xxx...  # Generate with Fernet.generate_key()

# CORS
CORS_ORIGINS=["http://localhost:5173"]

# Jina Reranker (optional)
JINA_API_KEY=jina_xxx...
JINA_RERANK_MODEL=jina-reranker-v2-base-multilingual
JINA_RERANK_ENABLED=true
```

---

### Configuration Priority

**LLM Settings**:
1. `global_settings` table (decrypted `llm_api_key`)
2. Environment variable `LLM_API_KEY`
3. Environment variable `OPENAI_API_KEY`
4. Raise HTTPException(503) if none configured

**Embedding Settings**:
1. `global_settings` table (decrypted `embedding_api_key`)
2. Environment variable `EMBEDDING_API_KEY`
3. Environment variable `OPENAI_API_KEY`
4. Raise HTTPException(503) if none configured

**Why Global Settings?**:
- Allows runtime configuration via UI
- No need to restart backend when changing providers
- API keys encrypted at rest
- Admins can update without server access

---

### Settings Encryption

**Library**: `cryptography.Fernet`

**Key Generation**:
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()  # Store in SETTINGS_ENCRYPTION_KEY
```

**Encryption** (settings.py):
```python
def encrypt_value(value: str) -> str:
    f = Fernet(settings.settings_encryption_key.encode())
    return f.encrypt(value.encode()).decode()
```

**Decryption** (settings.py):
```python
def decrypt_value(value: str) -> str:
    f = Fernet(settings.settings_encryption_key.encode())
    return f.decrypt(value.encode()).decode()
```

**Usage**: All API keys in `global_settings` table are encrypted before storage.

---

## Authentication & Authorization

### Authentication

**Method**: Supabase JWT Bearer tokens

**Flow**:
1. User logs in via Supabase Auth (frontend)
2. Supabase returns JWT token
3. Frontend sends token in `Authorization: Bearer <token>` header
4. Backend verifies token in `get_current_user` dependency

**Token Verification** (dependencies.py):
```python
async def get_current_user(credentials: HTTPAuthorizationCredentials):
    token = credentials.credentials
    payload = jwt.decode(
        token,
        settings.supabase_anon_key,
        algorithms=["HS256", "ES256"],
        options={"verify_signature": False},
        audience="authenticated"
    )
    user_id = payload["sub"]
    email = payload["email"]
    # Query user_profiles for is_admin
    return User(id=user_id, email=email, is_admin=...)
```

---

### Authorization

**Levels**:
1. **Authenticated** - Any logged-in user
2. **Admin** - User with `is_admin=true` in `user_profiles`

**Admin Endpoints**:
- `POST /documents/upload` - Admin only
- `DELETE /documents/{id}` - Admin only
- `PUT /settings` - Admin only
- `POST /admin/users` - Admin only
- `GET /admin/users` - Admin only
- `PATCH /admin/users/{id}/admin` - Admin only

**Admin Check** (dependencies.py):
```python
async def get_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(403, detail="Admin access required")
    return current_user
```

**Setting Admin Status**:
1. Via SQL: `UPDATE user_profiles SET is_admin = true WHERE email = 'admin@example.com'`
2. Via API: `PATCH /admin/users/{user_id}/admin` (existing admin only)

---

### Row-Level Security (RLS)

**Purpose**: Database-level access control.

**Enabled Tables**:
- `threads` - Users own threads
- `messages` - Users own messages
- `documents` - Users own documents
- `chunks` - Users own chunks
- `user_profiles` - Users see own profile, admins see all
- `global_settings` - All authenticated users can read

**Example Policy** (threads):
```sql
CREATE POLICY "Users can view their own threads"
    ON threads FOR SELECT
    USING (auth.uid() = user_id);
```

**Shared Access Model**:
- Documents are uploaded by admin (`user_id = admin_id`)
- Chunks inherit admin's `user_id`
- Search functions bypass RLS (use `p_user_id` parameter)
- Result: All users can search all documents

---

## Summary

This backend implements a production-ready RAG system with:

✅ **Multi-format document ingestion** - PDF, DOCX, HTML, TXT, MD
✅ **LLM-based metadata extraction** - Structured document metadata
✅ **Hybrid search** - Vector + keyword + RRF
✅ **Reranking** - Cross-encoder for improved relevance
✅ **Streaming chat** - Server-Sent Events with tool calling
✅ **Multi-tenant** - Row-level security, admin controls
✅ **Provider abstraction** - Runtime-configurable LLM/embedding
✅ **Observability** - LangSmith tracing
✅ **Real-time updates** - Supabase Realtime for ingestion status

**Key Design Decisions**:
- **No LangChain** - Direct SDK calls for full control
- **Pydantic for structured outputs** - Type-safe LLM responses
- **Hybrid search** - Best of vector and keyword
- **Shared document access** - Admin uploads, all users query
- **Background ingestion** - Non-blocking document processing
- **RLS + API auth** - Defense in depth

---

**End of Documentation**
