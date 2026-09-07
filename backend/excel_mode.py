"""
Excel Mode Handler.
Wraps the structured document planning pipeline for spreadsheet deliverables (.xlsx).
"""

from typing import AsyncGenerator, Dict, Any
from backend.docs_mode import handle_document_mode


async def handle_excel_mode(
    chat_id: str,
    user_message: str,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Executes Excel spreadsheet generation mode."""
    async for event in handle_document_mode(mode="excel", chat_id=chat_id, user_message=user_message):
        yield event
