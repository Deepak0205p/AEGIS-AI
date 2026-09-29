"""
Config-Driven Model Registry and Capabilities Resolver.
Reads model definitions, capabilities, and resource costs from data/models_registry.json.
Allows adding new open-weight models without modifying routing code.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field

from backend.config import logger

REGISTRY_PATH = Path(__file__).resolve().parent / "data" / "models_registry.json"

class ModelDefinition(BaseModel):
    model_id: str
    display_name: str
    capabilities: List[str]
    priority: int = 1
    resource_cost: str = "medium"
    context_window: int = 8192
    default_temperature: float = 0.5
    fallback_model_id: Optional[str] = None


class ModelRegistry:
    def __init__(self, config_path: Path = REGISTRY_PATH):
        self.config_path = config_path
        self._models: Dict[str, ModelDefinition] = {}
        self.load()

    def load(self):
        """Loads model definitions from models_registry.json."""
        if not self.config_path.exists():
            logger.warning(f"[REGISTRY] Configuration file not found at {self.config_path}")
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._models.clear()
            for m in data.get("models", []):
                model_def = ModelDefinition(**m)
                self._models[model_def.model_id] = model_def
            logger.info(f"[REGISTRY] Loaded {len(self._models)} models from {self.config_path.name}")
        except Exception as e:
            logger.error(f"[REGISTRY] Error loading models registry: {e}")

    def get_all_models(self) -> List[ModelDefinition]:
        return list(self._models.values())

    def get_model(self, model_id: str) -> Optional[ModelDefinition]:
        return self._models.get(model_id)

    def get_best_model_for_capability(
        self,
        capability: str,
        exclude_models: Optional[List[str]] = None
    ) -> Optional[ModelDefinition]:
        """
        Finds the highest priority (lowest priority integer) model matching the capability tag.
        """
        exclude = set(exclude_models or [])
        matching = [
            m for m in self._models.values()
            if capability in m.capabilities and m.model_id not in exclude
        ]
        if not matching:
            return None
        matching.sort(key=lambda m: (m.priority, m.model_id))
        return matching[0]

    def get_fallback_model(
        self,
        failed_model_id: str,
        capability: Optional[str] = None
    ) -> Optional[ModelDefinition]:
        """
        Resolves the fallback model for a failing model.
        1. Checks explicit fallback_model_id.
        2. If none, picks the next best model matching the capability.
        """
        model = self.get_model(failed_model_id)
        if model and model.fallback_model_id and model.fallback_model_id in self._models:
            if model.fallback_model_id != failed_model_id:
                return self._models[model.fallback_model_id]

        cap = capability or (model.capabilities[0] if model and model.capabilities else "general_reasoning")
        return self.get_best_model_for_capability(cap, exclude_models=[failed_model_id])

    def verify_all_models_present(
        self,
        available_tags: List[str]
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Verifies all models configured in models_registry.json are actually pulled locally in Ollama.
        Returns: (all_present: bool, found_models: List[str], missing_models: List[str])
        """
        found = []
        missing = []
        for model_id in self._models.keys():
            is_present = any(
                model_id == tag or model_id in tag or tag.startswith(model_id)
                for tag in available_tags
            )
            if is_present:
                found.append(model_id)
            else:
                missing.append(model_id)
        return (len(missing) == 0, found, missing)


# Global singleton registry instance
models_registry = ModelRegistry()
