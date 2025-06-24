"""
Database interface for terminology management
"""
import sqlite3
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TerminologyDatabase:
    """Interface to terminology database."""
    
    def __init__(self, db_path: str = "data/terms.db"):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Ensure database file exists and create if needed."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not db_file.exists():
            logger.info(f"Creating new terminology database: {self.db_path}")
            self._create_empty_database()
    
    def _create_empty_database(self):
        """Create empty database with default structure."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Terms table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS terms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_lang TEXT NOT NULL,
                    target_lang TEXT NOT NULL,
                    source_term TEXT NOT NULL,
                    target_term TEXT NOT NULL,
                    term_type TEXT DEFAULT 'preferred',
                    domain TEXT,
                    source_file TEXT,
                    definition TEXT,
                    usage_note TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Rules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    language TEXT NOT NULL,
                    pattern TEXT NOT NULL,
                    replacement TEXT NOT NULL,
                    rule_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'warning',
                    description TEXT,
                    source_file TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_term ON terms(source_term)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_lang ON terms(source_lang)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pattern ON rules(pattern)")
            
            # Insert default rules
            default_rules = [
                ('en', r'\blogin\b', 'sign in', 'preferred_synonym', 'warning', 'Prefer "sign in" over "login"'),
                ('en', r'\bLogout\b', 'Sign out', 'preferred_synonym', 'warning', 'Prefer "Sign out" over "Logout"'),
                ('en', r'\be-mail\b', 'email', 'preferred_synonym', 'warning', 'Use "email" without hyphen'),
                ('en', r'\bOk\b', 'OK', 'preferred_synonym', 'info', 'Use "OK" in all caps'),
                ('jp', r'ログイン', 'サインイン', 'preferred_synonym', 'warning', 'Use "サインイン" instead of "ログイン"'),
                ('jp', r'ログアウト', 'サインアウト', 'preferred_synonym', 'warning', 'Use "サインアウト" instead of "ログアウト"'),
            ]
            
            cursor.executemany("""
                INSERT INTO rules (language, pattern, replacement, rule_type, severity, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, default_rules)
            
            conn.commit()
            logger.info("Created database with default terminology rules")
    
    def find_term_suggestions(self, text: str, source_lang: str) -> List[Dict]:
        """Find terminology suggestions for given text."""
        suggestions = []
        
        # Check database terms
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Find exact matches first
            cursor.execute("""
                SELECT source_term, target_term, term_type, domain, definition
                FROM terms 
                WHERE source_lang = ? AND LOWER(?) LIKE '%' || LOWER(source_term) || '%'
                ORDER BY term_type, LENGTH(source_term) DESC
            """, (source_lang, text))
            
            for row in cursor.fetchall():
                source_term, target_term, term_type, domain, definition = row
                
                # Find position in text
                pattern = re.compile(re.escape(source_term), re.IGNORECASE)
                for match in pattern.finditer(text):
                    suggestions.append({
                        "type": "terminology_match",
                        "original": match.group(),
                        "suggestion": target_term,
                        "start": match.start(),
                        "end": match.end(),
                        "severity": "info" if term_type == "preferred" else "warning",
                        "reason": f"Terminology database suggestion ({domain})" if domain else "Terminology database suggestion",
                        "definition": definition or "",
                        "source": "database"
                    })
        
        return suggestions
    
    def find_rule_violations(self, text: str, language: str) -> List[Dict]:
        """Find rule violations in text."""
        violations = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT pattern, replacement, rule_type, severity, description
                FROM rules 
                WHERE language = ?
            """, (language,))
            
            for row in cursor.fetchall():
                pattern, replacement, rule_type, severity, description = row
                
                try:
                    # Apply regex pattern
                    regex = re.compile(pattern, re.IGNORECASE)
                    for match in regex.finditer(text):
                        violations.append({
                            "type": rule_type,
                            "original": match.group(),
                            "suggestion": replacement,
                            "start": match.start(),
                            "end": match.end(),
                            "severity": severity,
                            "reason": description or f"Rule-based suggestion: {pattern} -> {replacement}",
                            "source": "rules"
                        })
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")
        
        return violations
    
    def add_term(self, source_lang: str, target_lang: str, source_term: str, 
                 target_term: str, term_type: str = "preferred", domain: str = "",
                 definition: str = "") -> bool:
        """Add a new term to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO terms 
                    (source_lang, target_lang, source_term, target_term, term_type, domain, definition)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (source_lang, target_lang, source_term, target_term, term_type, domain, definition))
                conn.commit()
            
            logger.info(f"Added term: {source_term} ({source_lang}) -> {target_term} ({target_lang})")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding term: {e}")
            return False
    
    def add_rule(self, language: str, pattern: str, replacement: str, 
                 rule_type: str = "preferred_synonym", severity: str = "warning",
                 description: str = "") -> bool:
        """Add a new rule to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO rules 
                    (language, pattern, replacement, rule_type, severity, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (language, pattern, replacement, rule_type, severity, description))
                conn.commit()
            
            logger.info(f"Added rule: {pattern} -> {replacement} ({language})")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding rule: {e}")
            return False
    
    def get_terms_by_language(self, language: str, limit: int = 100) -> List[Dict]:
        """Get terms for a specific language."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT source_term, target_term, term_type, domain, definition
                FROM terms 
                WHERE source_lang = ?
                ORDER BY source_term
                LIMIT ?
            """, (language, limit))
            
            return [
                {
                    "source": row[0],
                    "target": row[1], 
                    "type": row[2],
                    "domain": row[3] or "",
                    "definition": row[4] or ""
                }
                for row in cursor.fetchall()
            ]
    
    def get_rules_by_language(self, language: str) -> List[Dict]:
        """Get rules for a specific language."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pattern, replacement, rule_type, severity, description
                FROM rules 
                WHERE language = ?
                ORDER BY rule_type, pattern
            """, (language,))
            
            return [
                {
                    "pattern": row[0],
                    "replacement": row[1],
                    "type": row[2], 
                    "severity": row[3],
                    "description": row[4] or ""
                }
                for row in cursor.fetchall()
            ]
    
    def search_terms(self, query: str, language: str = None) -> List[Dict]:
        """Search for terms containing query string."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if language:
                cursor.execute("""
                    SELECT source_term, target_term, source_lang, target_lang, domain
                    FROM terms 
                    WHERE (source_lang = ? OR target_lang = ?) 
                    AND (LOWER(source_term) LIKE ? OR LOWER(target_term) LIKE ?)
                    ORDER BY source_term
                    LIMIT 50
                """, (language, language, f"%{query.lower()}%", f"%{query.lower()}%"))
            else:
                cursor.execute("""
                    SELECT source_term, target_term, source_lang, target_lang, domain
                    FROM terms 
                    WHERE LOWER(source_term) LIKE ? OR LOWER(target_term) LIKE ?
                    ORDER BY source_term
                    LIMIT 50
                """, (f"%{query.lower()}%", f"%{query.lower()}%"))
            
            return [
                {
                    "source": row[0],
                    "target": row[1],
                    "source_lang": row[2],
                    "target_lang": row[3],
                    "domain": row[4] or ""
                }
                for row in cursor.fetchall()
            ]
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Term counts
            cursor.execute("SELECT COUNT(*) FROM terms")
            total_terms = cursor.fetchone()[0]
            
            cursor.execute("SELECT source_lang, COUNT(*) FROM terms GROUP BY source_lang")
            lang_counts = dict(cursor.fetchall())
            
            # Rule counts
            cursor.execute("SELECT COUNT(*) FROM rules")
            total_rules = cursor.fetchone()[0]
            
            cursor.execute("SELECT language, COUNT(*) FROM rules GROUP BY language")
            rule_counts = dict(cursor.fetchall())
            
            # Source files
            cursor.execute("SELECT DISTINCT source_file FROM terms WHERE source_file IS NOT NULL")
            source_files = [row[0] for row in cursor.fetchall()]
            
            return {
                "total_terms": total_terms,
                "total_rules": total_rules,
                "terms_by_language": lang_counts,
                "rules_by_language": rule_counts,
                "source_files": source_files,
                "database_path": self.db_path
            } 