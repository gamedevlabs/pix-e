"""
OpenAI provider implementation for GPT models.

This provider communicates with OpenAI's API for cloud-based LLM access.
"""

import copy
import json
from typing import Any, Dict, List, Optional

from openai import (
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    OpenAI,
)
from openai import RateLimitError as OpenAIRateLimitError
from pydantic import ValidationError

from llm.exceptions import (
    ModelUnavailableError,
    ProviderError,
    RateLimitError,
)
from llm.providers.base import BaseProvider, StructuredResult
from llm.types import ModelCapabilities, ModelDetails, ProviderType


class OpenAIProvider(BaseProvider):
    """
    Provider for OpenAI GPT models.

    Supports:
    - GPT-4 family (gpt-4, gpt-4-turbo, gpt-4o, gpt-4o-mini)
    - GPT-3.5 family (gpt-3.5-turbo)
    - Vision models (gpt-4o, gpt-4-turbo)
    - Structured outputs with JSON schema
    """

    # Models with native JSON schema support (strict mode)
    JSON_SCHEMA_MODELS = {
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4-turbo-2024-04-09",
        "gpt-4-turbo",
    }

    # Vision-capable models
    VISION_MODELS = {
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4-vision-preview",
    }

    # Context window sizes
    CONTEXT_WINDOWS = {
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
        "gpt-4-turbo": 128000,
        "gpt-4": 8192,
        "gpt-3.5-turbo": 16385,
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenAI provider.

        Args:
            config: Configuration dict with:
                - api_key: OpenAI API key (required)
                - organization: OpenAI organization ID (optional)
                - timeout: Request timeout in seconds (default: 60)
                - base_url: API base URL (optional, for compatible APIs)
        """
        super().__init__(config)
        self._is_available: Optional[bool] = None

        api_key = config.get("api_key")
        if not api_key:
            raise ProviderError(provider="openai", message="API key is required")

        self.client = OpenAI(
            api_key=api_key,
            organization=config.get("organization"),
            timeout=config.get("timeout", 60),
            base_url=config.get("base_url"),  # Allow custom base URL
        )

        # Async client for parallel execution
        self.async_client = AsyncOpenAI(
            api_key=api_key,
            organization=config.get("organization"),
            timeout=config.get("timeout", 60),
            base_url=config.get("base_url"),
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def provider_type(self) -> ProviderType:
        return "cloud"

    def is_available(self) -> bool:
        """Check if OpenAI API is reachable."""
        if self._is_available is not None:
            return self._is_available

        try:
            # Try to list models as a health check
            self.client.models.list()
            self._is_available = True
            return True
        except Exception:
            self._is_available = False
            return False

    def list_models(self) -> List[ModelDetails]:
        """List available OpenAI models (filters for GPT models only)."""
        try:
            response = self.client.models.list()
            models = []

            for model in response.data:
                model_id = model.id
                # Only include GPT models
                if model_id.startswith(("gpt-4", "gpt-3.5")):
                    models.append(
                        ModelDetails(
                            name=model_id,
                            provider=self.provider_name,
                            type=self.provider_type,
                            capabilities=self._get_model_capabilities(model_id),
                        )
                    )

            return models
        except APIError as e:
            raise ProviderError(
                provider="openai", message=f"Failed to list models: {str(e)}"
            )

    def get_model_info(self, model_name: str) -> ModelDetails:
        """Get information about a specific OpenAI model."""
        try:
            # OpenAI doesn't have a direct "get model" endpoint,
            # so we retrieve from the list or use known capabilities
            model = self.client.models.retrieve(model_name)

            return ModelDetails(
                name=model.id,
                provider=self.provider_name,
                type=self.provider_type,
                capabilities=self._get_model_capabilities(model.id),
            )
        except APIError as e:
            if (
                "does not exist" in str(e).lower()
                or getattr(e, "status_code", None) == 404
            ):
                raise ModelUnavailableError(
                    model=model_name, provider="openai", reason="Model not found"
                )
            raise ProviderError(
                provider="openai",
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
        """Generate text using OpenAI's chat completion API."""
        try:
            messages = [{"role": "user", "content": prompt}]

            # Build request parameters
            params: Dict[str, Any] = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                params["max_tokens"] = max_tokens

            # Add optional parameters
            if "top_p" in kwargs:
                params["top_p"] = kwargs["top_p"]
            if "seed" in kwargs:
                params["seed"] = kwargs["seed"]

            # type: ignore[arg-type]
            response = self.client.chat.completions.create(**params)

            return response.choices[0].message.content or ""

        except OpenAIRateLimitError as e:
            raise RateLimitError(
                message=f"OpenAI rate limit exceeded: {str(e)}",
                context={"provider": "openai", "model": model_name},
            )
        except APITimeoutError as e:
            raise ProviderError(
                provider="openai",
                message=f"Request timed out: {str(e)}",
                context={"model": model_name},
            )
        except APIError as e:
            if "does not exist" in str(e).lower():
                raise ModelUnavailableError(
                    model=model_name, provider="openai", reason=str(e)
                )
            raise ProviderError(
                provider="openai",
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
        """Generate structured JSON output using OpenAI's structured outputs."""
        try:
            messages = [{"role": "user", "content": prompt}]

            # Build request parameters
            params: Dict[str, Any] = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                params["max_tokens"] = max_tokens

            # Add optional parameters
            if "top_p" in kwargs:
                params["top_p"] = kwargs["top_p"]
            if "seed" in kwargs:
                params["seed"] = kwargs["seed"]

            # Determine JSON mode strategy
            if self._supports_json_schema(model_name):
                # Use strict JSON schema mode (newer models)
                schema = self._extract_json_schema(response_schema)
                params["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "response",
                        "strict": True,
                        "schema": schema,
                    },
                }
            else:
                # Use basic JSON mode (older models)
                params["response_format"] = {"type": "json_object"}
                # Add schema to prompt
                messages[0]["content"] = self._build_json_prompt(
                    prompt, response_schema
                )

            # type: ignore[arg-type]
            response = self.client.chat.completions.create(**params)
            content = response.choices[0].message.content or "{}"

            # Strip markdown code blocks if present
            content = self._strip_markdown_json(content)

            # Extract token usage
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0

            # Parse and validate
            try:
                parsed_data = json.loads(content)
                if hasattr(response_schema, "model_validate"):
                    # Pydantic v2
                    validated = response_schema.model_validate(parsed_data)
                else:
                    # Pydantic v1 or plain dict
                    validated = (
                        response_schema(**parsed_data)
                        if callable(response_schema)
                        else parsed_data
                    )

                # Return with token tracking
                return StructuredResult(
                    data=validated,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    model=model_name,
                    provider="openai",
                )
            except (json.JSONDecodeError, ValidationError) as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(
                    f"Failed to parse structured response from {model_name}: {str(e)}\n"
                    f"Raw content (first 500 chars): {content[:500]}"
                )
                raise ProviderError(
                    provider="openai",
                    message=f"Failed to parse structured response: {str(e)}",
                    context={"model": model_name, "content_preview": content[:200]},
                )

        except OpenAIRateLimitError as e:
            raise RateLimitError(
                message=f"OpenAI rate limit exceeded: {str(e)}",
                context={"provider": "openai", "model": model_name},
            )
        except APITimeoutError as e:
            raise ProviderError(
                provider="openai",
                message=f"Request timed out: {str(e)}",
                context={"model": model_name},
            )
        except APIError as e:
            if "does not exist" in str(e).lower():
                raise ModelUnavailableError(
                    model=model_name, provider="openai", reason=str(e)
                )
            raise ProviderError(
                provider="openai",
                message=f"Structured generation failed: {str(e)}",
                context={"model": model_name},
            )

    async def generate_structured_async(
        self,
        model_name: str,
        prompt: str,
        response_schema: type,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        """Generate structured JSON output asynchronously for parallel execution."""
        try:
            messages = [{"role": "user", "content": prompt}]

            params: Dict[str, Any] = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                params["max_tokens"] = max_tokens

            if "top_p" in kwargs:
                params["top_p"] = kwargs["top_p"]
            if "seed" in kwargs:
                params["seed"] = kwargs["seed"]

            if self._supports_json_schema(model_name):
                schema = self._extract_json_schema(response_schema)
                params["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "response",
                        "strict": True,
                        "schema": schema,
                    },
                }
            else:
                params["response_format"] = {"type": "json_object"}
                messages[0]["content"] = self._build_json_prompt(
                    prompt, response_schema
                )

            # Use async client
            response = await self.async_client.chat.completions.create(**params)
            content = response.choices[0].message.content or "{}"

            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0

            # Strip markdown code blocks if present
            content = self._strip_markdown_json(content)

            try:
                parsed_data = json.loads(content)
                if hasattr(response_schema, "model_validate"):
                    validated = response_schema.model_validate(parsed_data)
                else:
                    validated = (
                        response_schema(**parsed_data)
                        if callable(response_schema)
                        else parsed_data
                    )

                return StructuredResult(
                    data=validated,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    model=model_name,
                    provider="openai",
                )
            except (json.JSONDecodeError, ValidationError) as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(
                    f"Failed to parse structured response from {model_name}: {str(e)}\n"
                    f"Raw content (first 500 chars): {content[:500]}"
                )
                raise ProviderError(
                    provider="openai",
                    message=f"Failed to parse structured response: {str(e)}",
                    context={"model": model_name, "content_preview": content[:200]},
                )

        except OpenAIRateLimitError as e:
            raise RateLimitError(
                message=f"OpenAI rate limit exceeded: {str(e)}",
                context={"provider": "openai", "model": model_name},
            )
        except APITimeoutError as e:
            raise ProviderError(
                provider="openai",
                message=f"Request timed out: {str(e)}",
                context={"model": model_name},
            )
        except APIError as e:
            if "does not exist" in str(e).lower():
                raise ModelUnavailableError(
                    model=model_name, provider="openai", reason=str(e)
                )
            raise ProviderError(
                provider="openai",
                message=f"Structured generation failed: {str(e)}",
                context={"model": model_name},
            )

    def _get_model_capabilities(self, model_name: str) -> ModelCapabilities:
        """Determine capabilities for an OpenAI model."""
        # Check for exact match or prefix match
        has_json_schema = any(
            model_name == m or model_name.startswith(m) for m in self.JSON_SCHEMA_MODELS
        )

        has_vision = any(
            model_name == m or model_name.startswith(m) for m in self.VISION_MODELS
        )

        # All GPT models support function calling
        has_function_calling = True

        # Determine context window
        context_window = None
        for model_prefix, window_size in self.CONTEXT_WINDOWS.items():
            if model_name.startswith(model_prefix):
                context_window = window_size
                break

        return ModelCapabilities(
            json_strict=has_json_schema,
            vision=has_vision,
            multimodal=has_vision,
            function_calling=has_function_calling,
            min_context_window=context_window,
        )

    def _supports_json_schema(self, model_name: str) -> bool:
        """Check if model supports strict JSON schema mode."""
        return any(
            model_name == m or model_name.startswith(m) for m in self.JSON_SCHEMA_MODELS
        )

    def _extract_json_schema(self, response_schema: type) -> Dict[str, Any]:
        """Extract JSON schema from Pydantic model."""
        if hasattr(response_schema, "model_json_schema"):
            # Pydantic v2
            schema = response_schema.model_json_schema()
        elif hasattr(response_schema, "schema"):
            # Pydantic v1
            schema = response_schema.schema()
        else:
            # Fallback to basic object schema
            schema = {"type": "object"}

        # Make a deep copy to avoid mutating the original schema
        schema = copy.deepcopy(schema)

        # OpenAI requires additionalProperties=false at ALL levels for strict mode
        return self._add_additional_properties(schema)

    def _add_additional_properties(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively add additionalProperties=false to all objects in schema."""
        if isinstance(schema, dict):
            # If this is an object type OR has properties (implicit object), add additionalProperties  # noqa: E501
            if schema.get("type") == "object" or "properties" in schema:
                if "additionalProperties" not in schema:
                    schema["additionalProperties"] = False

                # Recursively process properties
                if "properties" in schema:
                    for prop_name, prop_schema in schema["properties"].items():
                        schema["properties"][prop_name] = (
                            self._add_additional_properties(prop_schema)
                        )

            # Handle arrays
            elif schema.get("type") == "array":
                if "items" in schema:
                    schema["items"] = self._add_additional_properties(schema["items"])

            # Handle anyOf, oneOf, allOf
            for key in ["anyOf", "oneOf", "allOf"]:
                if key in schema:
                    schema[key] = [
                        self._add_additional_properties(s) for s in schema[key]
                    ]

            # Handle $defs or definitions (common in Pydantic schemas)
            for key in ["$defs", "definitions"]:
                if key in schema:
                    for def_name, def_schema in schema[key].items():
                        schema[key][def_name] = self._add_additional_properties(
                            def_schema
                        )

        return schema

    def _strip_markdown_json(self, content: str) -> str:
        """Strip markdown code blocks from JSON content if present."""
        content = content.strip()
        # Remove markdown code blocks (```json ... ``` or ``` ... ```)
        if content.startswith("```"):
            # Find the first newline after ```
            start_idx = content.find("\n")
            if start_idx != -1:
                content = content[start_idx + 1 :]
            # Remove trailing ```
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
        return content

    def _build_json_prompt(self, prompt: str, response_schema: type) -> str:
        """Build a prompt with JSON schema instructions for non-strict models."""
        schema = self._extract_json_schema(response_schema)
        schema_str = json.dumps(schema, indent=2)

        return f"""{prompt}

        You must respond with valid JSON matching this schema:
        {schema_str}

        Respond only with the JSON object, no additional text."""
