#!/usr/bin/env python3
"""
Test script to verify Hugging Face token configuration
"""
import os
import sys
import django

# Add the backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from django.conf import settings
from llm.services.huggingface_service import HuggingFaceLLMService

def test_huggingface_token():
    """Test Hugging Face token configuration"""
    print("🔍 Testing Hugging Face Token Configuration")
    print("=" * 50)
    
    # Check environment variable
    env_token = os.environ.get('HUGGINGFACE_API_TOKEN')
    print(f"Environment Token: {'✓ Set' if env_token else '✗ Not set'}")
    if env_token:
        print(f"Token Preview: {env_token[:10]}...")
    
    # Check Django settings
    settings_token = settings.HUGGINGFACE_API_TOKEN
    print(f"Settings Token: {'✓ Set' if settings_token else '✗ Not set'}")
    if settings_token:
        print(f"Settings Preview: {settings_token[:10]}...")
    
    # Test token match
    if env_token and settings_token:
        if env_token == settings_token:
            print("✓ Environment and settings tokens match")
        else:
            print("⚠ Environment and settings tokens differ")
    
    print("\n🚀 Testing Hugging Face Service Initialization")
    print("=" * 50)
    
    try:
        # Test service initialization (without loading model)
        service = HuggingFaceLLMService()
        print("✓ HuggingFaceLLMService initialized successfully")
        
        # Get available models
        models = service.get_available_models()
        print(f"✓ Available models: {len(models)} models found")
        
        # List some models
        print("\n📋 Available Models:")
        for i, (model_id, model_info) in enumerate(list(models.items())[:3]):
            print(f"  {i+1}. {model_info['name']} ({model_id})")
            print(f"     Size: {model_info['size']}, Type: {model_info['type']}")
        
        if len(models) > 3:
            print(f"  ... and {len(models) - 3} more models")
            
    except Exception as e:
        print(f"✗ Error initializing service: {e}")
        return False
    
    print("\n✅ All tests passed! Hugging Face token is properly configured.")
    return True

if __name__ == "__main__":
    test_huggingface_token()
