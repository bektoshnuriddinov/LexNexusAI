#!/bin/bash
# Test script for document deduplication

echo "=========================================="
echo "Document Deduplication Test"
echo "=========================================="
echo ""

# Get auth token
echo "1. Getting auth token for test@test.com..."
TOKEN=$(curl -s -X POST "https://dkbbhbpluvtimzzyavyg.supabase.co/auth/v1/token?grant_type=password" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRrYmJoYnBsdXZ0aW16enlhdnlnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk1MzA5MTksImV4cCI6MjA1NTEwNjkxOX0.1gPZQUJmX2RmPIFX9pqo48jQZxeFMYEXPvHO_u2C6xE" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"M+T!kV3v2d_xn/p"}' | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "✗ Failed to get auth token"
    exit 1
fi

echo "✓ Auth token obtained"
echo ""

# Create a test file
echo "2. Creating test file..."
TEST_FILE="/tmp/dedup_test_$(date +%s).txt"
echo "This is a test file for deduplication testing." > "$TEST_FILE"
echo "Created: $TEST_FILE"
echo ""

# First upload
echo "3. Uploading file for the first time..."
FIRST_RESPONSE=$(curl -s -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@$TEST_FILE")

FIRST_DOC_ID=$(echo "$FIRST_RESPONSE" | jq -r '.id')
FIRST_HASH=$(echo "$FIRST_RESPONSE" | jq -r '.content_hash')

echo "✓ First upload response:"
echo "  Document ID: $FIRST_DOC_ID"
echo "  Content Hash: $FIRST_HASH"
echo "  Status: $(echo "$FIRST_RESPONSE" | jq -r '.status')"
echo ""

# Check if content_hash exists
if [ "$FIRST_HASH" = "null" ] || [ -z "$FIRST_HASH" ]; then
    echo "⚠️  WARNING: content_hash is null - migration may not be applied!"
    echo "   The deduplication logic is in place, but the database column doesn't exist."
    echo "   Please apply the migration from: supabase/migrations/20260214194302_add_content_hash.sql"
    echo ""
fi

# Wait a moment
sleep 2

# Second upload (exact duplicate)
echo "4. Uploading the SAME file again (testing deduplication)..."
SECOND_RESPONSE=$(curl -s -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@$TEST_FILE")

SECOND_DOC_ID=$(echo "$SECOND_RESPONSE" | jq -r '.id')
SECOND_HASH=$(echo "$SECOND_RESPONSE" | jq -r '.content_hash')

echo "✓ Second upload response:"
echo "  Document ID: $SECOND_DOC_ID"
echo "  Content Hash: $SECOND_HASH"
echo "  Status: $(echo "$SECOND_RESPONSE" | jq -r '.status')"
echo ""

# Compare results
echo "=========================================="
echo "DEDUPLICATION TEST RESULTS"
echo "=========================================="
echo ""

if [ "$FIRST_DOC_ID" = "$SECOND_DOC_ID" ]; then
    echo "✅ SUCCESS: Deduplication working!"
    echo "   Both uploads returned the same document ID: $FIRST_DOC_ID"
    echo "   No duplicate document was created."
else
    echo "❌ FAILED: Deduplication not working"
    echo "   First upload ID:  $FIRST_DOC_ID"
    echo "   Second upload ID: $SECOND_DOC_ID"
    echo "   These should be identical but are different."
    echo ""
    echo "Possible causes:"
    echo "  1. Migration not applied (content_hash column missing)"
    echo "  2. Code changes not loaded (backend not restarted)"
fi

echo ""

# List all documents
echo "5. Listing all documents..."
curl -s http://localhost:8000/documents \
  -H "Authorization: Bearer $TOKEN" | jq '.[] | {id, filename, content_hash, status}'

echo ""

# Cleanup
echo "6. Cleaning up test documents..."
curl -s -X DELETE http://localhost:8000/documents/$FIRST_DOC_ID \
  -H "Authorization: Bearer $TOKEN" > /dev/null

if [ "$FIRST_DOC_ID" != "$SECOND_DOC_ID" ]; then
    curl -s -X DELETE http://localhost:8000/documents/$SECOND_DOC_ID \
      -H "Authorization: Bearer $TOKEN" > /dev/null
fi

rm "$TEST_FILE"

echo "✓ Cleanup complete"
echo ""
