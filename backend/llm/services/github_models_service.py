"""
GitHub Models Service Implementation
Uses GitHub Models API for text generation
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from django.conf import settings

from .base import BaseLLMService, LLMServiceError

# Add path to import prompt debugger
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
try:
    from prompt_debugger import prompt_debugger
except ImportError:
    # Fallback if prompt_debugger is not available
    class DummyDebugger:
        def log_prompt(self, *args, **kwargs):
            pass

    prompt_debugger = DummyDebugger()

logger = logging.getLogger(__name__)


class GitHubModelsService(BaseLLMService):
    """GitHub Models service for text generation"""

    # Available GitHub Models
    AVAILABLE_MODELS = {
        "openai/gpt-4.1": {
            "name": "GPT-4.1 (GitHub Models)",
            "description": (
                "OpenAI GPT-4.1 model via GitHub Models API - excellent for "
                "creative text generation with advanced reasoning"
            ),
            "endpoint": "https://models.github.ai/inference",
            "model_url": "https://github.com/models/openai/gpt-4.1",
            "size": "4.1",
            "type": "chat",
            "provider": "GitHub Models (OpenAI)",
            "requires_auth": True,
            "task": "chat",
        }
    }

    def __init__(self, model_id: str, user_token: Optional[str] = None):
        """Initialize GitHub Models service with a specific model"""
        if model_id not in self.AVAILABLE_MODELS:
            raise LLMServiceError(f"Unknown GitHub model: {model_id}")

        self.model_id: str = model_id
        self.model_info: Dict[str, Any] = self.AVAILABLE_MODELS[model_id]
        self.model_name: str = self.model_info["name"]
        self.endpoint: str = self.model_info["endpoint"]

        self.client: Optional[ChatCompletionsClient] = None
        self.is_loaded: bool = False
        self.user_provided: bool = user_token is not None  # Track if user token was provided

        # Get GitHub token - prioritize user token if provided, but don't fallback
        # to env if user was expected to provide one
        if user_token:
            self.github_token: Optional[str] = user_token
        else:
            # Only use environment token if no user context
            self.github_token = os.environ.get("GITHUB_TOKEN") or getattr(
                settings, "GITHUB_TOKEN", None
            )

        logger.info(f"Initialized GitHub Models service for {model_id}")

    def load_model(self) -> bool:
        """Load GitHub Models client"""
        try:
            requires_auth = self.model_info.get("requires_auth", True)

            if requires_auth and not self.github_token:
                raise LLMServiceError(
                    "GitHub token required for this model. "
                    "Please set GITHUB_TOKEN environment variable. "
                    "Get your token at: https://github.com/settings/tokens"
                )

            # Initialize the GitHub Models client
            if self.github_token is None:
                raise LLMServiceError("GitHub token is required but not available")
            
            self.client = ChatCompletionsClient(
                endpoint=self.endpoint, credential=AzureKeyCredential(self.github_token)
            )

            self.is_loaded = True
            logger.info(f"GitHub Models client initialized for {self.model_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to load GitHub model {self.model_id}: {str(e)}")
            raise LLMServiceError(f"Could not connect to GitHub Models: {str(e)}")

    def update_token(self, token: str):
        """Update the GitHub token for this service"""
        self.github_token = token
        if self.is_loaded:
            # Recreate the client with new token
            self.client = ChatCompletionsClient(
                endpoint=self.model_info["endpoint"],
                credential=AzureKeyCredential(token),
            )

    def unload_model(self) -> bool:
        """Unload GitHub Models client"""
        try:
            if self.client:
                self.client = None
            self.is_loaded = False
            logger.info(f"Unloaded GitHub model: {self.model_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to unload GitHub model {self.model_id}: {str(e)}")
            return False

    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        num_return_sequences: int = 3,
        suggestion_type: str = "short",
    ) -> List[str]:
        """Generate text using GitHub Models API"""
        if not self.is_loaded or not self.client:
            raise LLMServiceError(
                "GitHub Models client not loaded. Call load_model() first."
            )

        try:
            # Create different prompts based on suggestion type
            if suggestion_type == "long":
                format_instruction = (
                    "- A complete sentence (10-20 words)\n"
                    "- Descriptive and detailed\n"
                    "- Suitable for comprehensive artistic descriptions"
                )
                example_format = (
                    "1. [detailed descriptive sentence]\n"
                    "2. [another detailed descriptive sentence]\n"
                    "3. [third detailed descriptive sentence]"
                )
            else:  # short
                format_instruction = (
                    "- A short phrase (2-8 words)\n"
                    "- Unique and different from the others\n"
                    "- Creative and descriptive\n"
                    "- Suitable for artistic/visual content"
                )
                example_format = (
                    "1. [first suggestion]\n2. [second suggestion]\n"
                    "3. [third suggestion]"
                )

            # Create a single prompt that requests multiple different suggestions
            enhanced_prompt = (
                f"Please provide {num_return_sequences} different, creative "
                f'suggestions to enhance this prompt: "{prompt}"\n\n'
                f"Each suggestion should be:\n{format_instruction}\n\n"
                f"Format your response as a numbered list:\n{example_format}"
            )

            # Debug: Log the prompt being sent
            prompt_debugger.log_prompt(
                service_name="GitHub Models",
                model_name=self.model_id,
                prompt=enhanced_prompt,
                prompt_type="generation",
                temperature=temperature,
                max_tokens=max_tokens,
                num_return_sequences=num_return_sequences,
                suggestion_type=suggestion_type,
            )

            # Create messages for the chat completion
            messages = [
                SystemMessage(
                    "You are a helpful assistant that provides creative, diverse "
                    "suggestions for artistic prompts."
                ),
                UserMessage(enhanced_prompt),
            ]

            response = None

            # Use threading for timeout
            import queue
            import threading

            result_queue = queue.Queue()
            exception_queue = queue.Queue()

            def api_call():
                try:
                    api_response = self.client.complete(
                        messages=messages,
                        temperature=temperature,
                        top_p=0.9,
                        max_tokens=max_tokens,
                        model=self.model_id,
                    )
                    result_queue.put(api_response)
                except Exception as e:
                    exception_queue.put(e)

            # Start the API call in a separate thread
            thread = threading.Thread(target=api_call)
            thread.daemon = True
            thread.start()
            thread.join(timeout=30.0)  # 30 second timeout

            if thread.is_alive():
                # Timeout occurred
                logger.error("GitHub Models API request timed out after 30 seconds")
                raise LLMServiceError(
                    "Request timed out. Please check your GitHub token "
                    "or try again later."
                )

            # Check if there was an exception
            if not exception_queue.empty():
                exception = exception_queue.get()
                if hasattr(exception, "status_code") and exception.status_code == 429:
                    raise LLMServiceError(
                        "Rate limit exceeded. Please check your GitHub token "
                        "or try again later."
                    )
                raise exception

            # Get the response
            if not result_queue.empty():
                response = result_queue.get()
            else:
                raise LLMServiceError("No response received from GitHub Models API")

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
                            if clean_line.startswith('"') and clean_line.endswith('"'):
                                clean_line = clean_line[1:-1]
                            elif clean_line.startswith("[") and clean_line.endswith(
                                "]"
                            ):
                                clean_line = clean_line[1:-1]

                            if clean_line and len(clean_line) > 3:
                                suggestions.append(clean_line.strip())

                    # If we didn't get enough suggestions from parsing, try to extract
                    # from the full text
                    if len(suggestions) < num_return_sequences:
                        # Split by common delimiters and try to extract more
                        all_text = (
                            generated_text.replace("\n", " ")
                            .replace(",", "\n")
                            .replace(";", "\n")
                        )
                        for line in all_text.split("\n"):
                            line = line.strip()
                            if (
                                line
                                and len(line) > 3
                                and len(line)
                                < (100 if suggestion_type == "long" else 50)
                            ):
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

            # If no suggestions generated, raise exception to trigger fallback
            raise LLMServiceError(
                f"Unable to generate suggestions for prompt: {prompt[:50]}..."
            )

        except Exception as e:
            logger.error(f"GitHub Models text generation failed: {str(e)}")
            raise LLMServiceError(f"GitHub Models generation failed: {str(e)}")

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        info = {
            "model_name": self.model_name,
            "model_id": self.model_id,
            "endpoint": self.endpoint,
            "is_loaded": self.is_loaded,
            "has_github_token": bool(self.github_token),
            **self.model_info,
        }
        return info

    @classmethod
    def get_available_models(cls) -> Dict[str, Dict[str, Any]]:
        """Get all available GitHub models"""
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
        suggestion_type = kwargs.get("suggestion_type", "short")
        return self.generate_text(
            prompt, max_tokens, temperature, num_suggestions, suggestion_type
        )

    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.is_loaded
