#!/usr/bin/env python3
"""
Test the cleaned up model dropdown - should show only essential models
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

def test_clean_model_list():
    """Test that only essential models appear in the dropdown"""
    print("🎯 Testing Cleaned Model Dropdown")
    print("=" * 50)
    
    services = llm_manager.list_services()
    
    print(f"📊 Total available services: {len(services)}")
    print("\n🔍 Available Models:")
    
    # Group by provider
    providers = {}
    for service_id, info in services.items():
        provider = info.get('provider', 'Unknown')
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(info)
    
    for provider, models in providers.items():
        print(f"\n📋 {provider}:")
        for model in models:
            status = "✅ Loaded" if model.get('loaded') else "⚪ Available"
            free_tag = "🆓" if model.get('free', True) else "💰"
            local_tag = "🏠" if model.get('local', False) else "☁️"
            print(f"  {free_tag}{local_tag} {model['name']} ({model['size']}) - {status}")
            print(f"     📝 {model['description']}")
    
    # Count by type
    hf_models = [s for s in services.values() if 'Hugging Face' in s.get('provider', '')]
    other_models = [s for s in services.values() if 'Hugging Face' not in s.get('provider', '')]
    
    print(f"\n📈 Summary:")
    print(f"  • Hugging Face Models: {len(hf_models)}")
    print(f"  • Other Services: {len(other_models)}")
    print(f"  • Total: {len(services)}")
    
    if len(hf_models) == 4:
        print("✅ Perfect! Model list cleaned to essential 4 HF models")
    else:
        print(f"⚠️  Expected 4 HF models, found {len(hf_models)}")

if __name__ == "__main__":
    test_clean_model_list()
