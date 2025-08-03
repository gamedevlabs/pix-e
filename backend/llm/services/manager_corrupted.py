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
        services_info = {}        # Add TGI models (only working models with free Hugging Face API)
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
    
    def get_suggestions(self, prompt: str, service_id: str = None, num_suggestions: int = 3, mode: str = 'default', **kwargs) -> List[str]:
        """Get text suggestions from specified service with contextual prompts"""
        service_id = service_id or self._active_service
        
        if not service_id:
            raise LLMServiceError("No active service. Load a service first.")
        
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
                suggestion_prompt = (
                    f"Generate {num_suggestions} creative, diverse prompt suggestions "
                    f"based on this input: '{prompt}'. "
                    f"Return only the suggestions, one per line, without numbering or extra text."
                )
                
                response = self._gemini_service.generate_response(suggestion_prompt)
                suggestions = [line.strip() for line in response.split('\n') if line.strip()]
                suggestions = suggestions[:num_suggestions]
                
            elif service_id in self._services:
                # Use Hugging Face service
                service = self._services[service_id]
                if not service.is_model_loaded():
                    raise LLMServiceError(f"Service {service_id} not loaded")
                
                suggestions = service.get_suggestions(prompt, num_suggestions, **kwargs)
            
            else:
                raise LLMServiceError(f"Service {service_id} not available")
            
            # Cache results for 10 minutes
            if suggestions:
                cache.set(cache_key, suggestions, 600)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to get suggestions from {service_id}: {e}")
            # Return fallback suggestions
            return self._get_fallback_suggestions(prompt, num_suggestions)
    
    def _get_fallback_suggestions(self, prompt: str, num_suggestions: int) -> List[str]:
        """Provide fallback suggestions when all services fail"""
        base_suggestions = [
            f"Create a {prompt} with vibrant colors and dynamic lighting",
            f"Design a {prompt} in a minimalist, clean aesthetic",
            f"Imagine a {prompt} with futuristic, sci-fi elements",
            f"Visualize a {prompt} with natural, organic textures",
            f"Picture a {prompt} with retro, vintage styling"
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
