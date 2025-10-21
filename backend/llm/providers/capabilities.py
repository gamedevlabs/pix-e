"""
Model capability utilities for the LLM Orchestrator.

Provides helpers for matching models based on capabilities and requirements.
"""

from typing import List, Optional

from llm.types import CapabilityRequirements, ModelDetails


def matches_requirements(
    model: ModelDetails, requirements: CapabilityRequirements
) -> bool:
    """
    Check if a model meets capability requirements.
    """
    caps = model.capabilities

    # Check vision requirement
    if requirements.vision and not caps.vision:
        return False

    # Check multimodal requirement
    if requirements.multimodal and not caps.multimodal:
        return False

    # Check function calling requirement
    if requirements.function_calling and not caps.function_calling:
        return False

    # Check JSON strict requirement
    if requirements.json_strict and not caps.json_strict:
        return False

    # Check minimum context window
    if requirements.min_context_window:
        if (
            not caps.min_context_window
            or caps.min_context_window < requirements.min_context_window
        ):
            return False

    return True


def filter_by_capabilities(
    models: List[ModelDetails], requirements: CapabilityRequirements
) -> List[ModelDetails]:
    """
    Filter models that meet capability requirements.
    """
    return [m for m in models if matches_requirements(m, requirements)]


def find_best_model(
    models: List[ModelDetails],
    requirements: CapabilityRequirements,
    prefer_local: bool = False,
) -> Optional[ModelDetails]:
    """
    Find the best model matching requirements.

    Selection criteria (in order):
    1. Meets all capability requirements
    2. Prefers local models if prefer_local=True
    3. Prefers models with larger context windows
    """
    matching = filter_by_capabilities(models, requirements)

    if not matching:
        return None

    # Sort by preference
    def sort_key(model: ModelDetails):
        # Prefer local if requested (high weight)
        local_score = 1000000 if (prefer_local and model.type == "local") else 0
        # Prefer larger context windows
        context_score = model.capabilities.min_context_window or 0
        return local_score + context_score

    return max(matching, key=sort_key)


def rank_models(
    models: List[ModelDetails],
    requirements: CapabilityRequirements,
    prefer_local: bool = False,
) -> List[ModelDetails]:
    """
    Rank models by how well they match requirements.

    Returns models sorted by:
    1. Local vs cloud (if prefer_local=True)
    2. Context window size
    """
    matching = filter_by_capabilities(models, requirements)

    def sort_key(model: ModelDetails):
        local_score = 1000000 if (prefer_local and model.type == "local") else 0
        context_score = model.capabilities.min_context_window or 0
        return local_score + context_score

    return sorted(matching, key=sort_key, reverse=True)


def get_capability_summary(models: List[ModelDetails]) -> dict:
    """
    Get summary of capabilities across all models.
    """
    total = len(models)
    if total == 0:
        return {
            "total_models": 0,
            "with_json_strict": 0,
            "with_vision": 0,
            "with_function_calling": 0,
            "max_context_window": 0,
            "local_models": 0,
            "cloud_models": 0,
        }

    return {
        "total_models": total,
        "with_json_strict": sum(1 for m in models if m.capabilities.json_strict),
        "with_vision": sum(1 for m in models if m.capabilities.vision),
        "with_multimodal": sum(1 for m in models if m.capabilities.multimodal),
        "with_function_calling": sum(
            1 for m in models if m.capabilities.function_calling
        ),
        "max_context_window": max(
            (
                m.capabilities.min_context_window
                for m in models
                if m.capabilities.min_context_window
            ),
            default=0,
        ),
        "avg_context_window": (
            (
                sum(
                    m.capabilities.min_context_window
                    for m in models
                    if m.capabilities.min_context_window
                )
                // sum(1 for m in models if m.capabilities.min_context_window)
            )
            if any(m.capabilities.min_context_window for m in models)
            else 0
        ),
        "local_models": sum(1 for m in models if m.type == "local"),
        "cloud_models": sum(1 for m in models if m.type == "cloud"),
    }


def get_models_with_capability(
    models: List[ModelDetails], capability: str
) -> List[ModelDetails]:
    """
    Get all models that have a specific capability.
    """
    result = []
    for model in models:
        caps = model.capabilities
        if hasattr(caps, capability) and getattr(caps, capability):
            result.append(model)
    return result


def compare_capabilities(model1: ModelDetails, model2: ModelDetails) -> dict:
    """
    Compare capabilities between two models.
    """
    caps1 = model1.capabilities
    caps2 = model2.capabilities

    # Count capabilities
    score1 = sum(
        [
            bool(caps1.json_strict),
            bool(caps1.vision),
            bool(caps1.multimodal),
            bool(caps1.function_calling),
        ]
    )

    score2 = sum(
        [
            bool(caps2.json_strict),
            bool(caps2.vision),
            bool(caps2.multimodal),
            bool(caps2.function_calling),
        ]
    )

    return {
        "model1": model1.name,
        "model2": model2.name,
        "model1_score": score1,
        "model2_score": score2,
        "better_model": (
            model1.name
            if score1 > score2
            else (model2.name if score2 > score1 else "tie")
        ),
        "differences": {
            "json_strict": (caps1.json_strict, caps2.json_strict),
            "vision": (caps1.vision, caps2.vision),
            "multimodal": (caps1.multimodal, caps2.multimodal),
            "function_calling": (caps1.function_calling, caps2.function_calling),
            "context_window": (caps1.min_context_window, caps2.min_context_window),
        },
    }
