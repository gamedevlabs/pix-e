"""
Ollama provider implementation for local LLM models.

This provider communicates with a local Ollama instance via HTTP API.
"""

import json
from typing import Any, Dict, List, Optional

import httpx
from pydantic import ValidationError

from llm_provider.base import (BaseProvider, ModelCapabilities, ModelDetails,
                               ProviderType)


class ProviderError(Exception):
    """Exception raised when a provider operation fails."""

    def __init__(
        self,
        provider: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.provider = provider
        self.message = message
        self.context = context or {}
        super().__init__(f"[{provider}] {message}")


class ModelUnavailableError(Exception):
    """Exception raised when a model is not available."""

    def __init__(self, model: str, provider: str, reason: str):
        self.model = model
        self.provider = provider
        self.reason = reason
        msg = f"Model '{model}' unavailable on {provider}: {reason}"
        super().__init__(msg)


class OllamaProvider(BaseProvider):
    """
    Provider for Ollama local LLM models.

    Communicates with Ollama via its REST API to:
    - List available models
    - Generate text and structured responses
    - Check model capabilities
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Ollama provider.

        Args:
            config: Configuration dict with:
                - base_url: Ollama API URL
                  (default: http://localhost:11434)
                - timeout: Request timeout in seconds (default: 60)
        """
        super().__init__(config)
        self.base_url = config.get(
            "base_url", "http://localhost:11434"
        )
        self.timeout = config.get("timeout", 60)
        self.client = httpx.Client(
            base_url=self.base_url, timeout=self.timeout
        )

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def provider_type(self) -> ProviderType:
        return "local"

    def is_available(self) -> bool:
        """Check if Ollama server is reachable."""
        if self._is_available is not None:
            return self._is_available

        try:
            response = self.client.get("/api/tags", timeout=5)
            self._is_available = response.status_code == 200
            return self._is_available
        except (httpx.RequestError, httpx.TimeoutException):
            self._is_available = False
            return False

    def list_models(self) -> List[ModelDetails]:
        """List all installed Ollama models."""
        try:
            response = self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()

            models = []
            for model_info in data.get("models", []):
                name = model_info.get("name", "")
                models.append(
                    ModelDetails(
                        name=name,
                        provider=self.provider_name,
                        type=self.provider_type,
                        capabilities=self._get_model_capabilities(
                            name, model_info
                        ),
                    )
                )

            return models
        except httpx.RequestError as e:
            raise ProviderError(
                provider="ollama", message=f"Failed to list models: {str(e)}"
            )

    def get_model_info(self, model_name: str) -> ModelDetails:
        """Get information about a specific model."""
        try:
            response = self.client.post(
                "/api/show", json={"name": model_name}
            )
            response.raise_for_status()
            model_info = response.json()

            return ModelDetails(
                name=model_name,
                provider=self.provider_name,
                type=self.provider_type,
                capabilities=self._get_model_capabilities(
                    model_name, model_info
                ),
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ModelUnavailableError(
                    model=model_name,
                    provider="ollama",
                    reason="Model not found in Ollama",
                )
            raise ProviderError(
                provider="ollama",
                message=f"Failed to get model info: {str(e)}",
                context={"model": model_name},
            )
        except httpx.RequestError as e:
            raise ProviderError(
                provider="ollama",
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
        """Generate text using Ollama."""
        try:
            options: Dict[str, Any] = {
                "temperature": temperature,
            }

            if max_tokens:
                options["num_predict"] = max_tokens

            # Add any extra options from kwargs
            if "options" in kwargs:
                options.update(kwargs["options"])

            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": options,
            }

            response = self.client.post("/api/generate", json=payload)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ModelUnavailableError(
                    model=model_name,
                    provider="ollama",
                    reason="Model not found",
                )
            raise ProviderError(
                provider="ollama",
                message=f"Generation failed: {str(e)}",
                context={"model": model_name},
            )
        except httpx.RequestError as e:
            raise ProviderError(
                provider="ollama",
                message=f"Request failed: {str(e)}",
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
        """Generate structured JSON output using Ollama."""
        try:
            # Build the prompt with JSON schema instructions
            schema_prompt = self._build_structured_prompt(
                prompt, response_schema
            )

            options: Dict[str, Any] = {
                "temperature": temperature,
            }

            if max_tokens:
                options["num_predict"] = max_tokens

            payload = {
                "model": model_name,
                "prompt": schema_prompt,
                "format": "json",  # Enable JSON mode
                "stream": False,
                "options": options,
            }

            response = self.client.post("/api/generate", json=payload)
            response.raise_for_status()

            result = response.json()
            json_response = result.get("response", "{}")

            # Parse and validate against Pydantic schema
            try:
                parsed_data = json.loads(json_response)
                if hasattr(response_schema, "model_validate"):
                    # Pydantic v2
                    return response_schema.model_validate(parsed_data)
                else:
                    # Pydantic v1 or plain dict
                    return (
                        response_schema(**parsed_data)
                        if callable(response_schema)
                        else parsed_data
                    )
            except (json.JSONDecodeError, ValidationError) as e:
                msg = f"Failed to parse structured response: {str(e)}"
                raise ProviderError(
                    provider="ollama",
                    message=msg,
                    context={"model": model_name},
                )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ModelUnavailableError(
                    model=model_name,
                    provider="ollama",
                    reason="Model not found",
                )
            msg = f"Structured generation failed: {str(e)}"
            raise ProviderError(
                provider="ollama",
                message=msg,
                context={"model": model_name},
            )
        except httpx.RequestError as e:
            raise ProviderError(
                provider="ollama",
                message=f"Request failed: {str(e)}",
                context={"model": model_name},
            )

    def _get_model_capabilities(
        self, model_name: str, model_info: Dict[str, Any]
    ) -> ModelCapabilities:
        """
        Determine model capabilities based on name and metadata.

        Ollama doesn't expose explicit capability flags, so we infer them
        from the model name and available metadata.
        """
        name_lower = model_name.lower()

        # Determine capabilities based on model characteristics
        vision_keywords = ["vision", "llava", "bakllava"]
        has_vision = any(kw in name_lower for kw in vision_keywords)

        # Most modern models support function calling
        function_keywords = [
            "llama3.1",
            "llama3.2",
            "llama3.3",
            "mistral",
            "qwen",
        ]
        has_function_calling = any(
            kw in name_lower for kw in function_keywords
        )

        # All Ollama models support JSON mode (structured output)
        has_json_strict = True

        # Try to infer context window from model info
        # Ollama doesn't always provide this, so we use common defaults
        context_window = None
        if "details" in model_info:
            # Common context windows by model family
            if "llama3" in name_lower:
                context_window = 128000 if "3.3" in name_lower else 8192
            elif "mistral" in name_lower:
                context_window = 32000
            elif "qwen" in name_lower:
                context_window = 32000

        return ModelCapabilities(
            json_strict=has_json_strict,
            vision=has_vision,
            multimodal=has_vision,
            function_calling=has_function_calling,
            min_context_window=context_window,
        )

    def _build_structured_prompt(
        self, prompt: str, response_schema: type
    ) -> str:
        """
        Build a prompt for structured JSON.

        Args:
            prompt: Original prompt
            response_schema: Pydantic model defining expected structure

        Returns:
            Enhanced prompt with JSON schema instructions
        """
        # Extract schema if it's a Pydantic model
        schema_str = ""
        if hasattr(response_schema, "model_json_schema"):
            # Pydantic v2
            schema = response_schema.model_json_schema()
            schema_str = json.dumps(schema, indent=2)
        elif hasattr(response_schema, "schema"):
            # Pydantic v1
            schema = response_schema.schema()
            schema_str = json.dumps(schema, indent=2)

        if schema_str:
            return (
                f"{prompt}\n\n"
                "You must respond with valid JSON matching this schema:\n"
                f"{schema_str}\n\n"
                "Respond only with the JSON object, "
                "no additional text or explanation."
            )
        else:
            return (
                f"{prompt}\n\n"
                "Respond with valid JSON only, "
                "no additional text or explanation."
            )

    def __del__(self):
        """Clean up HTTP client on deletion."""
        if hasattr(self, "client"):
            self.client.close()
