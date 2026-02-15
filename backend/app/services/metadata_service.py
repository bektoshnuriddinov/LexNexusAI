"""Metadata extraction service using LLM structured outputs."""
import logging
from openai import AsyncOpenAI
from app.models.schemas import DocumentMetadata
from app.config import get_settings

logger = logging.getLogger(__name__)


async def extract_metadata(text_content: str, filename: str) -> DocumentMetadata:
    """
    Extract structured metadata from document content using LLM.

    Args:
        text_content: Full document text
        filename: Original filename (may contain hints)

    Returns:
        DocumentMetadata object with extracted fields

    Note:
        - Truncates content to first 8000 characters for cost optimization
        - Uses structured outputs via beta.chat.completions.parse
        - Returns default metadata on extraction failure
    """
    try:
        settings = get_settings()

        # Get LLM settings from global settings table
        from app.db.supabase import get_supabase_client
        supabase = get_supabase_client()

        # Query global_settings for LLM configuration
        settings_result = supabase.table("global_settings").select("*").limit(1).execute()

        if not settings_result.data:
            raise ValueError("No global LLM settings configured. Please configure settings first.")

        llm_settings = settings_result.data[0]
        llm_base_url = llm_settings.get("llm_base_url")
        llm_api_key = llm_settings.get("llm_api_key")
        llm_model = llm_settings.get("llm_model")

        # Decrypt API key if encryption is enabled
        if settings.settings_encryption_key and llm_api_key:
            try:
                from cryptography.fernet import Fernet
                f = Fernet(settings.settings_encryption_key.encode())
                llm_api_key = f.decrypt(llm_api_key.encode()).decode()
            except Exception as e:
                logger.warning(f"Failed to decrypt LLM API key: {e}")

        if not llm_base_url or not llm_api_key or not llm_model:
            raise ValueError("LLM settings incomplete. Please configure base_url, api_key, and model.")

        # Create OpenAI client
        client = AsyncOpenAI(
            base_url=llm_base_url,
            api_key=llm_api_key
        )

        # Truncate content to 8000 chars for cost optimization
        truncated_content = text_content[:8000]
        if len(text_content) > 8000:
            truncated_content += "\n\n[Content truncated for metadata extraction]"

        # Use structured outputs (beta feature)
        completion = await client.beta.chat.completions.parse(
            model=llm_model,
            messages=[{
                "role": "user",
                "content": f"""Analyze this document and extract structured metadata.

Filename: {filename}

Content:
{truncated_content}

Extract the following information:
- Document type (tutorial, guide, reference, blog_post, research_paper, documentation, report, or other)
- Main topics/subjects covered (max 5)
- Programming languages mentioned (if any)
- Frameworks, libraries, or tools mentioned (max 5)
- Date or time period references (e.g., "2023", "Q3 2024", "January 2025")
- Key entities: people, companies, or organizations (max 5)
- One-sentence summary (max 200 characters)
- Technical difficulty level (beginner, intermediate, advanced, or expert)

Be concise and accurate. If information is not present, use appropriate defaults."""
            }],
            response_format=DocumentMetadata
        )

        metadata = completion.choices[0].message.parsed
        logger.debug(f"Extracted metadata for {filename}: {metadata.document_type}, {len(metadata.topics)} topics")

        return metadata

    except Exception as e:
        logger.error(f"Metadata extraction failed for {filename}: {e}")

        # Return default metadata on failure
        return DocumentMetadata(
            document_type="other",
            topics=[],
            programming_languages=[],
            frameworks_tools=[],
            date_references=None,
            key_entities=[],
            summary=f"Document: {filename}",
            technical_level="intermediate"
        )


async def get_default_metadata(filename: str) -> DocumentMetadata:
    """Return default metadata when extraction is not possible or fails."""
    return DocumentMetadata(
        document_type="other",
        topics=[],
        programming_languages=[],
        frameworks_tools=[],
        date_references=None,
        key_entities=[],
        summary=f"Document: {filename}",
        technical_level="intermediate"
    )
