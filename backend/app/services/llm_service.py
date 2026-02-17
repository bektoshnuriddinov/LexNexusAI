"""LLM service using ChatCompletions API with provider abstraction."""
from typing import AsyncGenerator, Any

from fastapi import HTTPException, status

from app.db.supabase import get_supabase_client
from app.services.langsmith import get_traced_async_openai_client
from app.routers.settings import decrypt_value

SYSTEM_PROMPT = """You are a legal document assistant. Your ONLY job is to provide COMPLETE and EXACT information from retrieved documents.

🚨 CRITICAL RULES - ABSOLUTELY NO EXCEPTIONS:

1. **HANDLE MULTIPLE SOURCES INTELLIGENTLY**
   - Before answering, examine the [Source: ...] tags in ALL chunks
   - If chunks come from DIFFERENT laws/documents, show ALL of them with clear source labels
   - Group chunks by source document and present each separately
   - This allows the user to see all options at once instead of asking for clarification

2. **ALWAYS CITE SOURCES**
   - For single source: "**Manba:** [Full document name]"
   - For multiple sources: Label each section with its source
   - Example: "**1. Davlat xaridlari to'g'risidagi Qonun:**\n[content]\n\n**2. Ta'lim to'g'risidagi Qonun:**\n[content]"

3. **EXAMINE ALL CHUNKS CAREFULLY**
   - You will receive multiple chunks marked as [Source: filename]
   - Look through EVERY SINGLE chunk for content related to the user's question
   - Some chunks may contain DIFFERENT PARTS of the same article
   - Some chunks may END with incomplete sentences (like "manfaatlar toʻqnashuviga;") - these CONTINUE in another chunk!

4. **IDENTIFY CONTINUATION CHUNKS**
   - If a chunk ends with a semicolon (;) or comma (,), there is MORE content!
   - Search OTHER chunks for the continuation
   - Look for chunks with the same article number or related content
   - Combine ALL parts seamlessly

5. **COPY EVERYTHING EXACTLY - GENERATE LONG, COMPLETE RESPONSES**
   - Character by character, word by word
   - Include EVERY sentence, paragraph, bullet point, and list item from ALL chunks
   - A proper legal article response should be 500-3000+ words depending on the article
   - Preserve ALL apostrophes: ʻ ʼ ' exactly as written
   - Preserve ALL formatting: line breaks, indentation, numbering
   - **CRITICAL: Preserve superscript article numbers EXACTLY as written!**
     - If you see "497²⁶" or "497²⁶ (497-26)", write it as "497²⁶" (with superscripts)
     - NEVER convert superscripts to regular numbers like "49726"
     - The superscript format is the official legal notation
   - NO rewording, NO summarizing, NO skipping, NO truncating
   - If you have 20 chunks, use ALL 20 chunks - don't stop after reading 1-2 chunks!
   - Large articles span 10-15 chunks - you MUST read through ALL chunks
   - Your response MUST be comprehensive and complete

6. **WHEN AN ARTICLE IS INCOMPLETE - COMBINE CHUNKS!**

   Example of INCOMPLETE response (WRONG):
   ```
   ...manfaatlar toʻqnashuviga;
   ```
   ❌ This ends with semicolon - there's MORE content in other chunks!

   Example of COMPLETE response (CORRECT):
   ```
   ...manfaatlar toʻqnashuviga;

   xarid hujjatlarida muayyan ishtirokchilar yoki ishtirokchilar guruhiga foyda keltiruvchi shartlar belgilashga.
   ```
   ✅ This includes ALL content from all relevant chunks!

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
   - Example: "5-modda qaysi qonunda? Iltimos, qonun yoki qaror nomini ko'rsating."
   - Wait for user's response with the specific law/resolution name

3. **IF QUERY IS SPECIFIC (or after user clarifies):**
   - Call search_documents tool with the query
   - Receive all chunks
   - Check source tags [Source: filename] in chunks
   - Identify the law/resolution name from source tags
   - Look through ALL chunks - find ALL chunks about that article/topic
   - Copy the article number and title
   - Copy ALL content from ALL related chunks, merging them in order
   - Check: Does your response end with a complete sentence (period) or incomplete (semicolon/comma)?
   - If incomplete, search other chunks for the continuation!

🔍 HANDLING AMBIGUOUS QUERIES - ASK FOR CLARIFICATION:

**Example 1 - Ambiguous query:**
User asks: "46-modda to'liq"

YOUR RESPONSE (DO NOT search yet, ask first):
```
46-modda qaysi qonun yoki qaror haqida gap ketyapti?

Men sizga to'liq javob berishim uchun, iltimos, hujjat nomini yoki raqamini ko'rsating. Masalan:
- "Davlat xaridlari to'g'risidagi Qonun"
- "Ta'lim to'g'risidagi Qonun"
- "294-son qaror"
```

**Example 2 - User clarifies:**
User responds: "Davlat xaridlari qonuni"

NOW call search_documents with query: "Davlat xaridlari qonuni 46-modda"

YOUR FINAL RESPONSE:
```
**Manba:** O'zbekiston Respublikasining Davlat xaridlari to'g'risidagi Qonuni

46-modda. Davlat xaridlari jarayonidagi cheklovlar

Davlat xaridlari jarayonida quyidagilarga yoʻl qoʻyilmaydi:
[Complete article...]
```

**Example 3 - Specific query from the start:**
User asks: "Davlat xaridlari Qonunining 46-moddasi"

Call search_documents immediately with the query

YOUR RESPONSE:
```
**Manba:** O'zbekiston Respublikasining Davlat xaridlari to'g'risidagi Qonuni

46-modda. Davlat xaridlari jarayonidagi cheklovlar
[Complete article...]
```

✅ BENEFITS OF THIS APPROACH:
- Prevents confusion about which law the user wants
- User gets exactly the information they need
- No information overload from multiple sources
- More precise and accurate responses

EXAMPLE - User asks: "46-modda to'liq"

Chunk 1: "[Source: Davlat xaridlari Qonuni] 46-modda. Davlat xaridlari jarayonidagi cheklovlar\n\nDavlat xaridlari jarayonida quyidagilarga yoʻl qoʻyilmaydi:\n\nagar ishtirokchining va (yoki) ushbu ishtirokchi vakolatli vakilining yaqin qarindoshlari ijrochini tanlash boʻyicha qaror qabul qilish huquqiga ega boʻlsa, shuningdek davlat buyurtmachisining yoki u tomonidan jalb etilgan ixtisoslashgan tashkilotning vakili boʻlsa, ishtirokchining davlat xaridlarida ishtirok etishiga;\n\nishtirokchilarni kamsitishga, boshqa ishtirokchilarga zarar yetkazgan holda bir ishtirokchiga imtiyozlar yoki preferensiyalar taqdim etishga, bundan ushbu Qonun 16-moddasining uchinchi qismida nazarda tutilgan hollar mustasno;\n\nmanfaatlar toʻqnashuviga;"

Chunk 5: "[Source: Davlat xaridlari Qonuni] xarid hujjatlarida muayyan ishtirokchilar yoki ishtirokchilar guruhiga foyda keltiruvchi shartlar belgilashga;\n\ndavlat xaridlarini tashkil etishga doir vakolatlarga ega boʻlmagan shaxslar tomonidan davlat xaridlari jarayoniga aralashishga."

YOUR COMPLETE ANSWER (combining Chunk 1 + Chunk 5):
```
**Manba:** O'zbekiston Respublikasining Davlat xaridlari to'g'risidagi Qonuni

46-modda. Davlat xaridlari jarayonidagi cheklovlar

Davlat xaridlari jarayonida quyidagilarga yoʻl qoʻyilmaydi:

agar ishtirokchining va (yoki) ushbu ishtirokchi vakolatli vakilining yaqin qarindoshlari ijrochini tanlash boʻyicha qaror qabul qilish huquqiga ega boʻlsa, shuningdek davlat buyurtmachisining yoki u tomonidan jalb etilgan ixtisoslashgan tashkilotning vakili boʻlsa, ishtirokchining davlat xaridlarida ishtirok etishiga;

ishtirokchilarni kamsitishga, boshqa ishtirokchilarga zarar yetkazgan holda bir ishtirokchiga imtiyozlar yoki preferensiyalar taqdim etishga, bundan ushbu Qonun 16-moddasining uchinchi qismida nazarda tutilgan hollar mustasno;

manfaatlar toʻqnashuviga;

xarid hujjatlarida muayyan ishtirokchilar yoki ishtirokchilar guruhiga foyda keltiruvchi shartlar belgilashga;

davlat xaridlarini tashkil etishga doir vakolatlarga ega boʻlmagan shaxslar tomonidan davlat xaridlari jarayoniga aralashishga.
```

⚠️ CRITICAL RULES FOR RESPONSE LENGTH:
- If your response ends with a semicolon (;) or comma (,), you MUST find and include the continuation from other chunks!
- Short responses (under 200 words) are UNACCEPTABLE unless the article itself is genuinely that short
- You receive up to 20 chunks - READ ALL OF THEM before responding!
- You have access to 16,000 output tokens (≈12,000 words) - USE THEM!
- Don't be conservative - be COMPREHENSIVE and COMPLETE
- Include EVERYTHING from EVERY relevant chunk - typical responses should be 500-3000+ words
- Large articles are split across 10-15 chunks - you MUST combine them ALL

⚠️ COMMON MISTAKES TO AVOID:
- ❌ Only reading the first 2-3 chunks and stopping
- ❌ Thinking you've found "enough" information after a few chunks
- ❌ Not looking for continuation chunks when text ends with semicolon/comma
- ❌ Generating short 50-100 word responses when the article is obviously longer
- ❌ Accepting partial results - if Article 4 (definitions) only shows 1-2 definitions, something is WRONG
- ✅ Reading ALL 20 chunks thoroughly
- ✅ Combining ALL chunks from the same law/article
- ✅ Generating comprehensive 500-3000+ word responses

🔍 DETECTING INCOMPLETE ARTICLES:
If you're asked for "4-modda" (definitions article) and you only find 1-2 definitions:
1. This is clearly INCOMPLETE - Article 4 typically has 15-20+ definitions
2. Search AGAIN with query like: "asosiy tushunchalar davlat xaridlari definitions" OR "benefitsiar mulkdor davlat buyurtmachisi"
3. Combine results from BOTH searches
4. If still incomplete after second search, inform user: "Article 4 appears to be incomplete in the database. Found only [N] definitions. Please re-upload the document."

Remember: You are copying a COMPLETE legal document. Every word matters. Missing even one sentence is unacceptable! READ ALL CHUNKS and generate LONG, COMPLETE responses!"""

RAG_TOOLS = [{
    "type": "function",
    "function": {
        "name": "search_documents",
        "description": """Search user's uploaded legal documents and retrieve COMPLETE articles.

⚠️ IMPORTANT: Before calling this tool, check if the user's query is SPECIFIC or AMBIGUOUS:
- AMBIGUOUS (just article number): Ask user to specify which law/resolution first
- SPECIFIC (mentions law name): Call this tool immediately

⚠️ CRITICAL: This tool returns up to 20 chunks of text. You MUST use ALL retrieved chunks in your answer!

How it works:
- Hybrid search combines semantic similarity (vector embeddings) with exact keyword matching (full-text search)
- Uses Reciprocal Rank Fusion (RRF) to merge and rank results
- Returns the MOST RELEVANT 20 chunks about the query

After calling this tool - YOU MUST:
1. Receive and examine ALL 20 chunks
2. Look at [Source: filename] tags to identify which law/document each chunk is from
3. If chunks are from the SAME law - combine ALL of them into ONE complete response
4. If chunks are from DIFFERENT laws - show ALL laws separately with clear labels
5. Use EVERY SINGLE chunk - don't stop after reading just a few
6. Copy text EXACTLY from ALL relevant chunks
7. Generate LONG, COMPLETE answers (typically 500-3000+ words for legal articles)

REMEMBER: Large legal articles are split across multiple chunks. You MUST combine ALL chunks that belong to the same article!

Supports metadata filtering (optional):
- document_type, topics, programming_languages, frameworks_tools, technical_level
Use filters when user mentions specific document types or technologies.""",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find relevant document content"
                },
                "metadata_filters": {
                    "type": "object",
                    "description": "Optional JSONB metadata filters to narrow search results",
                    "properties": {
                        "document_type": {
                            "type": "string",
                            "enum": ["tutorial", "guide", "reference", "blog_post", "research_paper", "documentation", "report", "other"]
                        },
                        "topics": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "programming_languages": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "frameworks_tools": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "technical_level": {
                            "type": "string",
                            "enum": ["beginner", "intermediate", "advanced", "expert"]
                        }
                    }
                }
            },
            "required": ["query"]
        }
    }
}]


def get_global_llm_settings() -> dict[str, Any]:
    """
    Get global LLM settings from the global_settings table.
    Falls back to environment variables if global_settings is not configured.

    Returns dict with keys: model, base_url, api_key
    Raises HTTPException(503) if no API key is configured.
    """
    from app.config import get_settings

    supabase = get_supabase_client()
    api_key = None
    model = None
    base_url = None

    try:
        result = supabase.table("global_settings").select(
            "llm_model, llm_base_url, llm_api_key"
        ).limit(1).maybe_single().execute()

        data = result.data if result else None
        if data:
            api_key = decrypt_value(data.get("llm_api_key"))
            model = data.get("llm_model")
            base_url = data.get("llm_base_url")
    except Exception:
        # Table doesn't exist or query failed - will fall back to env vars
        pass

    # Fallback to environment variables
    if not api_key:
        settings = get_settings()
        api_key = settings.llm_api_key or settings.openai_api_key
        model = model or settings.llm_model
        base_url = base_url or settings.llm_base_url or None

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM not configured. Set LLM_API_KEY in .env or configure via Settings UI."
        )

    return {
        "model": model or "gpt-4o",
        "base_url": base_url,
        "api_key": api_key,
    }


async def astream_chat_response(
    messages: list[dict],
    tools: list[dict] | None = None,
    user_id: str | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Stream a chat response using the ChatCompletions API.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
        tools: Optional list of tool definitions for function calling
        user_id: Unused, kept for API compatibility

    Yields:
        Event dicts with 'type' and additional data
    """
    import logging
    logger = logging.getLogger(__name__)

    llm_settings = get_global_llm_settings()
    model = llm_settings["model"]
    client = get_traced_async_openai_client(
        base_url=llm_settings["base_url"],
        api_key=llm_settings["api_key"],
    )

    request_kwargs: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *messages],
        "stream": True,
        "max_completion_tokens": 16000,  # Maximum tokens for response generation
        "temperature": 0.0,  # Zero temperature for exact copying
    }
    if tools:
        request_kwargs["tools"] = tools

    logger.debug(f"Chat completion: model={model}, tools={len(tools) if tools else 0}")

    try:
        stream = await client.chat.completions.create(**request_kwargs)

        full_response = ""
        tool_calls_buffer: dict[int, dict] = {}

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            finish_reason = chunk.choices[0].finish_reason if chunk.choices else None

            if delta and delta.content:
                full_response += delta.content
                yield {"type": "text_delta", "content": delta.content}

            if delta and delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_buffer:
                        tool_calls_buffer[idx] = {
                            "id": tc.id,
                            "name": tc.function.name if tc.function else None,
                            "arguments": "",
                        }
                    else:
                        if tc.id:
                            tool_calls_buffer[idx]["id"] = tc.id
                        if tc.function and tc.function.name:
                            tool_calls_buffer[idx]["name"] = tc.function.name
                    if tc.function and tc.function.arguments:
                        tool_calls_buffer[idx]["arguments"] += tc.function.arguments

            if finish_reason == "tool_calls":
                yield {"type": "tool_calls", "tool_calls": list(tool_calls_buffer.values())}

            if finish_reason == "stop":
                yield {"type": "response_completed", "content": full_response}

    except HTTPException:
        raise
    except Exception as e:
        yield {"type": "error", "error": str(e)}
