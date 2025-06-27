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
        # Initialize placeholder LLM provider (will be configured when API keys are supplied)
        self.llm_provider = LLMProvider()
        logger.info(f"Terminology checker initialized with database: {self.db_path}")
    
    async def check_text(self, text: str, language: str, context: str = "") -> List[Dict]:
        """
        Check text against terminology database and rules, with optional LLM analysis.
        
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
            
            # 4. LLM analysis (if available and configured)
            if self.llm_provider and (settings.OPENAI_API_KEY or settings.ANTHROPIC_API_KEY):
                terminology_context = self.export_terminology_context(language)
                llm_issues = await self.llm_provider.analyze_terminology(
                    text, language, context, terminology_context
                )
                issues.extend(llm_issues)
            
            # 5. Remove duplicates and sort by position
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

# LLM Integration
class LLMProvider:
    """LLM integration for advanced terminology analysis."""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize OpenAI client if API key is available
        if settings.OPENAI_API_KEY:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized")
            except ImportError:
                logger.warning("OpenAI package not installed")
        
        # Initialize Anthropic client if API key is available
        if settings.ANTHROPIC_API_KEY:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                logger.info("Anthropic client initialized")
            except ImportError:
                logger.warning("Anthropic package not installed")
        
        if not self.openai_client and not self.anthropic_client:
            logger.info("No LLM providers configured - using database-only checking")
    
    async def analyze_terminology(self, text: str, language: str, context: str = "", 
                                terminology_context: str = "") -> List[Dict]:
        """Use LLM to analyze terminology and suggest improvements."""
        if not self.openai_client and not self.anthropic_client:
            return []
        
        try:
            # Use OpenAI GPT-4o as primary choice
            if self.openai_client:
                return await self._analyze_with_openai(text, language, context, terminology_context)
            elif self.anthropic_client:
                return await self._analyze_with_anthropic(text, language, context, terminology_context)
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return []
        
        return []
    
    async def _analyze_with_openai(self, text: str, language: str, context: str, 
                                 terminology_context: str) -> List[Dict]:
        """Analyze terminology using OpenAI GPT-4o."""
        system_prompt = self._get_system_prompt(language, terminology_context)
        user_prompt = self._get_user_prompt(text, language, context)
        
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4o",  # Use GPT-4o
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            return self._parse_llm_response(result, text)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return []
    
    async def _analyze_with_anthropic(self, text: str, language: str, context: str,
                                    terminology_context: str) -> List[Dict]:
        """Analyze terminology using Anthropic Claude."""
        system_prompt = self._get_system_prompt(language, terminology_context)
        user_prompt = self._get_user_prompt(text, language, context)
        
        try:
            response = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.1,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            
            result = response.content[0].text
            return self._parse_llm_response(result, text)
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return []
    
    def _get_system_prompt(self, language: str, terminology_context: str) -> str:
        """Generate system prompt for LLM analysis."""
        if language == "en":
            base_prompt = """You are a professional UI/UX terminology expert specializing in English interface text. 
Analyze the provided text for terminology consistency, clarity, and user experience best practices.

Focus on:
1. Consistency with established UI terminology
2. Clarity and user-friendliness
3. Professional tone and style
4. Accessibility considerations
5. Industry standard terminology

Provide suggestions as a JSON object with this structure:
{
    "issues": [
        {
            "type": "terminology_suggestion",
            "original": "exact text from input",
            "suggestion": "recommended replacement",
            "start": 0,
            "end": 5,
            "severity": "warning|error|info",
            "reason": "explanation of the issue",
            "source": "llm_analysis"
        }
    ]
}"""
        else:
            base_prompt = """You are a professional UI/UX terminology expert specializing in Japanese interface text.
Analyze the provided text for terminology consistency, clarity, and user experience best practices.

Focus on:
1. Consistency with established Japanese UI terminology
2. Appropriate formality level (polite form)
3. Natural Japanese expression
4. Katakana vs. Hiragana vs. Kanji usage
5. Industry standard Japanese terminology

Provide suggestions as a JSON object with this structure:
{
    "issues": [
        {
            "type": "terminology_suggestion", 
            "original": "exact text from input",
            "suggestion": "recommended replacement",
            "start": 0,
            "end": 5,
            "severity": "warning|error|info",
            "reason": "explanation of the issue",
            "source": "llm_analysis"
        }
    ]
}"""
        
        if terminology_context:
            base_prompt += f"\n\nRelevant terminology context:\n{terminology_context}"
        
        return base_prompt
    
    def _get_user_prompt(self, text: str, language: str, context: str) -> str:
        """Generate user prompt for LLM analysis."""
        prompt = f"Analyze this {language.upper()} text: \"{text}\""
        if context:
            prompt += f"\n\nContext: {context}"
        return prompt
    
    def _parse_llm_response(self, response: str, original_text: str) -> List[Dict]:
        """Parse LLM response into structured issues."""
        try:
            import json
            data = json.loads(response)
            issues = data.get("issues", [])
            
            # Validate and clean up issues
            valid_issues = []
            for issue in issues:
                if all(key in issue for key in ["type", "original", "suggestion", "severity", "reason"]):
                    # Add default values for missing fields
                    if "start" not in issue:
                        issue["start"] = original_text.find(issue["original"])
                    if "end" not in issue:
                        issue["end"] = issue["start"] + len(issue["original"])
                    if "source" not in issue:
                        issue["source"] = "llm_analysis"
                    
                    valid_issues.append(issue)
            
            return valid_issues
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return []
    
    def _get_terminology_context(self, language: str, checker_instance=None) -> str:
        """Get terminology context for LLM prompts."""
        if checker_instance:
            return checker_instance.export_terminology_context(language)
        return "" 