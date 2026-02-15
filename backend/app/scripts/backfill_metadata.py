"""Backfill metadata for existing documents."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from supabase import create_client
from app.config import get_settings
from app.services.metadata_service import extract_metadata

settings = get_settings()
supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)


async def backfill_metadata():
    """Extract metadata for documents missing it."""

    print("=" * 60)
    print("Metadata Backfill Script")
    print("=" * 60)
    print()

    # Get documents without metadata (metadata is NULL or empty object)
    print("Fetching documents without metadata...")
    docs = supabase.table("documents").select("*").or_(
        "metadata.is.null,metadata.eq.{}"
    ).eq("status", "completed").execute()

    if not docs.data:
        print("✓ No documents need backfilling")
        return

    print(f"Found {len(docs.data)} documents to process\n")

    success_count = 0
    fail_count = 0

    for idx, doc in enumerate(docs.data, 1):
        try:
            print(f"[{idx}/{len(docs.data)}] Processing: {doc['filename']}")

            # Download file from storage
            file_data = supabase.storage.from_("documents").download(doc["storage_path"])
            text_content = file_data.decode('utf-8')

            # Extract metadata
            metadata = await extract_metadata(text_content, doc["filename"])

            # Update document
            supabase.table("documents").update({
                "metadata": metadata.model_dump()
            }).eq("id", doc["id"]).execute()

            # Update all chunks with inherited metadata
            chunk_metadata = metadata.model_dump()
            chunk_metadata["filename"] = doc["filename"]

            supabase.table("chunks").update({
                "metadata": chunk_metadata
            }).eq("document_id", doc["id"]).execute()

            print(f"  ✓ Extracted: {metadata.document_type}, {len(metadata.topics)} topics")
            print(f"    Summary: {metadata.summary[:80]}...")
            success_count += 1

        except Exception as e:
            print(f"  ✗ Failed: {e}")
            fail_count += 1

        print()

    print("=" * 60)
    print(f"Backfill complete:")
    print(f"  Success: {success_count}")
    print(f"  Failed:  {fail_count}")
    print(f"  Total:   {len(docs.data)}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(backfill_metadata())
