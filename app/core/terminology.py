"""
Core terminology checking logic with database integration.
"""
import re
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

from app.core.config import settings
from app.core.database import TerminologyDatabase

logger = logging.getLogger(__name__)

@dataclass
class TermRule:
    """Represents a terminology rule."""
    pattern: str
    replacement: str
    rule_type: str  # "preferred_synonym", "forbidden_term", "consistency"
    language: str
    severity: str = "warning"

class TerminologyChecker:
    """Main terminology checking engine with database integration."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_URL.replace("sqlite:///", "")
        self.database = TerminologyDatabase(self.db_path)
        logger.info(f"Terminology checker initialized with database: {self.db_path}")
    
    async def check_text(self, text: str, language: str, context: str = "") -> List[Dict]:
        """
        Check text against terminology database and rules.
        
        Args:
            text: The text to check
            language: Language code ("en" or "jp")
            context: Additional context about where this text appears
            
        Returns:
            List of issues found
        """
        issues = []
        
        try:
            # 1. Check database terms (translations/equivalents)
            term_suggestions = self.database.find_term_suggestions(text, language)
            issues.extend(term_suggestions)
            
            # 2. Check rules (style guide violations)
            rule_violations = self.database.find_rule_violations(text, language)
            issues.extend(rule_violations)
            
            # 3. Check placeholder consistency
        placeholder_issues = self._check_placeholders(text, language)
        issues.extend(placeholder_issues)
        
            # 4. Remove duplicates and sort by position
            issues = self._deduplicate_issues(issues)
            issues.sort(key=lambda x: x['start'])
            
            logger.debug(f"Found {len(issues)} issues in '{text}' ({language})")
            
        except Exception as e:
            logger.error(f"Error checking text: {e}")
            
        return issues
    
    def _check_placeholders(self, text: str, language: str) -> List[Dict]:
        """Check for placeholder formatting issues."""
        issues = []
        
        # Common placeholder patterns
        placeholder_patterns = [
            (r'\{[^}]*\}', 'Curly brace placeholder'),  # {name}, {0}
            (r'%[sd]', 'Printf-style placeholder'),      # %s, %d
            (r'\$\{[^}]*\}', 'Shell-style placeholder'), # ${name}
            (r'%\([^)]+\)[sd]', 'Python-style placeholder'), # %(name)s
        ]
        
        for pattern, desc in placeholder_patterns:
            try:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                placeholder = match.group()
                    
                    # Basic validation - check for empty placeholders
                    if len(placeholder) <= 2 or placeholder in ['{}', '%s', '%d']:
                    issues.append({
                            "type": "placeholder_issue",
                        "original": placeholder,
                            "suggestion": "Verify placeholder content",
                        "start": match.start(),
                        "end": match.end(),
                            "severity": "warning",
                            "reason": f"Empty or minimal {desc.lower()}",
                            "source": "validation"
                    })
            except re.error:
                continue
        
        return issues
    
    def _deduplicate_issues(self, issues: List[Dict]) -> List[Dict]:
        """Remove duplicate issues based on position and type."""
        seen = set()
        unique_issues = []
        
        for issue in issues:
            # Create a key based on position and original text
            key = (issue["start"], issue["end"], issue["original"], issue["type"])
            if key not in seen:
                seen.add(key)
                unique_issues.append(issue)
        
        return unique_issues
    
    def add_terminology(self, source_lang: str, target_lang: str, 
                       source_term: str, target_term: str,
                       term_type: str = "preferred", domain: str = "") -> bool:
        """Add new terminology to the database."""
        return self.database.add_term(
            source_lang, target_lang, source_term, target_term, 
            term_type, domain
        )
    
    def add_rule(self, language: str, pattern: str, replacement: str,
                rule_type: str = "preferred_synonym", severity: str = "warning",
                description: str = "") -> bool:
        """Add new rule to the database."""
        return self.database.add_rule(
            language, pattern, replacement, rule_type, severity, description
        )
    
    def get_terminology_for_language(self, language: str, limit: int = 100) -> List[Dict]:
        """Get terminology entries for a specific language."""
        return self.database.get_terms_by_language(language, limit)
    
    def get_rules_for_language(self, language: str) -> List[Dict]:
        """Get rules for a specific language."""
        return self.database.get_rules_by_language(language)
    
    def search_terminology(self, query: str, language: str = None) -> List[Dict]:
        """Search for terminology containing the query."""
        return self.database.search_terms(query, language)
    
    def get_database_statistics(self) -> Dict:
        """Get statistics about the terminology database."""
        return self.database.get_statistics()
    
    def import_tbx_file(self, tbx_file_path: str) -> int:
        """Import a TBX file into the database."""
        # Import the TBX importer here to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
        
        try:
            from tbx_importer import TBXImporter
            importer = TBXImporter(self.db_path)
            return importer.import_tbx_file(tbx_file_path)
        except ImportError as e:
            logger.error(f"Could not import TBX importer: {e}")
            return 0
    
    def export_terminology_context(self, language: str) -> str:
        """Export terminology as context string for LLM prompts."""
        terms = self.get_terminology_for_language(language, limit=50)
        rules = self.get_rules_for_language(language)
        
        context_lines = []
        
        if language == "en":
            context_lines.append("ENGLISH UI TERMINOLOGY PREFERENCES:")
        else:
            context_lines.append("JAPANESE UI TERMINOLOGY PREFERENCES:")
        
        # Add rules
        for rule in rules[:10]:  # Limit to top 10 rules
            context_lines.append(f"- Use \"{rule['replacement']}\" instead of pattern \"{rule['pattern']}\"")
        
        # Add key terminology
        if terms:
            context_lines.append("\nKEY TERMINOLOGY:")
            for term in terms[:20]:  # Limit to top 20 terms
                context_lines.append(f"- \"{term['source']}\" → \"{term['target']}\"")
                if term['domain']:
                    context_lines[-1] += f" ({term['domain']})"
        
        return "\n".join(context_lines)

# Backwards compatibility
class LLMProvider:
    """Placeholder for LLM integration - will be implemented later."""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        logger.info("LLM Provider initialized (placeholder - no API keys configured)")
    
    async def analyze_terminology(self, text: str, language: str, context: str = "") -> List[Dict]:
        """Placeholder for LLM analysis - returns empty list for now."""
        logger.debug("LLM analysis not configured - using database-only checking")
        return [] 