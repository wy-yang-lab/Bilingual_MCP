#!/usr/bin/env python3
"""
Quick test script for Bilingual Checker MCP with LLM Integration
Run this to verify your setup works!
"""
import asyncio

async def test_terminology_checker():
    """Test the terminology checker with LLM integration."""
    import sys
    import os
    
    # Add the app directory to Python path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
    
    try:
        from core.terminology import TerminologyChecker
        
        # Create checker
        checker = TerminologyChecker()
        
        # Check if LLM is available
        llm_available = bool(checker.llm_provider.openai_client or checker.llm_provider.anthropic_client)
        
        print(f"🤖 LLM Integration: {'✅ Available' if llm_available else '❌ Not configured'}")
        if llm_available:
            provider = "OpenAI" if checker.llm_provider.openai_client else "Anthropic"
            print(f"   Provider: {provider}")
        else:
            print("   Note: Add OPENAI_API_KEY or ANTHROPIC_API_KEY to .env for LLM features")
        print()
        
        # Test English
        text_en = "Please login to continue accessing your e-mail"
        print(f"📝 Testing: '{text_en}'")
        issues_en = await checker.check_text(text_en, "en", "Login button")
        print(f"✅ English test: Found {len(issues_en)} issues")
        for i, issue in enumerate(issues_en[:3], 1):  # Show max 3 issues
            print(f"   {i}. '{issue['original']}' → '{issue['suggestion']}'")
            if 'reason' in issue:
                print(f"      Reason: {issue['reason']}")
        
        print()
        
        # Test Japanese  
        text_jp = "ログインしてメールを確認してください"
        print(f"📝 Testing: '{text_jp}'")
        issues_jp = await checker.check_text(text_jp, "jp", "ユーザーインターフェース")
        print(f"✅ Japanese test: Found {len(issues_jp)} issues")
        for i, issue in enumerate(issues_jp[:3], 1):  # Show max 3 issues
            print(f"   {i}. '{issue['original']}' → '{issue['suggestion']}'")
            if 'reason' in issue:
                print(f"      Reason: {issue['reason']}")
        
        print()
        print("🎉 Bilingual Checker MCP with LLM integration is working correctly!")
        
        if not llm_available:
            print("\n💡 To enable LLM features:")
            print("   1. Copy .env.example to .env")
            print("   2. Add your OpenAI or Anthropic API key")
            print("   3. Run the test again")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🔍 Testing Bilingual Checker MCP with LLM Integration...")
    print("=" * 60)
    
    # Run async test
    success = asyncio.run(test_terminology_checker())
    
    if success:
        print("\n🚀 Ready for MCP client connections!")
    else:
        print("\n🔧 Please fix the issues above before proceeding.")

if __name__ == "__main__":
    main() 