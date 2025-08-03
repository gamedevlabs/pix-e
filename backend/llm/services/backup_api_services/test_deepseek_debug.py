#!/usr/bin/env python3
"""
Debug DeepSeek model loading issues
"""
import os
import sys
import django

# Add the backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from llm.services.manager import llm_manager
from llm.services.tgi_service import TGIService

def debug_deepseek_loading():
    """Debug DeepSeek model loading"""
    print("🔍 Debugging DeepSeek Model Loading")
    print("=" * 50)
    
    # Test direct TGI service initialization
    print("1. Testing direct TGI service initialization...")
    try:
        deepseek_service = TGIService('deepseek-ai/DeepSeek-R1-Distill-Qwen-32B')
        print("✅ TGI Service initialized successfully")
        print(f"   Model ID: {deepseek_service.model_id}")
        print(f"   Model Name: {deepseek_service.model_name}")
        print(f"   Endpoint: {deepseek_service.model_info.get('endpoint', 'Not found')}")
    except Exception as e:
        print(f"❌ TGI Service initialization failed: {e}")
        return
    
    # Test model loading
    print("\n2. Testing model loading...")
    try:
        success = deepseek_service.load_model()
        if success:
            print("✅ Model loaded successfully")
        else:
            print("❌ Model loading returned False")
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Full traceback:")
        traceback.print_exc()
    
    # Test via service manager
    print("\n3. Testing via service manager...")
    service_id = 'tgi_deepseek_ai_DeepSeek_R1_Distill_Qwen_32B'
    try:
        success = llm_manager.load_service(service_id)
        if success:
            print("✅ Service manager loaded successfully")
        else:
            print("❌ Service manager loading returned False")
    except Exception as e:
        print(f"❌ Service manager loading failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Full traceback:")
        traceback.print_exc()
    
    # Check environment variables
    print("\n4. Checking environment...")
    hf_token = os.environ.get('HUGGINGFACE_API_TOKEN')
    if hf_token:
        print(f"✅ HUGGINGFACE_API_TOKEN is set: {hf_token[:10]}...")
    else:
        print("❌ HUGGINGFACE_API_TOKEN is not set")
    
    # Test basic HTTP connectivity
    print("\n5. Testing HTTP connectivity...")
    try:
        import requests
        endpoint = 'https://api-inference.huggingface.co/models/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B'
        headers = {'Authorization': f'Bearer {hf_token}'} if hf_token else {}
        
        response = requests.get(endpoint, headers=headers, timeout=10)
        print(f"   HTTP Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Model endpoint is accessible")
        elif response.status_code == 401:
            print("❌ Authentication failed - check your HF token")
        elif response.status_code == 403:
            print("❌ Access forbidden - model may require approval")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ HTTP test failed: {e}")

if __name__ == "__main__":
    debug_deepseek_loading()
