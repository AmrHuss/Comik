#!/usr/bin/env python3
"""
Test script to verify the API is working locally
"""

import requests
import json

def test_api():
    base_url = "http://127.0.0.1:5000"
    
    print("Testing ManhwaVerse API...")
    print("=" * 50)
    
    # Test API root
    try:
        response = requests.get(f"{base_url}/api")
        print(f"✅ API Root: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Message: {data.get('message', 'N/A')}")
    except Exception as e:
        print(f"❌ API Root failed: {e}")
    
    # Test popular endpoint
    try:
        response = requests.get(f"{base_url}/api/popular")
        print(f"✅ Popular Endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success', False)}")
            print(f"   Count: {data.get('count', 0)}")
    except Exception as e:
        print(f"❌ Popular endpoint failed: {e}")
    
    # Test genre endpoint
    try:
        response = requests.get(f"{base_url}/api/genre?name=action")
        print(f"✅ Genre Endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success', False)}")
            print(f"   Count: {data.get('count', 0)}")
    except Exception as e:
        print(f"❌ Genre endpoint failed: {e}")
    
    print("=" * 50)
    print("API test completed!")

if __name__ == "__main__":
    test_api()
