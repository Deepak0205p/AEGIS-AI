"""
Temporary Context Handoff Buffer for Cross-Model Transitions.
Preserves conversation context, intermediate facts, schema details, or multimodal insights
in-memory when unloading one model from VRAM and loading a new model.
"""

import time
from typing import Dict, Any, Optional, List
from backend.config import logger


class ContextHandoffBuffer:
    """
    In-memory temporary context buffer.
    When a model swap happens (e.g. text model -> vision model, or text -> coder),
    active context/working memory is saved here and automatically injected into
    the new model's prompt/system instructions.
    """
    DEFAULT_TTL_SECONDS = 1800  # 30 minutes

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def save_handoff_context(
        self,
        chat_id: str,
        from_model: str,
        to_model: str,
        context_payload: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Saves context from previous model before it gets unloaded.
        """
        self._store[chat_id] = {
            "from_model": from_model,
            "to_model": to_model,
            "context_payload": context_payload,
            "metadata": metadata or {},
            "timestamp": time.time(),
        }
        logger.info(
            f"[CONTEXT_HANDOFF] Stored handoff context for chat_id={chat_id} "
            f"from '{from_model}' -> to '{to_model}'"
        )

    def get_handoff_context(self, chat_id: str, clear_after_read: bool = False) -> Optional[Dict[str, Any]]:
        """
        Retrieves handoff context for the given session.
        Checks TTL to prevent stale carry-over.
        """
        entry = self._store.get(chat_id)
        if not entry:
            return None

        # Check expiration
        if (time.time() - entry["timestamp"]) > self.DEFAULT_TTL_SECONDS:
            del self._store[chat_id]
            logger.info(f"[CONTEXT_HANDOFF] Expired handoff context for chat_id={chat_id}")
            return None

        if clear_after_read:
            del self._store[chat_id]
            logger.info(f"[CONTEXT_HANDOFF] Consumed and cleared handoff context for chat_id={chat_id}")

        return entry

    def clear_handoff_context(self, chat_id: str) -> None:
        """Explicitly clear context."""
        if chat_id in self._store:
            del self._store[chat_id]
            logger.info(f"[CONTEXT_HANDOFF] Cleared context for chat_id={chat_id}")

    def format_handoff_prompt_block(self, chat_id: str) -> str:
        """
        Formats handoff context into a clean system prompt injection block.
        """
        entry = self.get_handoff_context(chat_id)
        if not entry:
            return ""

        payload = entry["context_payload"]
        from_model = entry["from_model"]
        
        if isinstance(payload, str):
            content_str = payload
        elif isinstance(payload, list):
            content_str = "\n".join([str(item) for item in payload])
        elif isinstance(payload, dict):
            import json
            content_str = json.dumps(payload, indent=2)
        else:
            content_str = str(payload)

        if not content_str.strip():
            return ""

        return (
            f"--- PREVIOUS MODEL CONTEXT HANDOFF (from {from_model}) ---\n"
            f"{content_str.strip()}\n"
            f"----------------------------------------------------------"
        )


# Global singleton instance for backend
context_handoff = ContextHandoffBuffer()
