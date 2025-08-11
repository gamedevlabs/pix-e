"""
LLM Service Manager
Handles multiple LLM services and provides unified interface
"""

import os
import logging
from typing import Dict, List, Any, Optional
from django.core.cache import cache
from django.conf import settings

from .base import BaseLLMService, LLMServiceError
from .tgi_api_service import TGIAPIService
from .github_models_service import GitHubModelsService
from ..gemini.GeminiLink import GeminiLink

# Import for user token management
try:
    from accounts.models import AIServiceToken
except ImportError:
    AIServiceToken = None

logger = logging.getLogger(__name__)


class LLMServiceManager:
    """Manages multiple LLM services"""

    def __init__(self):
        self._services: Dict[str, BaseLLMService] = {}
        self._active_service: Optional[str] = None
        self._gemini_service = None

        # Initialize Gemini service if available
        try:
            if os.environ.get("GEMINI_API_KEY"):
                self._gemini_service = GeminiLink()
                logger.info("Gemini service initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Gemini service: {e}")

    def register_service(self, service_id: str, service: BaseLLMService):
        """Register a new LLM service"""
        self._services[service_id] = service

    def get_service(self, service_id: str) -> Optional[BaseLLMService]:
        """Get a registered service"""
        return self._services.get(service_id)

    def list_services(self) -> Dict[str, Dict[str, Any]]:
        """List all available services with their info"""
        services_info = {}

        # Add TGI API models - the working API models from Hugging Face
        for model_id, model_info in TGIAPIService.get_available_models().items():
            services_info[f"tgi_{model_id}"] = {
                "type": "tgi",
                "model_name": model_id,
                "provider": "Hugging Face TGI API",
                "status": "available",
                "model_url": model_info.get(
                    "model_url", f"https://huggingface.co/{model_id}"
                ),
                **model_info,
            }

        # Add GitHub Models
        for model_id, model_info in GitHubModelsService.AVAILABLE_MODELS.items():
            services_info[f"github_{model_id}"] = {
                "type": "github",
                "model_name": model_id,
                "provider": "GitHub Models (OpenAI)",
                "status": "available",
                "model_url": model_info.get(
                    "model_url", f"https://github.com/models/{model_id}"
                ),
                **model_info,
            }

        # Add Gemini service (used elsewhere in the app)
        if self._gemini_service:
            services_info["gemini"] = {
                "type": "gemini",
                "model_name": "gemini-2.0-flash",
                "provider": "Google AI",
                "name": "Gemini 2.0 Flash (Google)",
                "description": "Google's latest multimodal AI model for text generation",
                "status": "available",
            }

        # Add status for loaded services
        for service_id, service in self._services.items():
            if service_id in services_info:
                services_info[service_id]["status"] = (
                    "loaded" if service.is_model_loaded() else "available"
                )

        return services_info

    def load_service(
        self, service_id: str, model_name: str = None, user_token: str = None
    ):
        """Load a specific service and return the service instance"""
        try:
            # Check if service is already loaded
            if service_id in self._services:
                if self._services[service_id].is_model_loaded():
                    return self._services[service_id]

            # Determine service type and model
            if service_id.startswith("tgi_"):
                # TGI service - your original working models
                model_id = service_id.replace("tgi_", "")
                service = TGIAPIService(model_id, user_token=user_token)
                success = service.load_model()

                if success:
                    self.register_service(service_id, service)
                    self._active_service = service_id

                    # Cache service info
                    cache.set(
                        f"llm_service_{service_id}", service.get_model_info(), 3600
                    )

                    return service
                else:
                    raise LLMServiceError(f"Failed to load TGI service: {service_id}")

            elif service_id.startswith("github_"):
                # GitHub Models service
                model_id = service_id.replace("github_", "")
                service = GitHubModelsService(model_id, user_token=user_token)
                success = service.load_model()

                if success:
                    self.register_service(service_id, service)
                    self._active_service = service_id

                    # Cache service info
                    cache.set(
                        f"llm_service_{service_id}", service.get_model_info(), 3600
                    )

                    return service
                else:
                    raise LLMServiceError(
                        f"Failed to load GitHub Models service: {service_id}"
                    )

            elif service_id == "gemini":
                # Gemini is always "loaded" since it's API-based
                if self._gemini_service:
                    self._active_service = service_id
                    return self._gemini_service
                else:
                    raise LLMServiceError("Gemini service not available")

            else:
                raise LLMServiceError(f"Unknown service type: {service_id}")

        except Exception as e:
            logger.error(f"Failed to load service {service_id}: {e}")
            raise LLMServiceError(f"Could not load service: {e}")

    def get_service(self, service_id: str):
        """Get a loaded service instance"""
        return self._services.get(service_id)

    def unload_service(self, service_id: str) -> bool:
        """Unload a specific service"""
        try:
            if service_id in self._services:
                success = self._services[service_id].unload_model()
                if success:
                    del self._services[service_id]
                    cache.delete(f"llm_service_{service_id}")

                    if self._active_service == service_id:
                        self._active_service = None

                return success
            return True
        except Exception as e:
            logger.error(f"Failed to unload service {service_id}: {e}")
            return False

    def unload_all_services(self):
        """Unload all services"""
        for service_id in list(self._services.keys()):
            self.unload_service(service_id)
        self._active_service = None

    def _create_contextual_prompt(
        self,
        user_input: str,
        mode: str,
        num_suggestions: int,
        suggestion_type: str = "short",
    ) -> str:
        """Create a contextual prompt for generating suggestions based on type"""

        if suggestion_type.lower() == "long":
            word_count = "10-20 words each"
            format_instruction = (
                "Format as complete descriptive sentences, one per line:"
            )
        else:
            word_count = "2-8 words each"
            format_instruction = "Format as brief phrases only, one per line:"

        if mode.lower() == "gaming":
            contextual_prompt = f"""Help expand this gaming prompt: "{user_input}"

Provide {num_suggestions} creative suggestions ({word_count}) that could enhance this prompt for game art creation.

{format_instruction}"""

        else:
            contextual_prompt = f"""Help expand this artistic prompt: "{user_input}"

Provide {num_suggestions} creative suggestions ({word_count}) that could enhance this prompt for visual art creation.

{format_instruction}"""

        return contextual_prompt

    def get_suggestions(
        self,
        prompt: str,
        service_id: str = None,
        num_suggestions: int = 3,
        mode: str = "default",
        user=None,
        **kwargs,
    ) -> List[str]:
        """Get text suggestions from the specified AI service"""

        suggestion_type = kwargs.get("suggestion_type", "short")

        # Check if user has required API tokens for the service when specifically requested
        if user and service_id:
            user_token = self._get_user_token(service_id, user)
            if not user_token:
                service_name = self._get_service_display_name(service_id)
                logger.error(
                    f"No token found for service {service_id} ({service_name}) for user {user.username}"
                )
                raise LLMServiceError(
                    f"API token required for {service_name}. Please configure your API token in the AI suggestions panel."
                )

        # Try TGI models if specifically requested (your original working models)
        if service_id and service_id.startswith("tgi_"):
            try:
                # Get user token for TGI service
                user_token = self._get_user_token(service_id, user) if user else None

                # Try to load the service if not already loaded
                if service_id not in self._services:
                    service = self.load_service(service_id, user_token=user_token)
                    if not service:
                        logger.warning(f"Failed to load TGI service: {service_id}")
                        raise Exception(f"Could not load service: {service_id}")
                else:
                    service = self._services.get(service_id)
                    # Update service with user token if available
                    if user and hasattr(service, "update_token") and user_token:
                        service.update_token(user_token)

                # Get the service and generate suggestions
                if service and service.is_model_loaded():
                    contextual_prompt = self._create_contextual_prompt(
                        prompt, mode, num_suggestions, suggestion_type
                    )

                    # Extract temperature from kwargs if present, otherwise use default
                    temperature = kwargs.pop("temperature", 0.7)

                    suggestions = service.get_suggestions(
                        prompt=contextual_prompt,
                        max_tokens=50,
                        temperature=temperature,
                        num_suggestions=num_suggestions,
                        **kwargs,
                    )

                    # Clean up and validate suggestions based on suggestion_type and mode
                    cleaned_suggestions = []
                    for suggestion in suggestions:
                        if suggestion and len(suggestion.strip()) > 3:
                            suggestion_text = suggestion.strip()

                            # Remove common unwanted prefixes
                            if (
                                suggestion_text.startswith("SSH tunnel")
                                or suggestion_text.startswith("TGI")
                                or suggestion_text.startswith("Please")
                                or suggestion_text.startswith("Here are")
                                or suggestion_text.startswith("I can provide")
                            ):
                                continue

                            # Remove quotes if present
                            if suggestion_text.startswith(
                                '"'
                            ) and suggestion_text.endswith('"'):
                                suggestion_text = suggestion_text[1:-1].strip()

                            # For short suggestions, try to extract the core phrase
                            if suggestion_type == "short":
                                # If it contains a colon, take the part before the colon
                                if ":" in suggestion_text:
                                    suggestion_text = suggestion_text.split(":")[
                                        0
                                    ].strip()

                                # Remove common descriptive prefixes
                                prefixes_to_remove = [
                                    "A series of",
                                    "A collage art piece",
                                    "An abstract painting",
                                    "A painting of",
                                    "A drawing of",
                                    "An image of",
                                ]
                                for prefix in prefixes_to_remove:
                                    if suggestion_text.lower().startswith(
                                        prefix.lower()
                                    ):
                                        suggestion_text = suggestion_text[
                                            len(prefix) :
                                        ].strip()
                                        break

                                # If still too long (more than 8 words), try to shorten
                                words = suggestion_text.split()
                                if len(words) > 8:
                                    # Try to find the core descriptive phrase
                                    suggestion_text = " ".join(
                                        words[:6]
                                    )  # Take first 6 words

                            if suggestion_text and len(suggestion_text) > 3:
                                cleaned_suggestions.append(suggestion_text)

                    if cleaned_suggestions:
                        return cleaned_suggestions
                    else:
                        raise LLMServiceError(
                            f"TGI service {service_id} failed to generate valid suggestions"
                        )

            except Exception as e:
                logger.error(f"TGI service {service_id} failed: {e}")
                # Check if it's a timeout or rate limit error
                if "timed out" in str(e).lower() or "timeout" in str(e).lower():
                    raise LLMServiceError(
                        f"The TGI service timed out after 30 seconds. Please check your Hugging Face token and try again."
                    )
                elif "rate limit" in str(e).lower() or "429" in str(e):
                    raise LLMServiceError(
                        f"Rate limit exceeded for TGI service. Please check your Hugging Face token or try again later."
                    )
                else:
                    # Don't fall back - user specifically requested this service
                    raise LLMServiceError(
                        f"The TGI service ({service_id}) failed to respond. Please check your Hugging Face token and try again."
                    )

        # Try GitHub Models service if specifically requested
        if service_id and service_id.startswith("github_"):
            try:
                # Try to load the service if not already loaded
                if service_id not in self._services:
                    # Get user token if available
                    user_token = (
                        self._get_user_token(service_id, user) if user else None
                    )
                    service = self.load_service(service_id, user_token=user_token)
                    if not service:
                        logger.warning(
                            f"Failed to load GitHub Models service: {service_id}"
                        )
                        raise Exception(f"Could not load service: {service_id}")
                else:
                    service = self._services.get(service_id)
                    # Update service with user token if available
                    if user and hasattr(service, "update_token"):
                        user_token = self._get_user_token(service_id, user)
                        if user_token:
                            service.update_token(user_token)

                # Get the service and generate suggestions
                if service and service.is_model_loaded():
                    contextual_prompt = self._create_contextual_prompt(
                        prompt, mode, num_suggestions, suggestion_type
                    )
                    # Extract temperature from kwargs if present, otherwise use default
                    temperature = kwargs.pop("temperature", 0.7)

                    suggestions = service.get_suggestions(
                        prompt=contextual_prompt,
                        max_tokens=50,
                        temperature=temperature,
                        num_suggestions=num_suggestions,
                        **kwargs,
                    )

                    # Clean up and validate suggestions
                    cleaned_suggestions = []
                    for suggestion in suggestions:
                        if suggestion and len(suggestion.strip()) > 3:
                            suggestion_text = suggestion.strip()
                            cleaned_suggestions.append(suggestion_text)

                    if cleaned_suggestions:
                        return cleaned_suggestions
                    else:
                        raise LLMServiceError(
                            f"GitHub Models service {service_id} failed to generate valid suggestions"
                        )

            except Exception as e:
                logger.error(f"GitHub Models service {service_id} failed: {e}")
                # Check if it's a timeout or rate limit error
                if "timed out" in str(e).lower() or "timeout" in str(e).lower():
                    raise LLMServiceError(
                        f"The GitHub Models service timed out after 30 seconds. Please check your GitHub token and try again."
                    )
                elif "rate limit" in str(e).lower() or "429" in str(e):
                    raise LLMServiceError(
                        f"Rate limit exceeded for GitHub Models. Please check your GitHub token or try again later."
                    )
                else:
                    # Don't fall back - user specifically requested this service
                    raise LLMServiceError(
                        f"The GitHub Models service ({service_id}) failed to respond. Please check your API token and try again."
                    )

        # If no specific service requested, require user to select one
        if not service_id:
            raise LLMServiceError(
                "Please select an AI service from the dropdown menu to generate suggestions."
            )

    def get_active_service(self) -> Optional[str]:
        """Get currently active service ID"""
        return self._active_service

    def get_service_status(self, service_id: str) -> Dict[str, Any]:
        """Get status of a specific service"""
        if service_id == "gemini":
            return {
                "service_id": service_id,
                "loaded": self._gemini_service is not None,
                "type": "api",
                "provider": "Google",
            }

        elif service_id in self._services:
            service = self._services[service_id]
            return {
                "service_id": service_id,
                "loaded": service.is_model_loaded(),
                "type": "local",
                "provider": "Hugging Face",
                **service.get_model_info(),
            }

        else:
            return {
                "service_id": service_id,
                "loaded": False,
                "available": service_id in self.list_services(),
            }

    def _get_user_token(self, service_id: str, user) -> Optional[str]:
        """Get user-specific token for the service"""

        if not AIServiceToken or not user or not user.is_authenticated:
            logger.warning(
                f"Token retrieval failed: AIServiceToken={bool(AIServiceToken)}, user={bool(user)}, authenticated={user.is_authenticated if user else False}"
            )
            return None

        # Determine required service type based on service_id
        service_type_map = {
            "github_": "github",
            "tgi_": "huggingface",
            "gemini": "google",
        }

        required_service_type = None
        for prefix, service_type in service_type_map.items():
            if service_id.startswith(prefix):
                required_service_type = service_type
                break

        if not required_service_type:
            return None

        # Get user token for this service
        try:
            tokens = AIServiceToken.objects.filter(
                user=user, service_type=required_service_type, is_active=True
            )

            token = tokens.first()
            user_token = token.get_token() if token else None
            return user_token
        except Exception as e:
            logger.error(f"Error getting user token: {e}")
            return None

    def _get_service_display_name(self, service_id: str) -> str:
        """Get human-readable service name"""
        if service_id.startswith("github_"):
            return "GitHub Models"
        elif service_id.startswith("tgi_"):
            return "Hugging Face"
        elif service_id.startswith("gemini"):
            return "Google Gemini"
        else:
            return "AI Service"


# Global instance
llm_manager = LLMServiceManager()
