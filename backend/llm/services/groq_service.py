"""
Groq LLM Service Implementation
Free tier with high rate limits and fast inference
"""

import os
import logging
import requests
from typing import List, Dict, Any, Optional
import json

from .base import BaseLLMService, LLMServiceError

logger = logging.getLogger(__name__)


class GroqService(BaseLLMService):
    """Groq API service - generous free tier with fast inference"""

    # Free models available on Groq
    AVAILABLE_MODELS = {
        "llama-3.1-8b-instant": {
            "name": "Llama 3.1 8B Instant",
            "description": "Meta's fast and efficient model - perfect for suggestions",
            "size": "8B parameters",
            "type": "instruct",
            "speed": "Ultra Fast",
            "quality": "Excellent",
            "free_tier": True,
        },
        "llama-3.1-70b-versatile": {
            "name": "Llama 3.1 70B Versatile",
            "description": "Large model for highest quality suggestions",
            "size": "70B parameters",
            "type": "instruct",
            "speed": "Fast",
            "quality": "Outstanding",
            "free_tier": True,
        },
        "mixtral-8x7b-32768": {
            "name": "Mixtral 8x7B",
            "description": "Mistral's mixture of experts model",
            "size": "8x7B parameters",
            "type": "instruct",
            "speed": "Very Fast",
            "quality": "Very Good",
            "free_tier": True,
        },
        "gemma2-9b-it": {
            "name": "Gemma 2 9B IT",
            "description": "Google's instruction-tuned model",
            "size": "9B parameters",
            "type": "instruct",
            "speed": "Very Fast",
            "quality": "Very Good",
            "free_tier": True,
        },
    }

    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        super().__init__(model_name)
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def load_model(self) -> bool:
        """Verify Groq API access and model availability"""
        try:
            if not self.api_key:
                logger.info(
                    "No GROQ_API_KEY found. Get free API key from: https://console.groq.com/"
                )
                return False

            # Test API connection
            response = requests.get(
                f"{self.base_url}/models", headers=self.headers, timeout=10
            )

            if response.status_code == 401:
                raise LLMServiceError("Invalid Groq API key")
            elif response.status_code != 200:
                raise LLMServiceError(f"Groq API error: {response.status_code}")

            # Check if model is available
            models = response.json().get("data", [])
            model_ids = [model["id"] for model in models]

            if self.model_name not in model_ids:
                logger.warning(
                    f"Model {self.model_name} not available. Available: {model_ids[:5]}"
                )
                # Use first available model as fallback
                if model_ids:
                    self.model_name = model_ids[0]
                    logger.info(f"Using fallback model: {self.model_name}")

            self.is_loaded = True
            logger.info(f"Groq model {self.model_name} is ready")
            return True

        except requests.RequestException as e:
            raise LLMServiceError(f"Could not connect to Groq API: {e}")
        except Exception as e:
            raise LLMServiceError(f"Failed to initialize Groq service: {e}")

    def unload_model(self) -> bool:
        """Groq models don't need explicit unloading"""
        self.is_loaded = False
        return True

    def generate_text(
        self, prompt: str, max_length: int = 100, temperature: float = 0.7
    ) -> str:
        """Generate text using Groq API"""
        if not self.is_loaded:
            raise LLMServiceError("Model not loaded")

        try:
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_length,
                "temperature": temperature,
                "stream": False,
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers,
                timeout=30,
            )

            if response.status_code == 429:
                raise LLMServiceError("Groq rate limit exceeded. Please wait a moment.")
            elif response.status_code != 200:
                raise LLMServiceError(f"Groq API error: {response.status_code}")

            result = response.json()
            return result["choices"][0]["message"]["content"].strip()

        except requests.RequestException as e:
            raise LLMServiceError(f"Groq request failed: {e}")
        except Exception as e:
            raise LLMServiceError(f"Text generation failed: {e}")

    def generate_suggestions(
        self,
        prompt: str,
        num_suggestions: int = 3,
        mode: str = "default",
        suggestion_type: str = "short",
        **kwargs,
    ) -> List[str]:
        """Generate moodboard suggestions using Groq"""
        if not self.is_loaded:
            raise LLMServiceError("Model not loaded")

        try:
            # Create context-aware prompts
            if mode == "gaming":
                context = "game environment design, concept art, gaming atmosphere"
            else:
                context = "visual design, artistic mood, creative composition"

            if suggestion_type == "long":
                instruction = f"""Generate {num_suggestions} detailed creative suggestions to enhance this {context} prompt: "{prompt}"

Each suggestion should be a complete descriptive phrase (8-12 words) that adds depth and creativity.
Return only the suggestions, one per line, no numbers or bullets:"""
            else:
                instruction = f"""Generate {num_suggestions} short creative additions for this {context} prompt: "{prompt}"

Each suggestion should be 2-4 words that enhance the visual concept.
Return only the suggestions, one per line, no numbers or bullets:"""

            response_text = self.generate_text(
                instruction, max_length=150, temperature=0.8
            )

            # Parse suggestions
            suggestions = []
            lines = response_text.split("\\n")
            for line in lines:
                clean_line = line.strip().strip(".-*1234567890").strip()
                if clean_line and len(clean_line) > 2:
                    suggestions.append(clean_line)
                if len(suggestions) >= num_suggestions:
                    break

            # Fallback if parsing failed
            if not suggestions:
                logger.warning("Groq parsing failed, using fallback suggestions")
                if suggestion_type == "long":
                    if mode == "gaming":
                        suggestions = [
                            "Cinematic lighting with dramatic shadow contrasts",
                            "Rich environmental storytelling through visual details",
                            "Dynamic composition that guides the player's eye",
                        ]
                    else:
                        suggestions = [
                            "Sophisticated color harmony with subtle gradients",
                            "Textural variety that creates visual depth",
                            "Balanced asymmetry for engaging composition",
                        ]
                else:
                    if mode == "gaming":
                        suggestions = [
                            "cinematic lighting",
                            "epic atmosphere",
                            "detailed textures",
                        ]
                    else:
                        suggestions = [
                            "vibrant palette",
                            "artistic texture",
                            "modern composition",
                        ]

            return suggestions[:num_suggestions]

        except Exception as e:
            logger.error(f"Groq suggestion generation failed: {e}")
            raise LLMServiceError(f"Could not generate suggestions: {e}")

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "name": self.model_name,
            "provider": "Groq (Cloud)",
            "type": "api",
            "status": "loaded" if self.is_loaded else "available",
            "description": self.AVAILABLE_MODELS.get(self.model_name, {}).get(
                "description", "Groq model"
            ),
            "size": self.AVAILABLE_MODELS.get(self.model_name, {}).get(
                "size", "Unknown"
            ),
            "free_tier": True,
        }

    @staticmethod
    def get_setup_instructions() -> str:
        """Get instructions for setting up Groq"""
        return """
To use Groq (FREE):

1. Sign up at: https://console.groq.com/
2. Create a free API key (no payment required)
3. Set environment variable:
   $env:GROQ_API_KEY="your_groq_api_key_here"

Free tier includes:
- High rate limits
- Fast inference
- No payment required
- Multiple models available

Models reset daily, so you get fresh limits every day!
"""
