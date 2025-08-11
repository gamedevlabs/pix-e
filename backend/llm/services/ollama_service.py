"""
Ollama Local LLM Service Implementation
Provides completely free local AI models through Ollama
"""

import logging
from typing import Any, Dict, List

import requests

from .base import BaseLLMService, LLMServiceError

logger = logging.getLogger(__name__)


class OllamaService(BaseLLMService):
    """Ollama local LLM service - completely free alternative"""

    # Free local models available through Ollama
    AVAILABLE_MODELS = {
        "llama3.2:1b": {
            "name": "Llama 3.2 1B (Ultra Fast)",
            "description": "Meta's smallest Llama model - perfect for suggestions",
            "size": "1.3GB",
            "type": "instruct",
            "speed": "Very Fast",
            "quality": "Good",
        },
        "llama3.2:3b": {
            "name": "Llama 3.2 3B (Balanced)",
            "description": "Great balance of speed and quality",
            "size": "2GB",
            "type": "instruct",
            "speed": "Fast",
            "quality": "Very Good",
        },
        "phi3:mini": {
            "name": "Phi-3 Mini (Microsoft)",
            "description": "Microsoft's efficient model for creative tasks",
            "size": "2.3GB",
            "type": "instruct",
            "speed": "Fast",
            "quality": "Excellent",
        },
        "gemma2:2b": {
            "name": "Gemma 2 2B (Google)",
            "description": "Google's lightweight model",
            "size": "1.6GB",
            "type": "instruct",
            "speed": "Fast",
            "quality": "Very Good",
        },
        "qwen2.5:1.5b": {
            "name": "Qwen 2.5 1.5B (Lightweight)",
            "description": "Alibaba's efficient multilingual model",
            "size": "934MB",
            "type": "instruct",
            "speed": "Very Fast",
            "quality": "Good",
        },
    }

    def __init__(
        self, model_name: str = "llama3.2:1b", host: str = "http://localhost:11434"
    ):
        super().__init__(model_name)
        self.host = host.rstrip("/")
        self.endpoint = f"{self.host}/api/generate"
        self.chat_endpoint = f"{self.host}/api/chat"

    def load_model(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            # Check if Ollama server is running
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code != 200:
                raise LLMServiceError(
                    "Ollama server not running. Please install and start Ollama."
                )

            # Check available models
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]

            if self.model_name not in model_names:
                logger.warning(
                    f"Model {self.model_name} not found. Available: {model_names}"
                )
                logger.info(f"To install: ollama pull {self.model_name}")
                return False

            self.is_loaded = True
            logger.info(f"Ollama model {self.model_name} is available")
            return True

        except requests.RequestException as e:
            raise LLMServiceError(f"Could not connect to Ollama server: {e}")
        except Exception as e:
            raise LLMServiceError(f"Failed to load Ollama model: {e}")

    def unload_model(self) -> bool:
        """Ollama models don't need explicit unloading"""
        self.is_loaded = False
        return True

    def generate_text(
        self, prompt: str, max_length: int = 100, temperature: float = 0.7
    ) -> str:
        """Generate text using Ollama"""
        if not self.is_loaded:
            raise LLMServiceError("Model not loaded")

        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_length,
                    "stop": ["\\n\\n", "\\n###", "User:", "Assistant:"],
                },
            }

            response = requests.post(self.endpoint, json=payload, timeout=30)

            if response.status_code != 200:
                raise LLMServiceError(f"Ollama API error: {response.status_code}")

            result = response.json()
            return result.get("response", "").strip()

        except requests.RequestException as e:
            raise LLMServiceError(f"Ollama request failed: {e}")
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
        """Generate moodboard suggestions using Ollama"""
        if not self.is_loaded:
            raise LLMServiceError("Model not loaded")

        try:
            # Create context-aware prompts
            if mode == "gaming":
                context = "game environment, concept art, gaming atmosphere"
            else:
                context = "visual design, artistic mood, creative atmosphere"

            if suggestion_type == "long":
                instruction = (
                    f"Generate {num_suggestions} detailed creative suggestions "
                    f"to enhance this {context} prompt: '{prompt}'. Each "
                    f"suggestion should be a complete descriptive phrase "
                    f"(10-15 words)."
                )
            else:
                instruction = (
                    f"Generate {num_suggestions} short creative additions for "
                    f"this {context} prompt: '{prompt}'. Each suggestion "
                    f"should be 2-4 words."
                )

            full_prompt = (
                f"{instruction}\\n\\nReturn only the suggestions, one per line, "
                f"without numbers or bullets:"
            )

            response_text = self.generate_text(
                full_prompt, max_length=200, temperature=0.8
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
                if suggestion_type == "long":
                    if mode == "gaming":
                        suggestions = [
                            "Dynamic lighting effects with dramatic shadows",
                            "Rich environmental details and atmospheric particles",
                            "Cinematic composition with depth and perspective",
                        ]
                    else:
                        suggestions = [
                            "Harmonious color transitions and gradient effects",
                            "Textural elements that enhance visual interest",
                            "Balanced composition with focal emphasis",
                        ]
                else:
                    if mode == "gaming":
                        suggestions = [
                            "epic lighting",
                            "detailed textures",
                            "atmospheric effects",
                        ]
                    else:
                        suggestions = [
                            "vibrant colors",
                            "artistic flair",
                            "modern style",
                        ]

            return suggestions[:num_suggestions]

        except Exception as e:
            logger.error(f"Ollama suggestion generation failed: {e}")
            raise LLMServiceError(f"Could not generate suggestions: {e}")

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "name": self.model_name,
            "provider": "Ollama (Local)",
            "type": "local",
            "status": "loaded" if self.is_loaded else "available",
            "description": self.AVAILABLE_MODELS.get(self.model_name, {}).get(
                "description", "Ollama model"
            ),
            "size": self.AVAILABLE_MODELS.get(self.model_name, {}).get(
                "size", "Unknown"
            ),
            "host": self.host,
        }

    @staticmethod
    def get_installation_instructions() -> str:
        """Get instructions for installing Ollama"""
        return """
To use Ollama models:

1. Install Ollama:
   - Windows: Download from https://ollama.com/download
   - macOS: brew install ollama
   - Linux: curl -fsSL https://ollama.com/install.sh | sh

2. Start Ollama server:
   ollama serve

3. Pull a model:
   ollama pull llama3.2:1b

4. Verify installation:
   ollama list

Models will be automatically downloaded when first used.
"""
