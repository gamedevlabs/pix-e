"""
OpenAI provider implementation for GPT models.

This provider communicates with OpenAI's API for cloud-based LLM access.
"""

import json
from typing import Any, Dict, List, Optional

from openai import OpenAI, APIError, APITimeoutError, RateLimitError as OpenAIRateLimitError
from pydantic import ValidationError

from llm_orchestrator.exceptions import (
    ModelUnavailableError,
    ProviderError,
    RateLimitError,
)
from llm_orchestrator.models.providers.base import BaseProvider, GenerationResult
from llm_orchestrator.types import ModelCapabilities, ModelDetails, ProviderType


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
        
        api_key = config.get("api_key")
        if not api_key:
            raise ProviderError(
                message="OpenAI API key is required",
                provider="openai"
            )
        
        self.client = OpenAI(
            api_key=api_key,
            organization=config.get("organization"),
            timeout=config.get("timeout", 60),
            base_url=config.get("base_url"),  # Allow custom base URL
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
                            capabilities=self._get_model_capabilities(model_id)
                        )
                    )
            
            return models
        except APIError as e:
            raise ProviderError(
                message=f"Failed to list OpenAI models: {str(e)}",
                provider="openai"
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
                capabilities=self._get_model_capabilities(model.id)
            )
        except APIError as e:
            if "does not exist" in str(e).lower() or e.status_code == 404:
                raise ModelUnavailableError(
                    message=f"Model '{model_name}' not found",
                    model_name=model_name,
                    provider="openai"
                )
            raise ProviderError(
                message=f"Failed to get model info: {str(e)}",
                provider="openai"
            )
    
    def generate_text(
        self,
        model_name: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """Generate text using OpenAI's chat completion API."""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            # Build request parameters
            params = {
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
            
            response = self.client.chat.completions.create(**params)
            
            return response.choices[0].message.content or ""
            
        except OpenAIRateLimitError as e:
            raise RateLimitError(
                message=f"OpenAI rate limit exceeded: {str(e)}",
                provider="openai"
            )
        except APITimeoutError as e:
            raise ProviderError(
                message=f"OpenAI request timed out: {str(e)}",
                provider="openai"
            )
        except APIError as e:
            if "does not exist" in str(e).lower():
                raise ModelUnavailableError(
                    message=f"Model '{model_name}' not available",
                    model_name=model_name,
                    provider="openai"
                )
            raise ProviderError(
                message=f"OpenAI generation failed: {str(e)}",
                provider="openai"
            )
    
    def generate_structured(
        self,
        model_name: str,
        prompt: str,
        response_schema: type,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> Any:
        """Generate structured JSON output using OpenAI's structured outputs."""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            # Build request parameters
            params = {
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
                        "schema": schema
                    }
                }
            else:
                # Use basic JSON mode (older models)
                params["response_format"] = {"type": "json_object"}
                # Add schema to prompt
                messages[0]["content"] = self._build_json_prompt(prompt, response_schema)
            
            response = self.client.chat.completions.create(**params)
            content = response.choices[0].message.content or "{}"
            
            # Parse and validate
            try:
                parsed_data = json.loads(content)
                if hasattr(response_schema, "model_validate"):
                    # Pydantic v2
                    return response_schema.model_validate(parsed_data)
                else:
                    # Pydantic v1 or plain dict
                    return response_schema(**parsed_data) if callable(response_schema) else parsed_data
            except (json.JSONDecodeError, ValidationError) as e:
                raise ProviderError(
                    message=f"Failed to parse structured response: {str(e)}",
                    provider="openai"
                )
                
        except OpenAIRateLimitError as e:
            raise RateLimitError(
                message=f"OpenAI rate limit exceeded: {str(e)}",
                provider="openai"
            )
        except APITimeoutError as e:
            raise ProviderError(
                message=f"OpenAI request timed out: {str(e)}",
                provider="openai"
            )
        except APIError as e:
            if "does not exist" in str(e).lower():
                raise ModelUnavailableError(
                    message=f"Model '{model_name}' not available",
                    model_name=model_name,
                    provider="openai"
                )
            raise ProviderError(
                message=f"OpenAI structured generation failed: {str(e)}",
                provider="openai"
            )
    
    def _get_model_capabilities(self, model_name: str) -> ModelCapabilities:
        """Determine capabilities for an OpenAI model."""
        # Check for exact match or prefix match
        has_json_schema = any(
            model_name == m or model_name.startswith(m)
            for m in self.JSON_SCHEMA_MODELS
        )
        
        has_vision = any(
            model_name == m or model_name.startswith(m)
            for m in self.VISION_MODELS
        )
        
        # All GPT models support function calling and basic JSON mode
        has_function_calling = True
        has_json_mode = True  # All can do JSON, but not all strict schema
        
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
            min_context_window=context_window
        )
    
    def _supports_json_schema(self, model_name: str) -> bool:
        """Check if model supports strict JSON schema mode."""
        return any(
            model_name == m or model_name.startswith(m)
            for m in self.JSON_SCHEMA_MODELS
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
        
        # OpenAI requires additionalProperties to be false for strict mode
        if "additionalProperties" not in schema:
            schema["additionalProperties"] = False
        
        return schema
    
    def _build_json_prompt(self, prompt: str, response_schema: type) -> str:
        """Build a prompt with JSON schema instructions for non-strict models."""
        schema = self._extract_json_schema(response_schema)
        schema_str = json.dumps(schema, indent=2)
        
        return f"""{prompt}

You must respond with valid JSON matching this schema:
{schema_str}

Respond only with the JSON object, no additional text."""