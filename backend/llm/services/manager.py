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
        
        # Add TGI API models - the working API models from Hugging Face
        for model_id, model_info in TGIAPIService.get_available_models().items():
            services_info[f"tgi_{model_id}"] = {
                'type': 'tgi',
                'model_name': model_id,
                'provider': 'Hugging Face TGI API',
                'status': 'available',
                'model_url': model_info.get('model_url', f'https://huggingface.co/{model_id}'),
                **model_info
            }
        
        # Add GitHub Models
        for model_id, model_info in GitHubModelsService.AVAILABLE_MODELS.items():
            services_info[f"github_{model_id}"] = {
                'type': 'github',
                'model_name': model_id,
                'provider': 'GitHub Models (OpenAI)',
                'status': 'available',
                'model_url': model_info.get('model_url', f'https://github.com/models/{model_id}'),
                **model_info
            }
        
        # Add Gemini service (used elsewhere in the app)  
        if self._gemini_service:
            services_info['gemini'] = {
                'type': 'gemini',
                'model_name': 'gemini-2.0-flash',
                'provider': 'Google AI',
                'name': 'Gemini 2.0 Flash (Google)',
                'description': 'Google\'s latest multimodal AI model for text generation',
                'status': 'available'
            }
        
        # Add status for loaded services
        for service_id, service in self._services.items():
            if service_id in services_info:
                services_info[service_id]['status'] = 'loaded' if service.is_model_loaded() else 'available'
        
        return services_info
    
    def load_service(self, service_id: str, model_name: str = None):
        """Load a specific service and return the service instance"""
        try:
            # Check if service is already loaded
            if service_id in self._services:
                if self._services[service_id].is_model_loaded():
                    logger.info(f"Service {service_id} already loaded")
                    return self._services[service_id]
            
            # Determine service type and model
            if service_id.startswith('tgi_'):
                # TGI service - your original working models
                model_id = service_id.replace('tgi_', '')
                service = TGIAPIService(model_id)
                success = service.load_model()
                
                if success:
                    self.register_service(service_id, service)
                    self._active_service = service_id
                    
                    # Cache service info
                    cache.set(f"llm_service_{service_id}", service.get_model_info(), 3600)
                    
                    return service
                else:
                    raise LLMServiceError(f"Failed to load TGI service: {service_id}")
            
            elif service_id.startswith('github_'):
                # GitHub Models service
                model_id = service_id.replace('github_', '')
                service = GitHubModelsService(model_id)
                success = service.load_model()
                
                if success:
                    self.register_service(service_id, service)
                    self._active_service = service_id
                    
                    # Cache service info
                    cache.set(f"llm_service_{service_id}", service.get_model_info(), 3600)
                    
                    return service
                else:
                    raise LLMServiceError(f"Failed to load GitHub Models service: {service_id}")
            
            elif service_id == 'gemini':
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
        """Get text suggestions - try TGI models first, then fallback"""
        
        suggestion_type = kwargs.get('suggestion_type', 'short')
        
        # Try TGI models if specifically requested (your original working models)
        if service_id and service_id.startswith('tgi_'):
            try:
                logger.info(f"Attempting to use TGI service: {service_id}")
                
                # Try to load the service if not already loaded
                if service_id not in self._services:
                    logger.info(f"Loading TGI service: {service_id}")
                    service = self.load_service(service_id)
                    if not service:
                        logger.warning(f"Failed to load TGI service: {service_id}")
                        raise Exception(f"Could not load service: {service_id}")
                else:
                    service = self._services.get(service_id)
                
                # Get the service and generate suggestions
                if service and service.is_model_loaded():
                    contextual_prompt = self._create_contextual_prompt(prompt, mode, num_suggestions)
                    logger.info(f"Generating suggestions using TGI service for: {prompt[:50]}...")
                    
                    # Extract temperature from kwargs if present, otherwise use default
                    temperature = kwargs.pop('temperature', 0.7)
                    
                    suggestions = service.get_suggestions(
                        prompt=contextual_prompt, 
                        max_tokens=50, 
                        temperature=temperature, 
                        num_suggestions=num_suggestions,
                        **kwargs
                    )
                    
                    # Clean up and validate suggestions
                    cleaned_suggestions = []
                    for suggestion in suggestions:
                        if suggestion and len(suggestion.strip()) > 3:
                            # Remove any instructional text that might be returned
                            suggestion_text = suggestion.strip()
                            if not suggestion_text.startswith('SSH tunnel') and not suggestion_text.startswith('TGI'):
                                cleaned_suggestions.append(suggestion_text)
                    
                    if cleaned_suggestions:
                        logger.info(f"Generated {len(cleaned_suggestions)} suggestions using TGI service")
                        return cleaned_suggestions
                    
            except Exception as e:
                logger.warning(f"TGI service failed: {e}")
                logger.info("Falling back to other services")
        
        # Try GitHub Models service if specifically requested
        if service_id and service_id.startswith('github_'):
            try:
                logger.info(f"Attempting to use GitHub Models service: {service_id}")
                
                # Try to load the service if not already loaded
                if service_id not in self._services:
                    logger.info(f"Loading GitHub Models service: {service_id}")
                    service = self.load_service(service_id)
                    if not service:
                        logger.warning(f"Failed to load GitHub Models service: {service_id}")
                        raise Exception(f"Could not load service: {service_id}")
                else:
                    service = self._services.get(service_id)
                
                # Get the service and generate suggestions
                if service and service.is_model_loaded():
                    contextual_prompt = self._create_contextual_prompt(prompt, mode, num_suggestions)
                    logger.info(f"Generating suggestions using GitHub Models service for: {prompt[:50]}...")
                    
                    # Extract temperature from kwargs if present, otherwise use default
                    temperature = kwargs.pop('temperature', 0.7)
                    
                    suggestions = service.get_suggestions(
                        prompt=contextual_prompt, 
                        max_tokens=50, 
                        temperature=temperature, 
                        num_suggestions=num_suggestions,
                        **kwargs
                    )
                    
                    # Clean up and validate suggestions
                    cleaned_suggestions = []
                    for suggestion in suggestions:
                        if suggestion and len(suggestion.strip()) > 3:
                            suggestion_text = suggestion.strip()
                            cleaned_suggestions.append(suggestion_text)
                    
                    if cleaned_suggestions:
                        logger.info(f"Generated {len(cleaned_suggestions)} suggestions using GitHub Models")
                        return cleaned_suggestions
                    
            except Exception as e:
                logger.warning(f"GitHub Models service failed: {e}")
                logger.info("Falling back to other services")
        
        # If no specific service requested, try TGI models first (updated working models)
        if not service_id:
            # Try GitHub Models first (new high-quality models)
            github_models = ['github_openai/gpt-4.1']
            for model_id in github_models:
                try:
                    logger.info(f"Attempting to use GitHub model: {model_id}")
                    return self.get_suggestions(prompt, model_id, num_suggestions, mode, **kwargs)
                except Exception as e:
                    logger.warning(f"GitHub model {model_id} failed: {e}")
                    continue
            
            # Try TGI API models as backup (Mistral, Mixtral, Gemma)
            tgi_models = ['tgi_mistralai/Mistral-7B-Instruct-v0.2', 'tgi_mistralai/Mixtral-8x7B-Instruct-v0.1', 'tgi_google/gemma-7b-it']
            for model_id in tgi_models:
                try:
                    logger.info(f"Attempting to use TGI model: {model_id}")
                    return self.get_suggestions(prompt, model_id, num_suggestions, mode, **kwargs)
                except Exception as e:
                    logger.warning(f"TGI model {model_id} failed: {e}")
                    continue
        
        # Always use fallback suggestions for reliable results
        return self._get_fallback_suggestions(prompt, num_suggestions, mode, suggestion_type)
    
    def _get_fallback_suggestions(self, prompt: str, num_suggestions: int, mode: str = 'default', suggestion_type: str = 'short') -> List[str]:
        """Provide enhanced fallback suggestions when all services fail"""
        
        # Enhanced fallback suggestions based on prompt keywords
        prompt_lower = prompt.lower()
        
        # Extract key themes from prompt
        themes = {
            'nature': ['forest', 'tree', 'mountain', 'river', 'lake', 'ocean', 'beach', 'flower', 'garden', 'natural'],
            'fantasy': ['magic', 'mystical', 'dragon', 'castle', 'wizard', 'fairy', 'enchanted', 'magical', 'mythical'],
            'sci-fi': ['futuristic', 'space', 'robot', 'technology', 'cyberpunk', 'alien', 'cyber', 'tech', 'digital'],
            'urban': ['city', 'street', 'building', 'urban', 'modern', 'architecture', 'downtown', 'metropolitan'],
            'vintage': ['retro', 'vintage', 'classic', 'antique', 'old', 'historical', 'traditional'],
            'abstract': ['abstract', 'artistic', 'creative', 'surreal', 'imaginative', 'conceptual']
        }
        
        detected_theme = 'general'
        for theme, keywords in themes.items():
            if any(keyword in prompt_lower for keyword in keywords):
                detected_theme = theme
                break
        
        if suggestion_type == 'long':
            # Long suggestions - context-aware full sentences
            if mode.lower() == 'gaming':
                theme_suggestions = {
                    'nature': [
                        f"Immersive {prompt} environment with realistic wildlife and dynamic weather systems",
                        f"Open-world {prompt} setting featuring interactive ecosystems and day-night cycles",
                        f"Atmospheric {prompt} landscape with ambient sounds and particle effects"
                    ],
                    'fantasy': [
                        f"Epic {prompt} realm with magical creatures and spellcasting mechanics",
                        f"Mystical {prompt} world featuring ancient lore and enchanted artifacts",
                        f"Fantasy {prompt} setting with character progression and magical abilities"
                    ],
                    'sci-fi': [
                        f"Futuristic {prompt} environment with advanced technology and AI companions",
                        f"Cyberpunk {prompt} setting featuring neon-lit streets and digital interfaces",
                        f"Space-age {prompt} world with zero-gravity mechanics and alien encounters"
                    ],
                    'urban': [
                        f"Modern {prompt} cityscape with interactive NPCs and dynamic traffic systems",
                        f"Urban {prompt} environment featuring parkour mechanics and vertical exploration",
                        f"Metropolitan {prompt} setting with day-night cycles and realistic city life"
                    ],
                    'vintage': [
                        f"Retro-styled {prompt} world with classic arcade aesthetics and pixel art",
                        f"Vintage {prompt} setting featuring historical accuracy and period-appropriate details",
                        f"Classic {prompt} environment with nostalgic gameplay and timeless design"
                    ],
                    'general': [
                        f"Immersive {prompt} game world with rich storytelling and character development",
                        f"Interactive {prompt} environment featuring dynamic gameplay and player choices",
                        f"Atmospheric {prompt} setting with detailed world-building and engaging mechanics"
                    ]
                }
            else:
                theme_suggestions = {
                    'nature': [
                        f"Serene {prompt} scene with soft natural lighting and organic textures",
                        f"Peaceful {prompt} composition featuring earth tones and flowing forms",
                        f"Harmonious {prompt} artwork with botanical elements and gentle shadows"
                    ],
                    'fantasy': [
                        f"Ethereal {prompt} illustration with mystical lighting and dreamy atmosphere",
                        f"Enchanted {prompt} artwork featuring magical elements and soft glowing effects",
                        f"Whimsical {prompt} design with fantastical creatures and otherworldly beauty"
                    ],
                    'sci-fi': [
                        f"Sleek {prompt} design with metallic surfaces and neon accent lighting",
                        f"Futuristic {prompt} composition featuring holographic elements and clean lines",
                        f"High-tech {prompt} artwork with digital effects and modern aesthetics"
                    ],
                    'urban': [
                        f"Contemporary {prompt} scene with architectural details and urban sophistication",
                        f"Modern {prompt} composition featuring clean geometries and industrial materials",
                        f"Stylish {prompt} artwork with metropolitan flair and contemporary design"
                    ],
                    'vintage': [
                        f"Nostalgic {prompt} illustration with warm sepia tones and classic styling",
                        f"Retro {prompt} design featuring vintage typography and timeless aesthetics",
                        f"Classic {prompt} artwork with traditional techniques and elegant composition"
                    ],
                    'general': [
                        f"Artistic {prompt} composition with balanced lighting and thoughtful color palette",
                        f"Creative {prompt} design featuring unique perspective and visual interest",
                        f"Expressive {prompt} artwork with dynamic composition and emotional depth"
                    ]
                }
        else:
            # Short suggestions - context-aware brief phrases
            if mode.lower() == 'gaming':
                theme_suggestions = {
                    'nature': ["with dynamic weather", "featuring wildlife", "with day-night cycle", "atmospheric fog effects", "realistic textures"],
                    'fantasy': ["with magical effects", "mystical atmosphere", "enchanted lighting", "ethereal glow", "magical particles"],
                    'sci-fi': ["with neon accents", "holographic elements", "cyberpunk style", "futuristic lighting", "digital effects"],
                    'urban': ["with city lighting", "urban atmosphere", "metropolitan style", "architectural details", "street-level view"],
                    'vintage': ["retro pixel art", "classic arcade style", "nostalgic colors", "vintage aesthetics", "timeless design"],
                    'general': ["cinematic lighting", "dynamic composition", "atmospheric effects", "detailed textures", "immersive environment"]
                }
            else:
                theme_suggestions = {
                    'nature': ["with soft lighting", "organic textures", "earth tone palette", "natural shadows", "botanical elements"],
                    'fantasy': ["ethereal glow", "mystical atmosphere", "dreamy lighting", "magical elements", "otherworldly beauty"],
                    'sci-fi': ["sleek metallic finish", "neon accent lighting", "holographic effects", "modern aesthetics", "digital elements"],
                    'urban': ["architectural details", "urban sophistication", "contemporary style", "industrial materials", "metropolitan flair"],
                    'vintage': ["warm sepia tones", "classic styling", "nostalgic mood", "vintage aesthetics", "timeless appeal"],
                    'general': ["balanced composition", "thoughtful lighting", "creative perspective", "artistic flair", "visual harmony"]
                }
        
        # Get suggestions for detected theme
        suggestions = theme_suggestions.get(detected_theme, theme_suggestions['general'])
        
        # Return requested number of suggestions
        import random
        return random.sample(suggestions, min(num_suggestions, len(suggestions)))
    
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
