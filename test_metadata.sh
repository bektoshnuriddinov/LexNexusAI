#!/bin/bash
# Test metadata extraction functionality

echo "=========================================="
echo "Metadata Extraction Test"
echo "=========================================="
echo ""

# Check backend health
echo "1. Checking backend health..."
HEALTH=$(curl -s http://localhost:8000/health)
if [ "$HEALTH" == '{"status":"ok"}' ]; then
    echo "✓ Backend is running"
else
    echo "✗ Backend is not responding"
    exit 1
fi
echo ""

# Create a test file with technical content
echo "2. Creating test document..."
TEST_FILE="/tmp/python_tutorial_$(date +%s).txt"
cat > "$TEST_FILE" << 'EOF'
# Python FastAPI Tutorial for Beginners

This is a comprehensive guide to building web APIs with FastAPI, a modern Python web framework.

## Introduction

FastAPI is a high-performance web framework for building APIs with Python 3.7+. It's built on top of Starlette for the web parts and Pydantic for the data parts.

## Key Features

- Fast: Very high performance, on par with NodeJS and Go
- Easy: Designed to be easy to use and learn
- Robust: Get production-ready code with automatic interactive documentation
- Standards-based: Based on OpenAPI and JSON Schema

## Getting Started

First, install FastAPI and Uvicorn:

```python
pip install fastapi uvicorn
```

Create your first API:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

Run the server:

```bash
uvicorn main:app --reload
```

## Conclusion

FastAPI is perfect for beginners learning API development with Python. It combines ease of use with high performance.

Topics covered: Python, FastAPI, REST APIs, Web Development, Uvicorn
Framework: FastAPI
Difficulty: Beginner
Year: 2024
EOF

echo "✓ Created test file: $TEST_FILE"
echo ""

# Note: We need auth token but can't get it without Supabase credentials
echo "3. Attempting to test metadata extraction..."
echo ""
echo "⚠️  To complete this test, you need to:"
echo "   1. Apply the migration via Supabase Dashboard SQL Editor:"
echo "      Copy the SQL from: supabase/migrations/20260214200109_add_metadata.sql"
echo "   2. Verify global_settings table has LLM configuration"
echo "   3. Use the browser UI to upload this test file:"
echo "      File location: $TEST_FILE"
echo ""
echo "Expected results after upload:"
echo "  - document_type: 'tutorial'"
echo "  - topics: ['Python', 'FastAPI', 'REST APIs', 'Web Development']"
echo "  - programming_languages: ['Python']"
echo "  - frameworks_tools: ['FastAPI', 'Uvicorn']"
echo "  - technical_level: 'beginner'"
echo "  - summary: Short description of the tutorial"
echo ""
echo "To verify:"
echo "  1. Open http://localhost:5173"
echo "  2. Sign in as admin"
echo "  3. Go to Documents page"
echo "  4. Upload the file at: $TEST_FILE"
echo "  5. Wait ~15 seconds for processing"
echo "  6. Look for colored metadata badges below the document"
echo ""
echo "Metadata badges should appear:"
echo "  - Blue badge: 'tutorial'"
echo "  - Green badges: 'Python', 'FastAPI', 'REST APIs'"
echo "  - Purple badge: 'Python'"
echo "  - Orange badges: 'FastAPI', 'Uvicorn'"
echo ""
