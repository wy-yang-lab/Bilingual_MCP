"""
Tests for terminology checking functionality.
"""
import pytest
from app.core.terminology import TerminologyChecker

class TestTerminologyChecker:
    """Test cases for the TerminologyChecker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.checker = TerminologyChecker()
    
    @pytest.mark.asyncio
    async def test_english_login_check(self):
        """Test that 'login' is flagged and 'sign in' is suggested."""
        text = "Please login to continue"
        issues = await self.checker.check_text(text, "en")
        
        assert len(issues) == 1
        assert issues[0]["type"] == "preferred_synonym"
        assert issues[0]["original"] == "login"
        assert issues[0]["suggestion"] == "sign in"
        assert issues[0]["start"] == 7
        assert issues[0]["end"] == 12
    
    @pytest.mark.asyncio
    async def test_japanese_login_check(self):
        """Test Japanese terminology checking."""
        text = "ログインしてください"
        issues = await self.checker.check_text(text, "jp")
        
        assert len(issues) == 1
        assert issues[0]["type"] == "preferred_synonym"
        assert issues[0]["original"] == "ログイン"
        assert issues[0]["suggestion"] == "サインイン"
    
    @pytest.mark.asyncio
    async def test_no_issues_found(self):
        """Test text with no terminology issues."""
        text = "Please sign in to continue"
        issues = await self.checker.check_text(text, "en")
        
        assert len(issues) == 0
    
    @pytest.mark.asyncio
    async def test_multiple_issues(self):
        """Test text with multiple terminology issues."""
        text = "Please login with your e-mail"
        issues = await self.checker.check_text(text, "en")
        
        assert len(issues) == 2
        # Should find both 'login' and 'e-mail'
        issue_types = [issue["original"] for issue in issues]
        assert "login" in issue_types
        assert "e-mail" in issue_types
    
    @pytest.mark.asyncio
    async def test_case_insensitive(self):
        """Test that checking is case insensitive."""
        text = "Please LOGIN to continue"
        issues = await self.checker.check_text(text, "en")
        
        assert len(issues) == 1
        assert issues[0]["original"] == "LOGIN"
    
    @pytest.mark.asyncio
    async def test_unsupported_language(self):
        """Test behavior with unsupported language."""
        text = "Bonjour le monde"
        issues = await self.checker.check_text(text, "fr")
        
        # Should return empty list for unsupported language
        assert len(issues) == 0
    
    @pytest.mark.asyncio
    async def test_placeholder_validation(self):
        """Test placeholder format validation."""
        # Valid placeholders should not trigger issues
        text = "Hello {name}, you have {count} messages"
        issues = await self.checker.check_text(text, "en")
        
        # Should not have placeholder issues (only standard term issues if any)
        placeholder_issues = [i for i in issues if i["type"] == "placeholder_mismatch"]
        assert len(placeholder_issues) == 0 