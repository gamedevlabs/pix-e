#!/usr/bin/env python3
"""
Simple test for DeepSeek API connectivity
"""
import os
import sys
import requests

# Test basic API connectivity
def test_deepseek_api():
    print("🔍 Testing DeepSeek API Connectivity")
    print("=" * 40)
    
    # Check token
    hf_token = os.environ.get('HUGGINGFACE_API_TOKEN')
    if not hf_token:
        print("❌ No HUGGINGFACE_API_TOKEN found")
        return
    
    print(f"✅ Token found: {hf_token[:10]}...")
    
    # Test endpoint
    endpoint = 'https://api-inference.huggingface.co/models/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B'
    headers = {
        'Authorization': f'Bearer {hf_token}',
        'Content-Type': 'application/json'
    }
    
    # Simple test payload
    payload = {
        "inputs": "Hello",
        "parameters": {
            "max_new_tokens": 10,
            "temperature": 0.1
        }
    }
    
    print(f"🌐 Testing endpoint: {endpoint}")
    
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API call successful!")
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get('generated_text', 'No text found')
                print(f"📝 Generated: {generated_text}")
            else:
                print(f"📝 Response: {result}")
        
        elif response.status_code == 503:
            print("⏳ Model is loading (503) - This is normal for cold start")
            print("   Response:", response.text[:200])
        
        elif response.status_code == 401:
            print("❌ Authentication failed (401)")
            print("   Check your Hugging Face token")
        
        elif response.status_code == 403:
            print("❌ Access forbidden (403)")
            print("   Model may require approval or have usage limits")
            print("   Response:", response.text[:200])
        
        else:
            print(f"❌ API Error ({response.status_code})")
            print("   Response:", response.text[:200])
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (30s)")
        print("   This might happen if the model is cold-starting")
    
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_deepseek_api()
