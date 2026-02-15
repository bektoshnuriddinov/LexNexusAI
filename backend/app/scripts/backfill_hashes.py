"""Backfill content_hash for existing documents."""
import hashlib
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from supabase import create_client
from app.config import get_settings

settings = get_settings()
supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)


def backfill_hashes():
    """Calculate and store content_hash for all documents missing it."""
    # Get all documents without content_hash
    print("Fetching documents without content_hash...")
    docs = supabase.table("documents").select("*").is_("content_hash", "null").execute()

    if not docs.data:
        print("✓ No documents need backfilling")
        return

    print(f"Found {len(docs.data)} documents to process")

    success_count = 0
    fail_count = 0

    for doc in docs.data:
        try:
            # Download file from storage
            file_data = supabase.storage.from_("documents").download(doc["storage_path"])

            # Calculate hash
            content_hash = hashlib.sha256(file_data).hexdigest()

            # Update document
            supabase.table("documents").update({
                "content_hash": content_hash
            }).eq("id", doc["id"]).execute()

            print(f"✓ Updated {doc['filename']} (hash: {content_hash[:12]}...)")
            success_count += 1

        except Exception as e:
            print(f"✗ Failed {doc['filename']}: {e}")
            fail_count += 1

    print(f"\n{'='*60}")
    print(f"Backfill complete: {success_count} succeeded, {fail_count} failed")


if __name__ == "__main__":
    backfill_hashes()
