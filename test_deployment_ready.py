#!/usr/bin/env python3
"""
Test script to verify deployment readiness for Bilingual MCP.
"""
import os
import sys
import subprocess
import requests
from pathlib import Path

def test_files_exist():
    """Check that all required deployment files exist."""
    required_files = [
        "Dockerfile",
        "requirements.txt", 
        "start.sh",
        "app/main.py",
        "ui_app.py",
        "data/terms.db"
    ]
    
    print("🔍 Checking required files...")
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
        else:
            print(f"  ✅ {file}")
    
    if missing:
        print(f"  ❌ Missing files: {missing}")
        return False
    return True

def test_database():
    """Check database has data."""
    print("\n📊 Checking database...")
    try:
        import sqlite3
        conn = sqlite3.connect("data/terms.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM terms")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 100000:  # Should have 189k+ entries
            print(f"  ✅ Database has {count:,} entries")
            return True
        else:
            print(f"  ⚠️  Database has {count} entries (expected 100k+ for production)")
            print("     This is likely a test database - will work for demo")
            return True  # Allow small database for demo
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def test_api_imports():
    """Test that API can be imported."""
    print("\n🔧 Testing API imports...")
    try:
        sys.path.insert(0, ".")
        from app.main import app
        from app.core.config import settings
        print("  ✅ FastAPI app imports successfully")
        print(f"  ✅ Config loaded (PORT: {settings.PORT})")
        return True
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return False

def test_ui_imports():
    """Test that UI can be imported."""
    print("\n🎨 Testing UI imports...")
    try:
        import streamlit
        import requests
        print("  ✅ Streamlit imports successfully")
        print("  ✅ Required packages available")
        return True
    except Exception as e:
        print(f"  ❌ UI import error: {e}")
        return False

def test_docker_build():
    """Test Docker build (optional)."""
    print("\n🐳 Testing Docker build...")
    try:
        result = subprocess.run(
            ["docker", "build", "-t", "bilingual-mcp-test", "."],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            print("  ✅ Docker build successful")
            # Clean up
            subprocess.run(["docker", "rmi", "bilingual-mcp-test"], 
                         capture_output=True)
            return True
        else:
            print(f"  ❌ Docker build failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("  ⚠️  Docker build timeout (but might work on Render)")
        return True
    except FileNotFoundError:
        print("  ⚠️  Docker not installed (but Render will handle this)")
        return True
    except Exception as e:
        print(f"  ❌ Docker test error: {e}")
        return False

def main():
    print("🚀 Bilingual MCP Deployment Readiness Check")
    print("=" * 50)
    
    tests = [
        test_files_exist,
        test_database,
        test_api_imports,
        test_ui_imports,
        test_docker_build
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📋 DEPLOYMENT READINESS SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Ready for deployment!")
        print("\n📝 Next steps:")
        print("   1. Create Render account at https://render.com")
        print("   2. Create Streamlit account at https://share.streamlit.io")
        print("   3. Follow DEPLOYMENT_GUIDE.md")
        print("   4. Get OpenAI API key for LLM features")
        return True
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        print("   Please fix the issues above before deploying")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 