#!/usr/bin/env python3
"""
Test the updated LLM service manager with AI suggestions
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

def test_ai_suggestions():
    """Test AI suggestion generation"""
    print("🧠 Testing AI Suggestion Generation")
    print("=" * 50)
    
    test_prompts = [
        ("futuristic city", "gaming", "short"),
        ("magical forest", "default", "long"),
        ("space battle", "gaming", "short")
    ]
    
    for prompt, mode, suggestion_type in test_prompts:
        print(f"\n🎯 Testing: '{prompt}' (mode: {mode}, type: {suggestion_type})")
        print("-" * 40)
        
        try:
            suggestions = llm_manager.get_suggestions(
                prompt=prompt,
                mode=mode,
                suggestion_type=suggestion_type,
                num_suggestions=3
            )
            
            print(f"✅ Generated {len(suggestions)} suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n📊 Service Status:")
    print(f"Active Service: {llm_manager.get_active_service()}")
    services = llm_manager.list_services()
    loaded_services = [s for s, info in services.items() if info.get('loaded', False)]
    print(f"Loaded Services: {loaded_services}")

if __name__ == "__main__":
    test_ai_suggestions()
