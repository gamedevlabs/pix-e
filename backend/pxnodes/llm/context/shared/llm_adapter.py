"""
DEPRECATED — import from ``llm.llm_adapter`` instead.

This file is a backwards-compatibility shim. It re-exports from the
canonical location at ``llm.llm_adapter``.

The canonical location is documented in ``backend/llm/CONTRACT.md`` (Rule 3).
"""

import warnings

from llm.llm_adapter import LLMProviderAdapter, create_llm_provider  # noqa: F401

warnings.warn(
    "Import from 'pxnodes.llm.context.shared.llm_adapter' is deprecated. "
    "Use 'from llm.llm_adapter import LLMProviderAdapter, create_llm_provider' instead.",
    DeprecationWarning,
    stacklevel=2,
)
