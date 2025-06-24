#!/usr/bin/env python3
"""
Test if the database is ready for actual terminology checking
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import TerminologyDatabase

def test_terminology_checking():
    """Test actual terminology checking functionality."""
    print("🔍 Testing Bilingual Terminology Database")
    print("=" * 50)
    
    # Initialize database
    db = TerminologyDatabase(db_path="terms.db")
    
    # Get basic stats
    stats = db.get_statistics()
    print(f"📊 Database Statistics:")
    print(f"   Total terms: {stats.get('total_terms', 0):,}")
    print(f"   Languages: {stats.get('languages', [])}")
    print(f"   Domains: {stats.get('domain_count', 0)}")
    
    # Test actual terminology lookups
    print(f"\n🔍 Testing Terminology Lookups:")
    
    # Test common UI terms that should be in Microsoft terminology
    test_terms = [
        ("button", "en"),
        ("menu", "en"), 
        ("file", "en"),
        ("save", "en"),
        ("cancel", "en")
    ]
    
    for term, lang in test_terms:
        suggestions = db.find_term_suggestions(term, lang)
        if suggestions:
            print(f"   ✅ '{term}' found {len(suggestions)} suggestions:")
            for suggestion in suggestions[:2]:  # Show first 2
                print(f"      → {suggestion['suggestion']}")
        else:
            print(f"   ❌ '{term}' no suggestions found")
    
    # Test Japanese terms
    print(f"\n🔍 Testing Japanese Terms:")
    jp_terms = [
        ("ボタン", "jp"),
        ("メニュー", "jp"),
        ("ファイル", "jp")
    ]
    
    for term, lang in jp_terms:
        suggestions = db.find_term_suggestions(term, lang)
        if suggestions:
            print(f"   ✅ '{term}' found {len(suggestions)} suggestions:")
            for suggestion in suggestions[:2]:
                print(f"      → {suggestion['suggestion']}")
        else:
            print(f"   ❌ '{term}' no suggestions found")
    
    # Sample some actual terms from database
    print(f"\n📋 Sample Terms from Database:")
    en_terms = db.get_terms_by_language("en", limit=5)
    for i, term in enumerate(en_terms[:5], 1):
        # Handle different possible key names
        source = term.get('source_term', term.get('term', term.get('text', 'Unknown')))
        target = term.get('target_term', term.get('translation', term.get('suggestion', 'Unknown')))
        print(f"   {i}. {source} → {target}")
    
    print(f"\n✅ Database is {'READY' if stats.get('total_terms', 0) > 100000 else 'NOT READY'} for production use!")

if __name__ == "__main__":
    test_terminology_checking() 