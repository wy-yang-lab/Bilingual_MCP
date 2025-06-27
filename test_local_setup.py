#!/usr/bin/env python3
"""
Test script to verify local setup is working
"""
import requests
import json

def test_api():
    """Test the FastAPI backend"""
    print("🧪 Testing FastAPI Backend...")
    
    try:
        # Test health endpoint
        response = requests.get("http://127.0.0.1:8000/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
            
        # Test root endpoint
        response = requests.get("http://127.0.0.1:8000/")
        if response.status_code == 200:
            print("✅ Root endpoint working")
            data = response.json()
            print(f"   Version: {data.get('version')}")
            print(f"   LLM Providers: {data.get('llm_providers')}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
            
        # Test terminology checking endpoint
        test_payload = {
            "text": "Please login to access your e-mail account",
            "lang": "en",
            "context": "login form"
        }
        
        headers = {
            "Authorization": "Bearer TEST_TOKEN",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "http://127.0.0.1:8000/context-request",
            json=test_payload,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Terminology checking endpoint working")
            data = response.json()
            print(f"   Issues found: {len(data.get('issues', []))}")
            print(f"   LLM used: {data.get('llm_used')}")
        else:
            print(f"❌ Terminology endpoint failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
        print("🎉 All API tests passed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server at http://127.0.0.1:8000")
        print("   Make sure the FastAPI server is running")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_streamlit():
    """Test if Streamlit is accessible"""
    print("\n🧪 Testing Streamlit UI...")
    
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit UI is accessible at http://localhost:8501")
            return True
        else:
            print(f"❌ Streamlit returned status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Streamlit at http://localhost:8501")
        print("   Make sure Streamlit is running: streamlit run ui_app.py --server.port 8501")
        return False
    except Exception as e:
        print(f"❌ Streamlit test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Bilingual MCP Local Setup")
    print("=" * 50)
    
    api_ok = test_api()
    streamlit_ok = test_streamlit()
    
    print("\n" + "=" * 50)
    if api_ok and streamlit_ok:
        print("🎉 SUCCESS: Both API and UI are working!")
        print("\n📝 Next steps:")
        print("   1. Open http://localhost:8501 in your browser")
        print("   2. Test the terminology checker with sample text")
        print("   3. Add your OpenAI API key to enable LLM features")
    elif api_ok:
        print("⚠️  PARTIAL: API working, but Streamlit needs to be started")
        print("   Run: streamlit run ui_app.py --server.port 8501")
    else:
        print("❌ FAILED: Issues detected with the setup")
        print("   Check the error messages above") 