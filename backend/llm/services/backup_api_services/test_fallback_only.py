#!/usr/bin/env python
"""Test script for fallback suggestions only"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

def test_fallback_suggestions():
    """Test just the fallback suggestions without loading the problematic manager"""
    
    # Simulate fallback suggestions for default mode
    def get_fallback_suggestions(prompt, num_suggestions, mode='default'):
        if mode.lower() == 'gaming':
            base_suggestions = [
                "with cyberpunk neon lighting",
                "dark fantasy style",
                "retro pixel art aesthetic", 
                "futuristic sci-fi elements",
                "post-apocalyptic atmosphere",
                "epic battle scene",
                "glowing magical effects",
                "ancient ruins background"
            ]
        else:
            base_suggestions = [
                "with vibrant color palette",
                "minimalist modern style",
                "vintage retro aesthetic",
                "dramatic lighting effects",
                "abstract geometric patterns",
                "soft dreamy atmosphere",
                "bold artistic composition",
                "elegant sophisticated design"
            ]
        
        return base_suggestions[:num_suggestions]
    
    print("Testing fallback suggestions (short prompt enhancements):")
    
    # Test default mode
    print("\n=== Default Mode ===")
    suggestions = get_fallback_suggestions("magical forest", 3, "default")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. magical forest {suggestion}")
    
    # Test gaming mode
    print("\n=== Gaming Mode ===")
    gaming_suggestions = get_fallback_suggestions("dragon battle", 3, "gaming")
    for i, suggestion in enumerate(gaming_suggestions, 1):
        print(f"  {i}. dragon battle {suggestion}")
        
    print("\nThese are the new short suggestion format!")
    print("Users can select these to enhance their prompts before generating images.")

if __name__ == '__main__':
    test_fallback_suggestions()
