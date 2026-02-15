"""Ingestion orchestration: download -> extract -> chunk -> embed -> store."""
import hashlib
import logging
from app.db.supabase import get_supabase_client
from app.services.chunking_service import chunk_text
from app.services.embedding_service import get_embeddings
from app.services.metadata_service import extract_metadata
from app.services.extraction_service import extract_text

logger = logging.getLogger(__name__)

BATCH_SIZE = 50  # embeddings per batch


def hash_file_content(file_bytes: bytes) -> str:
    """Calculate SHA-256 hash of file content."""
    return hashlib.sha256(file_bytes).hexdigest()


async def process_document(document_id: str, user_id: str) -> None:
    """
    Process an uploaded document: extract text, chunk, embed, and store.

    Updates document status throughout the process.
    """
    supabase = get_supabase_client()

    try:
        # Update status to processing
        supabase.table("documents").update({
            "status": "processing"
        }).eq("id", document_id).execute()

        # Get document record
        doc_result = supabase.table("documents").select("*").eq("id", document_id).single().execute()
        doc = doc_result.data

        if not doc:
            raise ValueError(f"Document {document_id} not found")

        # Download file from storage
        storage_path = doc["storage_path"]
        file_bytes = supabase.storage.from_("documents").download(storage_path)

        # Extract text based on file type
        text = extract_text(file_bytes, doc["file_type"])

        if not text.strip():
            raise ValueError("No text content extracted from document")

        # Extract metadata from document content
        logger.info(f"Extracting metadata for document {document_id}")
        document_metadata = await extract_metadata(text, doc["filename"])

        # Store metadata in documents table
        supabase.table("documents").update({
            "metadata": document_metadata.model_dump()
        }).eq("id", document_id).execute()

        # Chunk the text
        chunks = chunk_text(text)

        if not chunks:
            raise ValueError("No chunks generated from document")

        # Batch embed and store chunks
        total_chunks = 0
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            embeddings = await get_embeddings(batch, user_id=user_id)

            # Insert chunks with embeddings (inherit metadata from document)
            chunk_records = []
            for j, (chunk_content, embedding) in enumerate(zip(batch, embeddings)):
                # Merge document metadata with chunk-specific metadata
                chunk_metadata = document_metadata.model_dump()
                chunk_metadata["filename"] = doc["filename"]
                chunk_metadata["chunk_index"] = i + j

                chunk_records.append({
                    "document_id": document_id,
                    "user_id": user_id,
                    "content": chunk_content,
                    "chunk_index": i + j,
                    "embedding": embedding,
                    "metadata": chunk_metadata,
                })

            supabase.table("chunks").insert(chunk_records).execute()
            total_chunks += len(batch)

        # Update document status to completed
        supabase.table("documents").update({
            "status": "completed",
            "chunk_count": total_chunks,
        }).eq("id", document_id).execute()

        logger.info(f"Document {document_id} processed: {total_chunks} chunks created")

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        supabase.table("documents").update({
            "status": "failed",
            "error_message": str(e),
        }).eq("id", document_id).execute()
