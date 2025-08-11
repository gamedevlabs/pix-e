"""
Hugging Face LLM Service Implementation
"""

import gc
import logging
import os
from typing import Any, Dict, List

import torch
from huggingface_hub import login
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from .base import BaseLLMService, LLMServiceError

logger = logging.getLogger(__name__)


class HuggingFaceLLMService(BaseLLMService):
    """
    Hugging Face model service for text generation.
    Recommended models for creative text suggestions and game design prompts
    """

    AVAILABLE_MODELS = {
        "distilgpt2": {
            "name": "DistilGPT-2",
            "description": (
                "Ultra fast, lightweight text generation for quick suggestions"
            ),
            "size": "80MB",
            "type": "text-generation",
        },
        "microsoft/DialoGPT-medium": {
            "name": "DialoGPT Medium",
            "description": (
                "Conversational AI model, excellent for creative suggestions"
            ),
            "size": "300MB",
            "type": "conversational",
        },
        "gpt2": {
            "name": "GPT-2",
            "description": (
                "Classic text generation model, reliable for creative writing"
            ),
            "size": "500MB",
            "type": "text-generation",
        },
        "gpt2-medium": {
            "name": "GPT-2 Medium",
            "description": (
                "Higher quality text generation with better creativity and detail"
            ),
            "size": "1.5GB",
            "type": "text-generation",
        },
    }

    def __init__(self, model_name: str = "distilgpt2"):
        super().__init__(model_name)
        self.tokenizer = None
        self.model = None
        self.generator = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Initialize HF Hub login if token available
        hf_token = os.environ.get("HF_TOKEN")
        if hf_token:
            try:
                login(token=hf_token)
                logger.info("Successfully logged into Hugging Face Hub")
            except Exception as e:
                logger.warning(f"Could not login to HF Hub: {e}")

    def load_model(self) -> bool:
        """Load the Hugging Face model"""
        try:
            if self.is_loaded:
                logger.info(f"Model {self.model_name} already loaded")
                return True

            logger.info(f"Loading model {self.model_name} on {self.device}")

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, padding_side="left"
            )

            # Add pad token if it doesn't exist
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # Load model with appropriate settings
            model_kwargs = {
                "torch_dtype": (
                    torch.float16 if self.device == "cuda" else torch.float32
                ),
                "low_cpu_mem_usage": True,
            }

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name, **model_kwargs
            )

            # Move to device
            self.model = self.model.to(self.device)

            # Create pipeline for easier text generation
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
            )

            self.is_loaded = True
            logger.info(f"Successfully loaded {self.model_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            self.cleanup()
            raise LLMServiceError(f"Could not load model: {e}")

    def unload_model(self) -> bool:
        """Unload model from memory"""
        try:
            self.cleanup()
            # Force garbage collection
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info(f"Successfully unloaded {self.model_name}")
            return True
        except Exception as e:
            logger.error(f"Error unloading model: {e}")
            return False

    def cleanup(self):
        """Clean up model resources"""
        self.generator = None
        self.model = None
        self.tokenizer = None
        self.is_loaded = False

    def generate_text(self, prompt: str, max_length: int = 100, **kwargs) -> str:
        """Generate text based on prompt"""
        if not self.is_loaded:
            raise LLMServiceError("Model not loaded. Call load_model() first.")

        try:
            # Set generation parameters
            generation_kwargs = {
                "max_length": len(self.tokenizer.encode(prompt)) + max_length,
                "num_return_sequences": 1,
                "temperature": kwargs.get("temperature", 0.7),
                "do_sample": True,
                "pad_token_id": self.tokenizer.eos_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
                "repetition_penalty": 1.1,
            }
            # Generate text
            outputs = self.generator(prompt, **generation_kwargs)
            generated_text = outputs[0]["generated_text"]

            # Remove the original prompt from output
            if generated_text.startswith(prompt):
                generated_text = generated_text[len(prompt) :].strip()

            return generated_text
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise LLMServiceError(f"Text generation failed: {e}")

    def get_suggestions(
        self, prompt: str, num_suggestions: int = 3, **kwargs
    ) -> List[str]:
        """Generate multiple text suggestions for creative prompts"""
        if not self.is_loaded:
            raise LLMServiceError("Model not loaded. Call load_model() first.")

        try:
            suggestion_type = kwargs.get(
                "suggestion_type", "short"
            )  # Handle suggestion_type parameter

            # Create different prompt templates for better variety
            if suggestion_type == "short":
                prompt_templates = [
                    f"{prompt} with ",  # Simple addition
                    f"{prompt} featuring ",  # Feature-based prompt
                    f"{prompt} including ",  # Inclusion-based
                ]
            else:  # long suggestions
                prompt_templates = [
                    f"A detailed {prompt} scene with ",  # Scene description starter
                    f"Create an image of {prompt} that shows ",  # Image-focused prompt
                    f"An epic {prompt} featuring ",  # Epic description
                ]

            all_suggestions = []

            for i, template in enumerate(prompt_templates[:num_suggestions]):
                try:
                    # Generate with varied parameters for diversity
                    temperature = 0.7 + (i * 0.1)  # Vary temperature for diversity

                    generation_kwargs = {
                        "max_new_tokens": 30 + (i * 10),  # Vary length
                        "num_return_sequences": 1,
                        "temperature": temperature,
                        "do_sample": True,
                        "pad_token_id": self.tokenizer.eos_token_id,
                        "eos_token_id": self.tokenizer.eos_token_id,
                        "repetition_penalty": 1.1,
                        "top_p": 0.9,
                        "top_k": 40,
                    }

                    # Generate text using pipeline for consistency
                    outputs = self.generator(template, **generation_kwargs)

                    for output in outputs:
                        generated_text = output["generated_text"]

                        # Extract only the new generated part
                        if generated_text.startswith(template):
                            suggestion = generated_text[len(template) :].strip()
                            suggestion = self._clean_suggestion(suggestion)

                            if (
                                suggestion and len(suggestion.split()) >= 2
                            ):  # At least 2 words
                                # Create final suggestion
                                if template.endswith(", "):
                                    final_suggestion = f"{prompt}, {suggestion}"
                                elif "scene with" in template:
                                    final_suggestion = (
                                        f"A {prompt} scene with {suggestion}"
                                    )
                                elif "featuring" in template:
                                    final_suggestion = (
                                        f"{prompt} featuring {suggestion}"
                                    )
                                elif "image of" in template:
                                    final_suggestion = (
                                        f"Create an image of {prompt} that shows "
                                        f"{suggestion}"
                                    )
                                else:
                                    final_suggestion = suggestion

                                all_suggestions.append(final_suggestion)
                                break

                except Exception as e:
                    logger.warning(f"Failed to generate suggestion {i}: {e}")
                    continue

            # Fill remaining slots with fallback suggestions if needed
            while len(all_suggestions) < num_suggestions:
                fallback = self._generate_fallback_suggestion(
                    prompt, len(all_suggestions)
                )
                all_suggestions.append(fallback)

            return all_suggestions[:num_suggestions]

        except Exception as e:
            logger.error(f"Suggestion generation failed: {e}")
            # Return fallback suggestions
            return self._get_fallback_suggestions(prompt, num_suggestions)

    def _clean_suggestion(self, suggestion: str) -> str:
        """Clean and format a suggestion"""
        # Remove numbering and common artifacts
        suggestion = suggestion.strip()

        # Remove leading numbers/bullets
        while suggestion and (suggestion[0].isdigit() or suggestion[0] in ".-*"):
            suggestion = suggestion[1:].strip()

        # Split on newlines and take first meaningful line
        lines = suggestion.split("\n")
        for line in lines:
            line = line.strip()
            if len(line) > 10 and not line.isdigit():
                return line

        return suggestion.split("\n")[0].strip() if suggestion else ""

    def _generate_simple_suggestions(self, prompt: str, num_needed: int) -> List[str]:
        """Generate simple suggestions as fallback"""
        simple_prompts = [
            f"Expand on: {prompt}",
            f"Alternative to: {prompt}",
            f"Creative twist on: {prompt}",
        ]

        suggestions = []
        for simple_prompt in simple_prompts[:num_needed]:
            try:
                result = self.generate_text(simple_prompt, max_length=50)
                if result:
                    suggestions.append(result)
            except Exception:
                continue

        return suggestions

    def _get_fallback_suggestions(self, prompt: str, num_suggestions: int) -> List[str]:
        """Provide fallback suggestions when generation fails"""
        base_suggestions = [
            f"A {prompt} with magical elements",
            f"Modern take on {prompt}",
            f"Retro-style {prompt}",
            f"Minimalist {prompt}",
            f"Fantasy-themed {prompt}",
            f"{prompt} in cyberpunk style",
            f"Artistic interpretation of {prompt}",
            f"Detailed {prompt} scene",
        ]

        return base_suggestions[:num_suggestions]

    def _generate_fallback_suggestion(self, prompt: str, index: int) -> str:
        """Generate a single fallback suggestion"""
        fallback_templates = [
            f"A detailed {prompt} with vibrant colors",
            f"Creative {prompt} in an artistic style",
            f"Beautiful {prompt} with dramatic lighting",
            f"Stylized {prompt} with unique elements",
            f"Modern {prompt} with clean composition",
            f"Fantasy {prompt} with magical atmosphere",
        ]

        return fallback_templates[index % len(fallback_templates)]

    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.is_loaded and self.model is not None

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        model_info = self.AVAILABLE_MODELS.get(self.model_name, {})
        return {
            "model_name": self.model_name,
            "is_loaded": self.is_loaded,
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
            **model_info,
        }

    @classmethod
    def get_available_models(cls) -> Dict[str, Dict[str, Any]]:
        """Get list of available models"""
        return cls.AVAILABLE_MODELS
