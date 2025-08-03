#!/usr/bin/env python
"""Test script for short suggestions"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from llm.services.manager import llm_manager

def test_short_suggestions():
    service_id = 'tgi_microsoft/Phi-3-mini-4k-instruct'
    print(f'Testing short suggestions with {service_id}')
    
    try:
        # Load model
        success = llm_manager.load_service(service_id, 'Phi-3 Mini')
        print(f'Load success: {success}')
        
        if success:
            # Test short suggestion generation
            print('\nGenerating short suggestions...')
            suggestions = llm_manager.get_suggestions(
                prompt='magical forest',
                service_id=service_id,
                num_suggestions=3,
                mode='default'
            )
            print(f'Number of suggestions returned: {len(suggestions)}')
            for i, suggestion in enumerate(suggestions, 1):
                print(f'  {i}. "{suggestion}"')
                
            print('\nTesting gaming mode...')
            gaming_suggestions = llm_manager.get_suggestions(
                prompt='dragon battle',
                service_id=service_id,
                num_suggestions=3,
                mode='gaming'
            )
            print(f'Gaming suggestions:')
            for i, suggestion in enumerate(gaming_suggestions, 1):
                print(f'  {i}. "{suggestion}"')
                
        # Unload model
        llm_manager.unload_service(service_id)
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_short_suggestions()
