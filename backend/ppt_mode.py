"""
PowerPoint Mode Handler.
Wraps the structured document planning pipeline for presentation deliverables (.pptx).
"""

from typing import AsyncGenerator, Dict, Any
from backend.docs_mode import handle_document_mode


async def handle_ppt_mode(
    chat_id: str,
    user_message: str,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Executes PowerPoint presentation generation mode."""
    async for event in handle_document_mode(mode="ppt", chat_id=chat_id, user_message=user_message):
        yield event
