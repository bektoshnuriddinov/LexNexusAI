# Creating Test Files for Multi-Format Support

## test_document.html ✓
Already created. This HTML file contains Python programming tutorial content with proper HTML structure.

## test_document.pdf (Manual Creation Required)

**Method 1: Using LibreOffice (Free)**
1. Open LibreOffice Writer
2. Copy and paste the content below
3. Save As → Export as PDF → `test_document.pdf`

**Method 2: Using Microsoft Word**
1. Create a new Word document
2. Copy and paste the content below
3. Save As → PDF → `test_document.pdf`

**Content:**
```
# Python Programming Basics

This is a sample PDF document for testing PDF text extraction in the RAG system.

## Introduction

Python is a high-level, interpreted programming language known for its simplicity and readability. It's widely used in web development, data science, artificial intelligence, and automation.

## Topics Covered
- Variables and data types
- Functions and methods
- Object-oriented programming
- Error handling and exceptions
- File operations

## Why Learn Python?

Python's straightforward syntax makes it an ideal choice for beginners, while its powerful libraries and frameworks support advanced applications in machine learning, web development, and scientific computing.

## Key Features
- Easy to Learn: Clean and readable syntax
- Versatile: Used in multiple domains
- Large Community: Extensive libraries and support
- Cross-platform: Works on Windows, Mac, and Linux

## Conclusion

This document tests multi-format support in the RAG system. Python programming skills are essential for modern software development and data analysis.

Document Type: Tutorial | Technical Level: Beginner | Year: 2024
```

## test_document.docx (Manual Creation Required)

**Method: Using Microsoft Word or LibreOffice Writer**
1. Create a new document
2. Copy and paste the same content as above (PDF content)
3. Save As → Word Document (.docx) → `test_document.docx`

**Alternative:** Use the same PDF content but save in DOCX format

## Placement

All test files should be saved to:
`.agent/validation/fixtures/`

## Verification

After creating the files, verify they work:

```bash
# Test PDF extraction
cd backend
python -c "
from app.services.extraction_service import extract_text_from_pdf
with open('../.agent/validation/fixtures/test_document.pdf', 'rb') as f:
    text = extract_text_from_pdf(f.read())
    print('PDF extraction:', 'SUCCESS' if 'Python' in text else 'FAILED')
"

# Test DOCX extraction
python -c "
from app.services.extraction_service import extract_text_from_docx
with open('../.agent/validation/fixtures/test_document.docx', 'rb') as f:
    text = extract_text_from_docx(f.read())
    print('DOCX extraction:', 'SUCCESS' if 'Python' in text else 'FAILED')
"

# Test HTML extraction
python -c "
from app.services.extraction_service import extract_text_from_html
with open('../.agent/validation/fixtures/test_document.html', 'rb') as f:
    text = extract_text_from_html(f.read())
    print('HTML extraction:', 'SUCCESS' if 'Python' in text else 'FAILED')
"
```

## Expected Content Similarity

All three files should contain similar content about:
- Python programming
- Tutorial-level difficulty
- Topics: variables, functions, OOP, error handling, file operations
- Document type: Tutorial
- Technical level: Beginner

This ensures metadata extraction will produce similar results across formats for comparison testing.
