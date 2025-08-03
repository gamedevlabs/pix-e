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
from .huggingface_service import HuggingFaceLLMService
from .tgi_service import TGIService
from ..gemini.GeminiLink import GeminiLink

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
        logger.info(f"Registered LLM service: {service_id}")
    
    def get_service(self, service_id: str) -> Optional[BaseLLMService]:
        """Get a registered service"""
        return self._services.get(service_id)
    
    def list_services(self) -> Dict[str, Dict[str, Any]]:
        """List all available services with their info"""
        services_info = {}
        
        # Add TGI models (only working models with free Hugging Face API)
        for model_id, model_info in TGIService.get_available_models().items():
            services_info[f"tgi_{model_id}"] = {
                'type': 'tgi',
                'model_name': model_id,
                'provider': 'Hugging Face Inference API',
                'status': 'available',
                **model_info
            }
        
        # Local Hugging Face models disabled - only using TGI models that work with free API
        # for model_id, model_info in HuggingFaceLLMService.get_available_models().items():
        #     services_info[f"hf_{model_id.replace('/', '_')}"] = {
        #         'type': 'huggingface_local',
        #         'model_name': model_id,
        #         'provider': 'Hugging Face (Local)',
        #         'status': 'available',
        #         **model_info
        #     }
        
        # Add Gemini service (used elsewhere in the app)  
        if self._gemini_service:
            services_info['gemini'] = {
                'type': 'gemini',
                'model_name': 'gemini-2.0-flash',
                'provider': 'Google',
                'name': 'Gemini 2.0 Flash',
                'description': 'Google\'s latest multimodal AI model',
                'status': 'available'
            }
        
        # Add status for loaded services
        for service_id, service in self._services.items():
            if service_id in services_info:
                services_info[service_id]['status'] = 'loaded' if service.is_model_loaded() else 'available'
        
        return services_info
    
    def load_service(self, service_id: str, model_name: str = None) -> bool:
        """Load a specific service"""
        try:
            # Check if service is already loaded
            if service_id in self._services:
                if self._services[service_id].is_model_loaded():
                    logger.info(f"Service {service_id} already loaded")
                    return True
            
            # Determine service type and model
            if service_id.startswith('tgi_'):
                # TGI service
                model_id = service_id.replace('tgi_', '')
                service = TGIService(model_id)
                success = service.load_model()
                
                if success:
                    self.register_service(service_id, service)
                    self._active_service = service_id
                    
                    # Cache service info
                    cache.set(f"llm_service_{service_id}", service.get_model_info(), 3600)
                    
                return success
            
            elif service_id.startswith('hf_'):
                # Hugging Face local service
                actual_model_name = model_name or service_id.replace('hf_', '').replace('_', '/')
                service = HuggingFaceLLMService(actual_model_name)
                success = service.load_model()
                
                if success:
                    self.register_service(service_id, service)
                    self._active_service = service_id
                    
                    # Cache service info
                    cache.set(f"llm_service_{service_id}", service.get_model_info(), 3600)
                    
                return success
            
            elif service_id == 'gemini':
                # Gemini is always "loaded" since it's API-based
                if self._gemini_service:
                    self._active_service = service_id
                    return True
                else:
                    raise LLMServiceError("Gemini service not available")
            
            else:
                raise LLMServiceError(f"Unknown service type: {service_id}")
                
        except Exception as e:
            logger.error(f"Failed to load service {service_id}: {e}")
            raise LLMServiceError(f"Could not load service: {e}")
    
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
    
    def _create_contextual_prompt(self, user_input: str, mode: str, num_suggestions: int) -> str:
        """Create a contextual prompt for generating short prompt suggestions"""
        
        if mode.lower() == 'gaming':
            contextual_prompt = f"""Help expand this gaming prompt: "{user_input}"

Provide {num_suggestions} short, creative suggestions (2-8 words each) that could enhance this prompt for game art creation:

Examples of good suggestions:
- "with neon cyberpunk lighting"
- "dark fantasy aesthetic" 
- "pixel art style"
- "futuristic sci-fi elements"
- "retro 8-bit atmosphere"

Format as brief phrases only, one per line:"""
        
        else:
            contextual_prompt = f"""Help expand this artistic prompt: "{user_input}"

Provide {num_suggestions} short, creative suggestions (2-8 words each) that could enhance this prompt for visual art creation:

Examples of good suggestions:
- "with vibrant color palette"
- "minimalist modern style"
- "vintage retro aesthetic"
- "dramatic lighting effects"
- "abstract geometric patterns"

Format as brief phrases only, one per line:"""
        
        return contextual_prompt
    
    def get_suggestions(self, prompt: str, service_id: str = None, num_suggestions: int = 3, mode: str = 'default', **kwargs) -> List[str]:
        """Get text suggestions from specified service with contextual prompts"""
        service_id = service_id or self._active_service
          # If no service is available, return fallback suggestions directly
        if not service_id:
            logger.info(f"No active service available, using fallback suggestions for: {prompt[:50]}... (mode: {mode})")
            suggestion_type = kwargs.get('suggestion_type', 'short')
            return self._get_fallback_suggestions(prompt, num_suggestions, mode, suggestion_type)
        
        # Create contextual prompt based on mode
        contextual_prompt = self._create_contextual_prompt(prompt, mode, num_suggestions)
        
        # Check cache first (include mode in cache key)
        cache_key = f"suggestions_{service_id}_{hash(contextual_prompt)}_{num_suggestions}_{mode}"
        cached_suggestions = cache.get(cache_key)
        if cached_suggestions:
            logger.info(f"Returning cached suggestions for: {prompt[:50]}... (mode: {mode})")
            return cached_suggestions
        
        try:
            suggestions = []
            
            if service_id == 'gemini' and self._gemini_service:
                # Use Gemini for suggestions
                response = self._gemini_service.generate_response(contextual_prompt)
                suggestions = [line.strip() for line in response.split('\n') if line.strip()]
                suggestions = suggestions[:num_suggestions]
                
            elif service_id in self._services:
                # Use Hugging Face service with contextual prompt
                service = self._services[service_id]
                if not service.is_model_loaded():
                    raise LLMServiceError(f"Service {service_id} not loaded")
                
                # For TGI services, pass the contextual prompt instead of the raw user input
                # Extract parameters to avoid conflicts
                max_tokens = kwargs.get('max_tokens', 200)  # Increase default from 100 to 200
                temperature = kwargs.get('temperature', 0.8)
                suggestions = service.get_suggestions(contextual_prompt, max_tokens, temperature, num_suggestions)
            
            else:
                raise LLMServiceError(f"Service {service_id} not available")
            
            # Cache results for 10 minutes
            if suggestions:
                cache.set(cache_key, suggestions, 600)
            
            return suggestions
              except Exception as e:
            logger.error(f"Failed to get suggestions from {service_id}: {e}")
            # Return fallback suggestions
            suggestion_type = kwargs.get('suggestion_type', 'short')
            return self._get_fallback_suggestions(prompt, num_suggestions, mode, suggestion_type)
      def _get_fallback_suggestions(self, prompt: str, num_suggestions: int, mode: str = 'default', suggestion_type: str = 'short') -> List[str]:
        """Provide fallback suggestions when all services fail"""
        
        if suggestion_type == 'long':
            # Long suggestions - full descriptive sentences
            if mode.lower() == 'gaming':
                base_suggestions = [
                    f"Epic {prompt} battlefield scene with dynamic lighting and particle effects",
                    f"Mysterious {prompt} dungeon environment with ancient architecture and glowing runes", 
                    f"Futuristic {prompt} cityscape with neon lights and cyberpunk aesthetic elements",
                    f"Fantasy {prompt} realm with magical creatures and ethereal atmospheric lighting",
                    f"Post-apocalyptic {prompt} wasteland with rusty machinery and dramatic storm clouds"
                ]
            else:
                base_suggestions = [
                    f"Artistic interpretation of {prompt} with vibrant colors and dynamic composition",
                    f"Minimalist {prompt} design featuring clean lines and balanced visual elements",
                    f"Vintage-style {prompt} illustration with retro color palette and nostalgic mood",
                    f"Modern {prompt} concept art with bold geometric shapes and contemporary styling",
                    f"Dreamy {prompt} scene with soft atmospheric lighting and ethereal qualities"
                ]
        else:
            # Short suggestions - brief enhancement phrases
            if mode.lower() == 'gaming':
                base_suggestions = [
                    "with cyberpunk neon lighting",
                    "dark fantasy style",
                    "retro pixel art aesthetic", 
                    "futuristic sci-fi elements",
                    "post-apocalyptic atmosphere",
                    "epic battle scene",
                    "glowing magical effects",
                    "ancient ruins background"
                ]
            else:
                base_suggestions = [
                    "with vibrant color palette",
                    "minimalist modern style",
                    "vintage retro aesthetic",
                    "dramatic lighting effects",
                    "abstract geometric patterns",
                    "soft dreamy atmosphere",
                    "bold artistic composition",
                    "elegant sophisticated design"
                ]
        
        return base_suggestions[:num_suggestions]
    
    def get_active_service(self) -> Optional[str]:
        """Get currently active service ID"""
        return self._active_service
    
    def get_service_status(self, service_id: str) -> Dict[str, Any]:
        """Get status of a specific service"""
        if service_id == 'gemini':
            return {
                'service_id': service_id,
                'loaded': self._gemini_service is not None,
                'type': 'api',
                'provider': 'Google'
            }
        
        elif service_id in self._services:
            service = self._services[service_id]
            return {
                'service_id': service_id,
                'loaded': service.is_model_loaded(),
                'type': 'local',
                'provider': 'Hugging Face',
                **service.get_model_info()
            }
        
        else:
            return {
                'service_id': service_id,
                'loaded': False,
                'available': service_id in self.list_services()
            }


# Global instance
llm_manager = LLMServiceManager()
