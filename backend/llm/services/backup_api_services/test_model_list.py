#!/usr/bin/env python3
"""
Test the updated model list with TGI API models
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

def test_model_list():
    """Test the updated model list"""
    print("🔍 Testing Updated Model List")
    print("=" * 50)
    
    services = llm_manager.list_services()
    
    print(f"📋 Available Services: {len(services)} total")
    print("-" * 40)
    
    # Group by type
    local_models = []
    api_models = []
    
    for service_id, info in services.items():
        if info.get('local', False):
            local_models.append((service_id, info))
        else:
            api_models.append((service_id, info))
    
    print(f"🖥️  LOCAL MODELS ({len(local_models)}):")
    for service_id, info in local_models:
        status = "✅ Loaded" if info.get('loaded') else "⭕ Available"
        print(f"  {status} {info['name']} ({info['size']})")
        print(f"     ID: {service_id}")
        print(f"     Description: {info['description']}")
        print()
    
    print(f"🌐 API MODELS ({len(api_models)}):")
    for service_id, info in api_models:
        status = "✅ Loaded" if info.get('loaded') else "⭕ Available"
        requires_auth = "🔐 Requires Auth" if info.get('requires_auth') else "🔓 No Auth"
        print(f"  {status} {info['name']} ({info['size']}) {requires_auth}")
        print(f"     ID: {service_id}")
        print(f"     Provider: {info['provider']}")
        print(f"     Description: {info['description']}")
        print()

if __name__ == "__main__":
    test_model_list()
