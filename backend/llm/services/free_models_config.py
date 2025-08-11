"""
Free Local AI Models Configuration
These models run locally without API limitations, credits, or payments.
"""

# Configuration for completely free local models
FREE_LOCAL_MODELS = {
    # Lightweight models (< 1GB) - Best for basic suggestions
    "distilgpt2": {
        "name": "DistilGPT-2 (Lightweight)",
        "description": "Fast and efficient text generation - perfect for suggestions",
        "size": "80MB",
        "type": "text-generation",
        "speed": "Very Fast",
        "quality": "Good for short suggestions",
        "free": True,
        "local": True,
    },
    "gpt2": {
        "name": "GPT-2 (Standard)",
        "description": "Reliable text generation model",
        "size": "500MB",
        "type": "text-generation",
        "speed": "Fast",
        "quality": "Good creative suggestions",
        "free": True,
        "local": True,
    },
    # Mid-range models (1-2GB) - Better quality
    "microsoft/DialoGPT-medium": {
        "name": "DialoGPT Medium",
        "description": "Conversational model, excellent for creative prompts",
        "size": "300MB",
        "type": "conversational",
        "speed": "Fast",
        "quality": "Very good for creative suggestions",
        "free": True,
        "local": True,
    },
    "gpt2-medium": {
        "name": "GPT-2 Medium",
        "description": "Enhanced text generation with better creativity",
        "size": "1.5GB",
        "type": "text-generation",
        "speed": "Medium",
        "quality": "Excellent for detailed suggestions",
        "free": True,
        "local": True,
    },
    # Advanced models (2-5GB) - Highest quality
    "EleutherAI/gpt-neo-125M": {
        "name": "GPT-Neo 125M (Efficient)",
        "description": "EleutherAI's efficient model for quality generation",
        "size": "500MB",
        "type": "text-generation",
        "speed": "Fast",
        "quality": "Very good suggestions",
        "free": True,
        "local": True,
    },
    "EleutherAI/gpt-neo-1.3B": {
        "name": "GPT-Neo 1.3B (High Quality)",
        "description": "Large model for high-quality creative suggestions",
        "size": "5GB",
        "type": "text-generation",
        "speed": "Slower but worth it",
        "quality": "Excellent detailed suggestions",
        "free": True,
        "local": True,
    },
}

# Alternative free API services (no payment required)
FREE_API_ALTERNATIVES = {
    "ollama": {
        "name": "Ollama (Local Server)",
        "description": "Run Llama, Mistral, and other models locally",
        "setup": "Install Ollama desktop app",
        "models": ["llama3.2", "mistral", "phi3", "gemma2"],
        "free": True,
        "local": True,
        "url": "https://ollama.com/",
    },
    "groq": {
        "name": "Groq (Free Tier)",
        "description": "Fast inference API with generous free tier",
        "models": ["llama-3.1-70b", "mixtral-8x7b", "gemma2-9b"],
        "free_tier": "High rate limits, no payment required",
        "local": False,
        "url": "https://groq.com/",
    },
}


def get_recommended_free_model():
    """Get the best free model for moodboard suggestions"""
    return "microsoft/DialoGPT-medium"  # Best balance of speed, quality, and size


def get_lightweight_model():
    """Get the fastest loading model for immediate use"""
    return "distilgpt2"


def get_high_quality_model():
    """Get the highest quality model (requires more resources)"""
    return "EleutherAI/gpt-neo-1.3B"
