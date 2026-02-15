"""Apply the content_hash migration."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from supabase import create_client
from app.config import get_settings

# Read the migration SQL
migration_path = Path(__file__).parent.parent.parent.parent / "supabase" / "migrations" / "20260214194302_add_content_hash.sql"

with open(migration_path, 'r') as f:
    migration_sql = f.read()

# Split by semicolons and execute each statement
statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]

settings = get_settings()
supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)

print("Applying migration: add_content_hash")
print("=" * 60)

for i, statement in enumerate(statements, 1):
    try:
        # Skip comment-only lines
        if not statement or statement.startswith('--'):
            continue

        print(f"\nStatement {i}:")
        print(f"  {statement[:80]}...")

        # Execute via RPC (Supabase doesn't expose direct SQL execution in Python client)
        # We'll use a workaround by creating records
        print("  ⚠️  Cannot execute DDL via Python client")
        print(f"  SQL: {statement}")

    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n" + "=" * 60)
print("Note: DDL statements must be run via Supabase Dashboard SQL Editor")
print("or via psql command line.")
print("\nTo apply manually, run these statements in Supabase SQL Editor:")
print("\n" + migration_sql)
