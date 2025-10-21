"""
Gemini provider implementation for Google's Gemini models.

This provider communicates with Google's Gemini API for cloud-based LLM access.
"""

import re
from typing import Any, Dict, List, Optional

from google import genai
from google.genai.errors import APIError as GeminiAPIError
from google.genai.errors import ClientError
from local_llm.base import BaseProvider
from pydantic import ValidationError

from llm.exceptions import (
    ModelUnavailableError,
    ProviderError,
    RateLimitError,
)
from llm.types import ModelCapabilities, ModelDetails, ProviderType


class GeminiProvider(BaseProvider):
    """
    Provider for Google Gemini models.

    Supports:
    - Gemini 2.0 family (gemini-2.0-flash, gemini-2.0-flash-thinking)
    - Gemini 1.5 family (gemini-1.5-pro, gemini-1.5-flash, gemini-1.5-flash-8b)
    - Gemini 1.0 family (gemini-1.0-pro)
    - Native multimodal (vision) support
    - Native Pydantic structured outputs
    """

    # Model families for capability detection
    GEMINI_2_MODELS = {
        "gemini-2.0-flash-exp",
        "gemini-2.0-flash-thinking-exp",
        "gemini-2.0-flash",
    }

    GEMINI_15_MODELS = {
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-8b",
        "gemini-1.5-flash-8b-latest",
    }

    GEMINI_10_MODELS = {
        "gemini-1.0-pro",
        "gemini-1.0-pro-latest",
    }

    # Context window sizes
    CONTEXT_WINDOWS = {
        "gemini-2.0": 1048576,  # 1M tokens
        "gemini-1.5-pro": 2097152,  # 2M tokens
        "gemini-1.5-flash": 1048576,  # 1M tokens
        "gemini-1.0-pro": 32768,  # 32K tokens
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Gemini provider.

        Args:
            config: Configuration dict with:
                - api_key: Gemini API key (required)
                - timeout: Request timeout in seconds (default: 60)
        """
        super().__init__(config)
        self._is_available: Optional[bool] = None

        api_key = config.get("api_key")
        if not api_key:
            raise ProviderError(provider="gemini", message="API key is required")

        # Initialize client (timeout will be handled per-request if needed)
        self.client = genai.Client(api_key=api_key)

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def provider_type(self) -> ProviderType:
        return "cloud"

    def is_available(self) -> bool:
        """Check if Gemini API is reachable."""
        if self._is_available is not None:
            return self._is_available

        try:
            # Try to list models as a health check
            list(self.client.models.list())
            self._is_available = True
            return True
        except Exception:
            self._is_available = False
            return False

    def list_models(self) -> List[ModelDetails]:
        """List available Gemini models."""
        try:
            models = []

            for model in self.client.models.list():
                model_name = model.name
                # Skip if name is None
                if not model_name:
                    continue

                # Extract just the model ID (remove 'models/' prefix if present)
                if "/" in model_name:
                    model_name = model_name.split("/")[-1]

                # Only include Gemini models (filter out others like Imagen, etc.)
                if model_name.startswith("gemini"):
                    models.append(
                        ModelDetails(
                            name=model_name,
                            provider=self.provider_name,
                            type=self.provider_type,
                            capabilities=self._get_model_capabilities(model_name),
                        )
                    )

            return models
        except (ClientError, GeminiAPIError) as e:
            raise ProviderError(
                provider="gemini", message=f"Failed to list models: {str(e)}"
            )

    def get_model_info(self, model_name: str) -> ModelDetails:
        """Get information about a specific Gemini model."""
        try:
            # Gemini API expects 'models/' prefix
            full_name = (
                f"models/{model_name}"
                if not model_name.startswith("models/")
                else model_name
            )
            model = self.client.models.get(model=full_name)

            # Extract clean model name
            model_name_from_api = model.name or model_name
            clean_name = (
                model_name_from_api.split("/")[-1]
                if "/" in model_name_from_api
                else model_name_from_api
            )

            return ModelDetails(
                name=clean_name,
                provider=self.provider_name,
                type=self.provider_type,
                capabilities=self._get_model_capabilities(clean_name),
            )
        except (ClientError, GeminiAPIError) as e:
            error_str = str(e).lower()
            if "not found" in error_str or "404" in error_str:
                raise ModelUnavailableError(
                    model=model_name, provider="gemini", reason="Model not found"
                )
            raise ProviderError(
                provider="gemini",
                message=f"Failed to get model info: {str(e)}",
                context={"model": model_name},
            )

    def generate_text(
        self,
        model_name: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using Gemini's API."""
        try:
            # Build generation config
            config: Dict[str, Any] = {"temperature": temperature}

            if max_tokens:
                config["max_output_tokens"] = max_tokens

            # Add optional parameters
            if "top_p" in kwargs:
                config["top_p"] = kwargs["top_p"]
            if "top_k" in kwargs:
                config["top_k"] = kwargs["top_k"]

            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,  # type: ignore[arg-type]
            )

            return response.text or ""

        except (ClientError, GeminiAPIError) as e:
            error_str = str(e).lower()

            if "quota" in error_str or "rate limit" in error_str:
                # Try to extract retry delay from error message
                retry_after = None
                if "retry in" in error_str:
                    # Extract seconds from "Please retry in 13.674307975s"
                    match = re.search(r"retry in (\d+(?:\.\d+)?)", error_str)
                    if match:
                        retry_after = int(float(match.group(1)))

                raise RateLimitError(
                    message=f"Gemini rate limit exceeded: {str(e)}",
                    retry_after_seconds=retry_after,
                    context={"provider": "gemini", "model": model_name},
                )
            elif "not found" in error_str or "404" in error_str:
                raise ModelUnavailableError(
                    model=model_name, provider="gemini", reason=str(e)
                )
            elif "timeout" in error_str:
                raise ProviderError(
                    provider="gemini",
                    message=f"Request timed out: {str(e)}",
                    context={"model": model_name},
                )
            else:
                raise ProviderError(
                    provider="gemini",
                    message=f"Generation failed: {str(e)}",
                    context={"model": model_name},
                )

    def generate_structured(
        self,
        model_name: str,
        prompt: str,
        response_schema: type,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Generate structured JSON output using Gemini's native Pydantic support.

        Gemini has excellent native support for Pydantic models - just pass the
        model directly and get back a validated instance!
        """
        try:
            # Build generation config
            config: Dict[str, Any] = {
                "temperature": temperature,
                "response_mime_type": "application/json",
                "response_schema": response_schema,  # Pydantic model directly!
            }

            if max_tokens:
                config["max_output_tokens"] = max_tokens

            # Add optional parameters
            if "top_p" in kwargs:
                config["top_p"] = kwargs["top_p"]
            if "top_k" in kwargs:
                config["top_k"] = kwargs["top_k"]

            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,  # type: ignore[arg-type]
            )

            # Gemini SDK automatically parses and validates against the Pydantic schema
            return response.parsed

        except ValidationError as e:
            raise ProviderError(
                provider="gemini",
                message=f"Failed to validate response: {str(e)}",
                context={"model": model_name},
            )
        except (ClientError, GeminiAPIError) as e:
            error_str = str(e).lower()

            if "quota" in error_str or "rate limit" in error_str:
                # Try to extract retry delay from error message
                retry_after = None
                if "retry in" in error_str:
                    # Extract seconds from "Please retry in 13.674307975s"
                    match = re.search(r"retry in (\d+(?:\.\d+)?)", error_str)
                    if match:
                        retry_after = int(float(match.group(1)))

                raise RateLimitError(
                    message=f"Gemini rate limit exceeded: {str(e)}",
                    retry_after_seconds=retry_after,
                    context={"provider": "gemini", "model": model_name},
                )
            elif "not found" in error_str or "404" in error_str:
                raise ModelUnavailableError(
                    model=model_name, provider="gemini", reason=str(e)
                )
            elif "timeout" in error_str:
                raise ProviderError(
                    provider="gemini",
                    message=f"Request timed out: {str(e)}",
                    context={"model": model_name},
                )
            else:
                raise ProviderError(
                    provider="gemini",
                    message=f"Structured generation failed: {str(e)}",
                    context={"model": model_name},
                )

    def _get_model_capabilities(self, model_name: str) -> ModelCapabilities:
        """Determine capabilities for a Gemini model."""
        # Determine model family
        is_gemini_2 = any(
            model_name.startswith(m.replace("-exp", "")) for m in self.GEMINI_2_MODELS
        )
        is_gemini_15 = any(
            model_name.startswith(m.replace("-latest", ""))
            for m in self.GEMINI_15_MODELS
        )
        is_gemini_10 = any(
            model_name.startswith(m.replace("-latest", ""))
            for m in self.GEMINI_10_MODELS
        )

        # All Gemini 1.5+ models have JSON strict, vision, and function calling
        has_json_strict = is_gemini_2 or is_gemini_15
        has_vision = is_gemini_2 or is_gemini_15
        has_function_calling = is_gemini_2 or is_gemini_15

        # Gemini 1.0 has limited capabilities
        if is_gemini_10:
            has_json_strict = True  # Basic JSON mode
            has_vision = False
            has_function_calling = False

        # Determine context window
        context_window = None
        if is_gemini_2:
            context_window = self.CONTEXT_WINDOWS["gemini-2.0"]
        elif "1.5-pro" in model_name:
            context_window = self.CONTEXT_WINDOWS["gemini-1.5-pro"]
        elif "1.5-flash" in model_name:
            context_window = self.CONTEXT_WINDOWS["gemini-1.5-flash"]
        elif is_gemini_10:
            context_window = self.CONTEXT_WINDOWS["gemini-1.0-pro"]

        return ModelCapabilities(
            json_strict=has_json_strict,
            vision=has_vision,
            multimodal=has_vision,
            function_calling=has_function_calling,
            min_context_window=context_window,
        )
