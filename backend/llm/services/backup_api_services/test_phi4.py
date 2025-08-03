#!/usr/bin/env python3
"""
Test Phi-4 model loading (simpler test)
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

def test_phi4_loading():
    """Test Phi-4 model loading"""
    print("🔍 Testing Phi-4 Model Loading")
    print("=" * 40)
    
    # Test via service manager
    service_id = 'tgi_microsoft_phi_4'
    print(f"🚀 Attempting to load service: {service_id}")
    
    try:
        success = llm_manager.load_service(service_id)
        if success:
            print("✅ Phi-4 loaded successfully!")
            return True
        else:
            print("❌ Phi-4 loading returned False")
            return False
            
    except Exception as e:
        print(f"❌ Phi-4 loading failed: {e}")
        return False

def test_model_list():
    """Test that the models appear in the list"""
    print("\n📋 Testing Model List")
    print("=" * 40)
    
    services = llm_manager.list_services()
    tgi_models = {k: v for k, v in services.items() if k.startswith('tgi_')}
    
    print(f"Found {len(tgi_models)} TGI models:")
    for service_id, info in tgi_models.items():
        print(f"  • {info['name']} ({service_id})")
        print(f"    Status: {info.get('status', 'unknown')}")

if __name__ == "__main__":
    test_model_list()
    test_phi4_loading()
