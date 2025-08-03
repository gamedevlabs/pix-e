#!/usr/bin/env python3
"""
Test DeepSeek model loading with the fixed TGI service
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

def test_deepseek_loading():
    """Test DeepSeek model loading with fixed service"""
    print("🔍 Testing DeepSeek Model Loading (Fixed)")
    print("=" * 50)
    
    # Test via service manager
    service_id = 'tgi_deepseek_ai_DeepSeek_R1_Distill_Qwen_32B'
    print(f"🚀 Attempting to load service: {service_id}")
    
    try:
        success = llm_manager.load_service(service_id)
        if success:
            print("✅ Service loaded successfully!")
            
            # Test generation
            print("\n🧠 Testing text generation...")
            try:
                suggestions = llm_manager.get_suggestions(
                    prompt="futuristic city",
                    service_id=service_id,
                    num_suggestions=2
                )
                
                print(f"✅ Generated {len(suggestions)} suggestions:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"  {i}. {suggestion}")
                    
            except Exception as e:
                print(f"❌ Generation failed: {e}")
        else:
            print("❌ Service loading returned False")
            
    except Exception as e:
        print(f"❌ Service loading failed: {e}")
        print(f"   Error type: {type(e).__name__}")
    
    # Check service status
    print(f"\n📊 Final Status:")
    services = llm_manager.list_services()
    if service_id in services:
        service_info = services[service_id]
        print(f"   Loaded: {service_info.get('loaded', False)}")
        print(f"   Status: {service_info.get('status', 'unknown')}")
    else:
        print(f"   Service {service_id} not found in services list")

if __name__ == "__main__":
    test_deepseek_loading()
