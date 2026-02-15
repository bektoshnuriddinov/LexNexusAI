"""Document upload, list, and delete endpoints."""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status

from app.dependencies import get_current_user, get_admin_user, User
from app.db.supabase import get_supabase_client
from app.services.ingestion_service import process_document, hash_file_content

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_TYPES = {
    "text/plain": [".txt"],
    "text/markdown": [".md"],
    "application/pdf": [".pdf"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    "text/html": [".html", ".htm"],
    "application/octet-stream": None,  # fallback, check extension
}
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx", ".html", ".htm"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB (increased for PDFs)


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_admin_user),
):
    """Upload a document for ingestion. Admin only."""
    # Validate file extension
    filename = file.filename or "unknown"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10 MB."
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty."
        )

    # Calculate content hash for deduplication
    content_hash = hash_file_content(content)

    # Determine content type based on file extension
    content_type = file.content_type or "text/plain"
    if ext == ".md":
        content_type = "text/markdown"
    elif ext == ".txt":
        content_type = "text/plain"
    elif ext == ".pdf":
        content_type = "application/pdf"
    elif ext == ".docx":
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif ext in (".html", ".htm"):
        content_type = "text/html"

    supabase = get_supabase_client()

    # Check for exact duplicate (same content hash)
    existing = supabase.table("documents").select("*").eq(
        "user_id", current_user.id
    ).eq("content_hash", content_hash).execute()

    if existing.data:
        # Exact duplicate - return existing document without re-processing
        return existing.data[0]

    # Check if filename exists with different content (update scenario)
    existing_by_name = supabase.table("documents").select("*").eq(
        "user_id", current_user.id
    ).eq("filename", filename).execute()

    document_id = None
    storage_path = None

    if existing_by_name.data:
        old_doc = existing_by_name.data[0]
        if old_doc.get("content_hash") and old_doc["content_hash"] != content_hash:
            # Content changed - delete old chunks and re-use document record
            supabase.table("chunks").delete().eq("document_id", old_doc["id"]).execute()

            # Re-use existing storage path and document ID
            document_id = old_doc["id"]
            storage_path = old_doc["storage_path"]

            # Delete old file from storage
            try:
                supabase.storage.from_("documents").remove([storage_path])
            except Exception:
                pass  # Old file may not exist

            # Upload new content to same path
            supabase.storage.from_("documents").upload(
                path=storage_path,
                file=content,
                file_options={"content-type": content_type},
            )

            # Update document record
            supabase.table("documents").update({
                "content_hash": content_hash,
                "file_type": content_type,
                "file_size": len(content),
                "status": "processing",
                "chunk_count": 0,
                "error_message": None,
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("id", document_id).execute()

            # Get updated document
            result = supabase.table("documents").select("*").eq("id", document_id).single().execute()
            document = result.data
        else:
            # Same content, same filename - return existing
            return old_doc
    else:
        # New file - upload to storage
        file_id = str(uuid.uuid4())
        storage_path = f"{current_user.id}/{file_id}{ext}"

        supabase.storage.from_("documents").upload(
            path=storage_path,
            file=content,
            file_options={"content-type": content_type},
        )

        # Create new document record
        doc_record = {
            "user_id": current_user.id,
            "filename": filename,
            "file_type": content_type,
            "file_size": len(content),
            "storage_path": storage_path,
            "status": "pending",
            "content_hash": content_hash,
        }

        result = supabase.table("documents").insert(doc_record).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create document record"
            )

        document = result.data[0]
        document_id = document["id"]

    # Trigger background processing (only if status is not already completed)
    if document.get("status") != "completed":
        background_tasks.add_task(process_document, document_id, current_user.id)

    return document


@router.get("")
async def list_documents(current_user: User = Depends(get_current_user)):
    """List all documents for the current user."""
    supabase = get_supabase_client()
    result = supabase.table("documents").select("*").eq(
        "user_id", current_user.id
    ).order("created_at", desc=True).execute()

    return result.data


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_admin_user),
):
    """Delete a document and its storage file (chunks cascade via FK). Admin only."""
    supabase = get_supabase_client()

    # Get document (RLS ensures user owns it)
    result = supabase.table("documents").select("*").eq(
        "id", document_id
    ).eq("user_id", current_user.id).single().execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    doc = result.data

    # Delete from storage
    try:
        supabase.storage.from_("documents").remove([doc["storage_path"]])
    except Exception:
        pass  # Storage file may already be gone

    # Delete document record (chunks cascade)
    supabase.table("documents").delete().eq("id", document_id).execute()

    return {"status": "deleted"}
