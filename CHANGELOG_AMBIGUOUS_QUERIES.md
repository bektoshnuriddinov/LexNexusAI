# Changelog - Ambiguous Query Handling

**Date:** 2026-02-15
**Feature:** Smart clarification for ambiguous article queries

## Problem

When users asked for a specific article without mentioning which law or resolution (e.g., "46-modda" or "5-modda to'liq"), the system had conflicting behavior:
- Instructions said to ask for clarification
- Examples showed displaying all results from multiple laws at once
- This could be confusing and overwhelming for users

## Solution

Updated the system prompt to properly handle ambiguous queries:

### New Behavior Flow

1. **Analyze Query Type**
   - **Ambiguous:** Just article number without law name ("46-modda", "5-modda")
   - **Specific:** Mentions law/resolution name ("Davlat xaridlari Qonunining 46-moddasi")

2. **For Ambiguous Queries:**
   - **DO NOT search immediately**
   - Ask user to clarify which law/resolution they mean
   - Example: "46-modda qaysi qonun yoki qaror haqida gap ketyapti? Iltimos, hujjat nomini yoki raqamini ko'rsating."

3. **For Specific Queries:**
   - Search immediately and provide full article

4. **After User Clarifies:**
   - Search with the specific law name
   - Provide complete article from that law

## Changes Made

### File: `backend/app/services/llm_service.py`

#### 1. Updated SYSTEM_PROMPT (lines 64-125)

**Before:**
```python
📋 STEP-BY-STEP PROCESS:
1. **FIRST**: Check if chunks come from MULTIPLE DIFFERENT laws/documents
   - If YES: Ask user to clarify which law they mean (see example below)
   - If NO or user already specified: Continue to step 2
...
🔍 HANDLING MULTIPLE SOURCES - SHOW ALL:
(showed all results from multiple laws)
```

**After:**
```python
📋 STEP-BY-STEP PROCESS:

**CRITICAL: ALWAYS SEARCH FIRST - NEVER RESPOND WITHOUT CALLING search_documents TOOL!**

1. **ANALYZE USER'S QUERY - Is it specific or ambiguous?**

   AMBIGUOUS queries (need clarification):
   - Just article number: "5-modda", "46-modda to'liq"
   - No law/resolution name mentioned

   SPECIFIC queries (can search directly):
   - Mentions law name: "Davlat xaridlari Qonunining 46-moddasi"
   - Mentions resolution: "294-son qaror"
   - Contains unique terms from specific law

2. **IF QUERY IS AMBIGUOUS:**
   - **DO NOT call search_documents tool yet!**
   - Ask user: "Qaysi qonun yoki qaror haqida gap ketyapti? Iltimos, hujjat nomini yoki raqamini ko'rsating."
   ...
```

#### 2. Updated RAG_TOOLS description (lines 180-186)

**Before:**
```python
"description": """**ALWAYS CALL THIS TOOL FOR ALL QUESTIONS** - Search user's uploaded legal documents and retrieve COMPLETE articles.
```

**After:**
```python
"description": """Search user's uploaded legal documents and retrieve COMPLETE articles.

⚠️ IMPORTANT: Before calling this tool, check if the user's query is SPECIFIC or AMBIGUOUS:
- AMBIGUOUS (just article number): Ask user to specify which law/resolution first
- SPECIFIC (mentions law name): Call this tool immediately
```

## Examples

### Example 1: Ambiguous Query

**User:** "46-modda to'liq"

**Assistant Response:**
```
46-modda qaysi qonun yoki qaror haqida gap ketyapti?

Men sizga to'liq javob berishim uchun, iltimos, hujjat nomini yoki raqamini ko'rsating. Masalan:
- "Davlat xaridlari to'g'risidagi Qonun"
- "Ta'lim to'g'risidagi Qonun"
- "294-son qaror"
```

**User:** "Davlat xaridlari qonuni"

**Assistant:** [Provides complete Article 46 from that specific law]

### Example 2: Specific Query

**User:** "Davlat xaridlari Qonunining 46-moddasi"

**Assistant:** [Immediately provides complete Article 46 from that law]

### Example 3: Resolution Query

**User:** "294-son qarorning 5-ilovasi"

**Assistant:** [Immediately provides Annex 5 from Resolution 294]

## Benefits

✅ **Clearer Communication**
- User knows exactly which document they'll get information from
- No confusion about mixed results from different laws

✅ **Better User Experience**
- No information overload from multiple sources
- Focused, relevant answers
- Natural conversation flow

✅ **More Accurate**
- Ensures user gets exactly the law/resolution they need
- Prevents wrong assumptions about which document user meant

✅ **Efficient**
- Two-turn conversation: clarify → answer
- Better than showing all results and hoping user finds the right one

## Testing

To test the new behavior:

1. **Test Ambiguous Query:**
   ```
   User: "46-modda"
   Expected: Assistant asks which law/resolution
   ```

2. **Test User Clarification:**
   ```
   User: "Davlat xaridlari"
   Expected: Assistant searches and provides Article 46 from that law
   ```

3. **Test Specific Query:**
   ```
   User: "Davlat xaridlari qonunining 46-moddasi"
   Expected: Assistant immediately provides the article
   ```

4. **Test Resolution Query:**
   ```
   User: "294-son qaror"
   Expected: Assistant provides information from that resolution
   ```

## Deployment

**No database changes required** - this is a prompt-only update.

**To apply:**
1. Changes are already in the code
2. Restart the backend service:
   ```powershell
   powershell -File scripts/restart-backend.ps1
   ```
3. Test with sample queries

## Rollback

If issues arise, revert the changes in `backend/app/services/llm_service.py` by using git:
```bash
git diff HEAD~1 backend/app/services/llm_service.py
git checkout HEAD~1 -- backend/app/services/llm_service.py
```

Then restart the backend.

---

**Status:** ✅ Implemented and ready for testing
**Impact:** Medium - Improves user experience for legal document queries
**Risk:** Low - No breaking changes, only prompt modification
