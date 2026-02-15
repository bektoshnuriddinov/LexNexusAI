"""Tool execution dispatcher."""
import json
import logging
from app.services.retrieval_service import search_documents

logger = logging.getLogger(__name__)


async def execute_tool_call(tool_call: dict, user_id: str) -> str:
    """
    Execute a tool call and return the result as a string.

    Args:
        tool_call: Dict with 'name' and 'arguments' keys
        user_id: The user's ID for context

    Returns:
        Tool result as a string
    """
    name = tool_call["name"]
    arguments = json.loads(tool_call["arguments"])

    if name == "search_documents":
        query = arguments.get("query", "")
        metadata_filters = arguments.get("metadata_filters")

        logger.info(f"🔧 TOOL: search_documents | Query: '{query}' | User: {user_id[:8]}...")

        results = await search_documents(query, user_id, metadata_filters=metadata_filters)

        if not results:
            logger.warning("⚠️  TOOL: No results found - returning 'No relevant documents found'")
            return "No relevant documents found."

        logger.info(f"✅ TOOL: Found {len(results)} results - formatting for LLM...")

        # Format results for LLM context
        formatted = []
        for i, r in enumerate(results, 1):
            content_preview = r['content'][:100] + "..." if len(r['content']) > 100 else r['content']
            logger.info(f"  Result {i}: similarity={r['similarity']:.3f}, "
                       f"length={len(r['content'])} chars, "
                       f"preview='{content_preview}'")
            formatted.append(
                f"[Source: {r.get('metadata', {}).get('filename', 'unknown')}] "
                f"(similarity: {r['similarity']:.2f})\n{r['content']}"
            )

        formatted_text = "\n\n---\n\n".join(formatted)
        logger.info(f"📤 TOOL: Returning {len(formatted_text)} characters of formatted text to LLM")
        return formatted_text

    logger.warning(f"Unknown tool: {name}")
    return f"Error: Unknown tool '{name}'"
