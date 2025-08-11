"""
Text Generation Inference (TGI) Service Implementation - Fixed Version
Uses Hugging Face's TGI server for high-performance text generation
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings
from huggingface_hub import AsyncInferenceClient, InferenceClient

from .base import BaseLLMService, LLMServiceError

logger = logging.getLogger(__name__)


class TGIAPIService(BaseLLMService):
    """TGI API service for text generation via Hugging Face Inference API"""

    # Updated working models that support conversational tasks
    # These models are verified to work with Hugging Face Inference API
    AVAILABLE_MODELS = {
        "mistralai/Mistral-7B-Instruct-v0.2": {
            "name": "Mistral 7B Instruct v0.2 (TGI API)",
            "description": (
                "Mistral AI's instruction-tuned model via Hugging Face TGI API "
                "- excellent for creative text generation"
            ),
            "endpoint": (
                "https://api-inference.huggingface.co/models/mistralai/"
                "Mistral-7B-Instruct-v0.2"
            ),
            "model_url": "https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2",
            "size": "7B",
            "type": "instruct",
            "provider": "Hugging Face TGI API",
            "requires_auth": True,
            "task": "conversational",
        },
        "mistralai/Mixtral-8x7B-Instruct-v0.1": {
            "name": "Mixtral 8x7B Instruct (TGI API)",
            "description": (
                "Mistral AI's mixture of experts model via Hugging Face TGI API "
                "- powerful for complex text generation"
            ),
            "endpoint": (
                "https://api-inference.huggingface.co/models/mistralai/"
                "Mixtral-8x7B-Instruct-v0.1"
            ),
            "model_url": "https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1",
            "size": "8x7B",
            "type": "instruct",
            "provider": "Hugging Face TGI API",
            "requires_auth": True,
            "task": "conversational",
        },
        "google/gemma-7b-it": {
            "name": "Gemma 7B IT (TGI API)",
            "description": "Google's instruction-tuned model via Hugging Face TGI API - reliable for text suggestions",
            "endpoint": "https://api-inference.huggingface.co/models/google/gemma-7b-it",
            "model_url": "https://huggingface.co/google/gemma-7b-it",
            "size": "7B",
            "type": "instruct",
            "provider": "Hugging Face TGI API",
            "requires_auth": True,
            "task": "conversational",
        },
    }

    def __init__(self, model_id: str, user_token: Optional[str] = None):
        """Initialize TGI service with a specific model"""
        if model_id not in self.AVAILABLE_MODELS:
            raise LLMServiceError(f"Unknown model: {model_id}")

        self.model_id = model_id
        self.model_info = self.AVAILABLE_MODELS[model_id]
        self.model_name = self.model_info["name"]
        self.endpoint = self.model_info["endpoint"]

        self.client = None
        self.async_client = None
        self.is_loaded = False

        # Prioritize user token, fallback to environment variables
        self.api_token = (
            user_token
            or os.environ.get("HF_TOKEN")
            or getattr(settings, "HF_TOKEN", None)
        )

        self.user_provided = bool(user_token)

        logger.info(
            f"Initialized TGI service for {model_id} at {self.endpoint} (user token: {'provided' if user_token else 'not provided'})"
        )

    def update_token(self, token: str):
        """Update the API token"""
        self.api_token = token
        self.user_provided = bool(token)
        # Reinitialize clients with new token
        if self.is_loaded:
            self.load_model()

    def load_model(self) -> bool:
        """Load TGI model (establish connections)"""
        try:
            requires_auth = self.model_info.get("requires_auth", True)

            if requires_auth and not self.api_token:
                raise LLMServiceError(
                    "Hugging Face API token required for this model. "
                    "Please configure your Hugging Face token in the AI suggestions panel."
                )

            # Initialize the inference client with timeout
            self.client = InferenceClient(
                model=self.model_id,  # Use model name directly, not endpoint
                token=self.api_token,
                timeout=30.0,  # 30 second timeout
            )

            self.async_client = AsyncInferenceClient(
                model=self.model_id,  # Use model name directly, not endpoint
                token=self.api_token,
            )
            # Skip connection test for now to avoid hanging
            # Test connection with improved timeout handling
            # if self.api_token or not requires_auth:
            #     test_response = self._test_connection()
            #     if test_response:
            #         self.is_loaded = True
            #         logger.info(f"Successfully connected to TGI endpoint: {self.endpoint}")
            #         return True
            #     else:
            #         # Don't fail completely - model might just be slow to respond
            #         logger.warning("Connection test failed but continuing - model may be slow to respond")
            #         self.is_loaded = True
            #         return True
            # else:
            #     # For models that don't require auth, skip connection test if no token
            #     self.is_loaded = True
            #     logger.info(f"TGI client initialized for {self.endpoint} (no auth test)")
            #     return True

            # Skip connection test entirely for now
            self.is_loaded = True
            logger.info(
                f"TGI client initialized for {self.endpoint} (connection test skipped)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to load TGI model {self.model_id}: {str(e)}")
            raise LLMServiceError(f"Could not connect to TGI endpoint: {str(e)}")

    def unload_model(self) -> bool:
        """Unload TGI model (clean up connections)"""
        try:
            if self.client:
                self.client = None
            if self.async_client:
                self.async_client = None
            self.is_loaded = False
            logger.info(f"Unloaded TGI model: {self.model_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to unload TGI model {self.model_id}: {str(e)}")
            return False

    def _test_connection(self) -> bool:
        """Test connection to TGI endpoint with improved timeout handling"""
        try:
            if not self.client:
                return False

            # Use a simple HTTP GET test first (faster than text generation)
            headers = (
                {"Authorization": f"Bearer {self.api_token}"} if self.api_token else {}
            )

            try:
                # Test if model endpoint is reachable
                response = requests.get(
                    self.endpoint, headers=headers, timeout=10  # 10 second timeout
                )

                if response.status_code == 200:
                    logger.info("Model endpoint is ready")
                    return True
                elif response.status_code == 503:
                    logger.info(
                        "Model is loading (503) - this is normal for cold start"
                    )
                    return True  # Model is loading but will be available
                else:
                    logger.warning(f"Model endpoint returned {response.status_code}")
                    return (
                        response.status_code < 500
                    )  # Client errors are ok, server errors are not

            except requests.exceptions.Timeout:
                logger.warning(
                    "Model endpoint test timed out - assuming available but slow"
                )
                return True  # Assume it's available but slow
            except Exception as e:
                logger.error(f"HTTP test failed: {e}")
                return False

        except Exception as e:
            logger.error(f"TGI connection test failed: {str(e)}")
            return False

    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        num_return_sequences: int = 3,
        suggestion_type: str = "short",
    ) -> List[str]:
        """Generate text using conversational API with improved error handling"""
        if not self.is_loaded or not self.client:
            raise LLMServiceError("TGI model not loaded. Call load_model() first.")

        try:
            # Use the prompt as-is since it comes from the manager's contextual prompt
            # The manager already formats it properly with mode and suggestion_type
            enhanced_prompt = prompt

            # Use conversational API since these models support that task
            try:
                # Format as a conversation message
                messages = [{"role": "user", "content": enhanced_prompt}]

                # Use threading for timeout on Windows-compatible approach
                import queue
                import threading

                result_queue = queue.Queue()
                exception_queue = queue.Queue()

                def api_call():
                    try:
                        response = self.client.chat_completion(
                            messages=messages,
                            max_tokens=max_tokens,
                            temperature=temperature,
                            stream=False,
                        )
                        result_queue.put(response)
                    except Exception as e:
                        exception_queue.put(e)

                # Start the API call in a separate thread
                thread = threading.Thread(target=api_call)
                thread.daemon = True
                thread.start()
                thread.join(timeout=30.0)  # 30 second timeout

                if thread.is_alive():
                    # Timeout occurred
                    logger.error("API request timed out after 30 seconds")
                    raise LLMServiceError(
                        "Request timed out. Please check your API token or try again later."
                    )

                # Check if there was an exception
                if not exception_queue.empty():
                    raise exception_queue.get()

                # Get the response
                if not result_queue.empty():
                    response = result_queue.get()
                else:
                    raise LLMServiceError("No response received from API")

                if response and response.choices:
                    generated_text = response.choices[0].message.content
                    if generated_text and generated_text.strip():
                        # Parse the numbered list response
                        suggestions = []
                        lines = generated_text.strip().split("\n")

                        for line in lines:
                            line = line.strip()
                            if line and (line[0].isdigit() or line.startswith("-")):
                                # Remove numbering (1., 2., 3., etc.) or bullet points
                                clean_line = line
                                if ". " in clean_line and clean_line[0].isdigit():
                                    clean_line = clean_line.split(". ", 1)[1]
                                elif line.startswith("- "):
                                    clean_line = line[2:]
                                elif line.startswith("* "):
                                    clean_line = line[2:]

                                # Remove quotes if present
                                if clean_line.startswith('"') and clean_line.endswith(
                                    '"'
                                ):
                                    clean_line = clean_line[1:-1]
                                elif clean_line.startswith("[") and clean_line.endswith(
                                    "]"
                                ):
                                    clean_line = clean_line[1:-1]

                                if clean_line and len(clean_line) > 3:
                                    suggestions.append(clean_line.strip())

                        # If we didn't get enough suggestions from parsing, try to
                        # extract from the full text
                        if len(suggestions) < num_return_sequences:
                            # Split by common delimiters and try to extract more
                            all_text = (
                                generated_text.replace("\n", " ")
                                .replace(",", "\n")
                                .replace(";", "\n")
                            )
                            for line in all_text.split("\n"):
                                line = line.strip()
                                if line and len(line) > 3 and len(line) < 50:
                                    # Remove common prefixes
                                    for prefix in [
                                        "with",
                                        "featuring",
                                        "including",
                                        "showing",
                                    ]:
                                        if line.startswith(prefix + " "):
                                            line = line[len(prefix) + 1 :]
                                            break

                                    if (
                                        line not in suggestions
                                        and len(suggestions) < num_return_sequences
                                    ):
                                        suggestions.append(line)

                        # Ensure we have exactly the requested number of suggestions
                        if len(suggestions) > num_return_sequences:
                            suggestions = suggestions[:num_return_sequences]

                        if suggestions:
                            return suggestions

            except Exception as e:
                logger.warning(f"Conversational generation failed: {e}")
                # Try fallback with text generation if conversational fails
                try:
                    response = self.client.text_generation(
                        enhanced_prompt,
                        max_new_tokens=max_tokens,
                        temperature=temperature,
                        do_sample=True,
                        return_full_text=False,
                    )

                    if response and response.strip():
                        # Try to parse the response similar to above
                        suggestions = []
                        lines = response.strip().split("\n")

                        for line in lines:
                            line = line.strip()
                            if line and (line[0].isdigit() or line.startswith("-")):
                                clean_line = line
                                if ". " in clean_line and clean_line[0].isdigit():
                                    clean_line = clean_line.split(". ", 1)[1]
                                elif line.startswith("- "):
                                    clean_line = line[2:]

                                if clean_line and len(clean_line) > 3:
                                    suggestions.append(clean_line.strip())

                        if suggestions:
                            return suggestions[:num_return_sequences]

                except Exception as e2:
                    logger.warning(f"Fallback generation failed: {e2}")

            # If no suggestions generated, raise exception to trigger fallback
            raise LLMServiceError(
                f"Unable to generate suggestions for prompt: {prompt[:50]}..."
            )

        except Exception as e:
            logger.error(f"TGI text generation failed: {str(e)}")
            raise LLMServiceError(f"TGI generation failed: {str(e)}")

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        info = {
            "model_name": self.model_name,
            "model_id": self.model_id,
            "endpoint": self.endpoint,
            "is_loaded": self.is_loaded,
            "has_api_token": bool(self.api_token),
            **self.model_info,
        }
        return info

    @classmethod
    def get_available_models(cls) -> Dict[str, Dict[str, Any]]:
        """Get all available TGI models"""
        return cls.AVAILABLE_MODELS

    def get_suggestions(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        num_suggestions: int = 3,
        **kwargs,
    ) -> List[str]:
        """Get text suggestions (alias for generate_text for compatibility)"""
        # Extract suggestion_type if provided but ignore it for now
        kwargs.get("suggestion_type", "short")

        return self.generate_text(prompt, max_tokens, temperature, num_suggestions)

    def is_model_loaded(self) -> bool:
        """Check if model is loaded (alias for is_loaded for compatibility)"""
        return self.is_loaded
